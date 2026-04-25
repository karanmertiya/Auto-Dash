from __future__ import annotations

import re

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import bad_request, not_found
from app.db.models import CleaningExecution, CleaningPlan, Dataset, DatasetVersion
from app.modules.cleaning.executor import SafeScriptExecutor
from app.modules.cleaning.schemas import CleaningOperation, CleaningPlanModel
from app.modules.collaboration.audit import AuditService


class CleaningService:
    def __init__(self, session: Session, settings: Settings | None = None) -> None:
        self.session = session
        self.settings = settings or get_settings()
        self.audit = AuditService(session)
        self.executor = SafeScriptExecutor(self.settings)

    def generate_plan(self, *, dataset_id: str, actor: str = "local-user") -> CleaningPlan:
        dataset = self.session.get(Dataset, dataset_id)
        if dataset is None or dataset.current_version_id is None:
            raise not_found("Dataset", dataset_id)
        version = self.session.get(DatasetVersion, dataset.current_version_id)
        if version is None:
            raise not_found("DatasetVersion", dataset.current_version_id)
        profile = version.profile_json
        plan = self._deterministic_plan(profile)
        record = CleaningPlan(
            dataset_id=dataset.id,
            dataset_version_id=version.id,
            status="draft",
            summary=plan.summary,
            script=plan.script,
            plan_json=plan.model_dump(mode="json"),
            generated_by="deterministic-fallback",
        )
        self.session.add(record)
        self.audit.log(
            action="cleaning_plan.generated",
            entity_type="cleaning_plan",
            entity_id=record.id,
            actor=actor,
            project_id=dataset.project_id,
            payload={"dataset_id": dataset.id, "requires_approval": True},
        )
        self.session.commit()
        self.session.refresh(record)
        return record

    def execute_plan(
        self,
        *,
        cleaning_plan_id: str,
        actor: str = "local-user",
        script_override: str | None = None,
    ) -> CleaningExecution:
        plan = self.session.get(CleaningPlan, cleaning_plan_id)
        if plan is None:
            raise not_found("CleaningPlan", cleaning_plan_id)
        version = self.session.get(DatasetVersion, plan.dataset_version_id)
        if version is None:
            raise not_found("DatasetVersion", plan.dataset_version_id)
        script = script_override or plan.script
        attempts = []
        result = None
        current_script = script
        for attempt_number in range(1, 4):
            result = self.executor.execute(
                script=current_script,
                input_path=version.staged_path,
            )
            result.attempts = attempt_number
            attempts.append(result.model_dump(mode="json"))
            if result.status == "succeeded":
                break
            current_script = self._local_self_correction(current_script, result.error_message or "")
            if current_script == script:
                break
        if result is None:
            raise bad_request("Cleaning execution did not run.", "execution_not_started")

        execution = CleaningExecution(
            cleaning_plan_id=plan.id,
            dataset_version_id=version.id,
            status=result.status,
            output_path=result.output_path,
            error_message=result.error_message,
            attempts=result.attempts,
            run_log_json={"attempts": attempts},
        )
        self.session.add(execution)
        if result.status == "succeeded":
            version.cleaned_path = result.output_path
            plan.status = "executed"
        else:
            plan.status = "failed"
        self.audit.log(
            action=f"cleaning_execution.{result.status}",
            entity_type="cleaning_execution",
            entity_id=execution.id,
            actor=actor,
            payload={"cleaning_plan_id": plan.id, "attempts": result.attempts},
        )
        self.session.commit()
        self.session.refresh(execution)
        return execution

    def _deterministic_plan(self, profile: dict) -> CleaningPlanModel:
        operations: list[CleaningOperation] = []
        rename_map: dict[str, str] = {}
        date_columns: list[str] = []
        numeric_string_columns: list[str] = []
        suspicious_flags: list[str] = []
        for column in profile.get("columns", []):
            name = column["name"]
            clean_name = self._clean_column_name(name)
            if clean_name != name:
                rename_map[name] = clean_name
                operations.append(
                    CleaningOperation(
                        operation="rename_column",
                        column=name,
                        target_column=clean_name,
                        rationale="Normalize column name to snake_case for durable code and semantic references.",
                        expression=f"rename {name!r} -> {clean_name!r}",
                    )
                )
            active_name = clean_name
            stats = column.get("stats", {})
            role = column.get("semantic_role")
            if role == "date" or stats.get("mixed_type_signals", {}).get("parseable_datetime_ratio", 0) > 0.8:
                date_columns.append(active_name)
                operations.append(
                    CleaningOperation(
                        operation="date_normalization",
                        column=active_name,
                        rationale="Parse date-like values into a typed Polars Date column.",
                        expression=f"pl.col({active_name!r}).str.strptime(pl.Date, strict=False)",
                    )
                )
            numeric_ratio = stats.get("mixed_type_signals", {}).get("parseable_numeric_ratio", 0)
            if role == "metric" or numeric_ratio > 0.85:
                numeric_string_columns.append(active_name)
                operations.append(
                    CleaningOperation(
                        operation="numeric_cast",
                        column=active_name,
                        rationale="Cast metric-like values to Float64 without failing on dirty rows.",
                        expression=f"pl.col({active_name!r}).cast(pl.Float64, strict=False)",
                    )
                )
            if column.get("warnings"):
                suspicious_flags.append(active_name)
        script = self._script(rename_map, date_columns, numeric_string_columns, suspicious_flags)
        summary = (
            "Draft cleaning plan normalizes column names, parses date fields, safely casts metric-like "
            "columns, deduplicates exact duplicate rows, and adds review flags instead of hiding dirty rows."
        )
        warnings = [
            "Review all casts before execution. Raw data is preserved and the script is editable.",
            "Suspicious records are flagged, not dropped.",
        ]
        return CleaningPlanModel(
            summary=summary,
            operations=operations,
            script=script,
            warnings=warnings,
        )

    def _script(
        self,
        rename_map: dict[str, str],
        date_columns: list[str],
        numeric_columns: list[str],
        suspicious_columns: list[str],
    ) -> str:
        lines = [
            "def transform(df):",
            "    result = df.clone()",
        ]
        if rename_map:
            lines.append(f"    result = result.rename({rename_map!r})")
        lines.append("    result = result.unique(maintain_order=True)")
        if date_columns:
            lines.append("    result = result.with_columns([")
            for column in date_columns:
                lines.append(
                    "        pl.coalesce(["
                    f"pl.col({column!r}).cast(pl.String, strict=False).str.strptime(pl.Date, format='%Y-%m-%d', strict=False), "
                    f"pl.col({column!r}).cast(pl.String, strict=False).str.strptime(pl.Date, format='%m/%d/%Y', strict=False), "
                    f"pl.col({column!r}).cast(pl.String, strict=False).str.strptime(pl.Date, format='%Y/%m/%d', strict=False)"
                    f"]).alias({column!r}),"
                )
            lines.append("    ])")
        if numeric_columns:
            lines.append("    result = result.with_columns([")
            for column in numeric_columns:
                lines.append(f"        pl.col({column!r}).cast(pl.Float64, strict=False).alias({column!r}),")
            lines.append("    ])")
        if suspicious_columns:
            expressions = [f"pl.col({column!r}).is_null()" for column in suspicious_columns]
            lines.append(
                f"    result = result.with_columns(({ ' | '.join(expressions) }).alias('_dashforge_review_flag'))"
            )
        else:
            lines.append("    result = result.with_columns(pl.lit(False).alias('_dashforge_review_flag'))")
        lines.append("    return result")
        return "\n".join(lines) + "\n"

    def _clean_column_name(self, name: str) -> str:
        value = re.sub(r"[^0-9A-Za-z]+", "_", name.strip()).strip("_").lower()
        if value and value[0].isdigit():
            value = f"col_{value}"
        return value or "unnamed_column"

    def _local_self_correction(self, script: str, error_message: str) -> str:
        if "not found" in error_message.lower() and "rename" in script:
            return script.replace("    result = result.unique(maintain_order=True)\n", "")
        return script
