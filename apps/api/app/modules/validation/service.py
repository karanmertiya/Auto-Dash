from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.errors import not_found
from app.db.models import Dataset, DatasetVersion, ValidationResult
from app.modules.ingestion.service import read_dataframe
from app.modules.validation.schemas import ValidationFinding, ValidationReport


class ValidationService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def validate_dataset(self, *, dataset_id: str) -> ValidationReport:
        dataset = self.session.get(Dataset, dataset_id)
        if dataset is None or dataset.current_version_id is None:
            raise not_found("Dataset", dataset_id)
        version = self.session.get(DatasetVersion, dataset.current_version_id)
        if version is None:
            raise not_found("DatasetVersion", dataset.current_version_id)
        findings = self._findings(dataset, version)
        self.session.execute(delete(ValidationResult).where(ValidationResult.dataset_id == dataset.id))
        for finding in findings:
            self.session.add(
                ValidationResult(
                    dataset_id=dataset.id,
                    dataset_version_id=version.id,
                    severity=finding.severity,
                    rule_name=finding.rule_name,
                    message=finding.message,
                    result_json=finding.details,
                )
            )
        self.session.commit()
        return ValidationReport(dataset_id=dataset.id, dataset_version_id=version.id, findings=findings)

    def _findings(self, dataset: Dataset, version: DatasetVersion) -> list[ValidationFinding]:
        profile = version.profile_json
        findings: list[ValidationFinding] = []
        age_hours = (datetime.now(UTC).replace(tzinfo=None) - version.created_at).total_seconds() / 3600
        if age_hours > 24:
            findings.append(
                ValidationFinding(
                    severity="warning",
                    rule_name="freshness_check",
                    message=f"Dataset version is {age_hours:.1f} hours old.",
                    details={"age_hours": age_hours},
                )
            )
        for column in profile.get("columns", []):
            stats = column.get("stats", {})
            missing_ratio = stats.get("missing_ratio", 0)
            if missing_ratio > 0.2:
                findings.append(
                    ValidationFinding(
                        severity="warning",
                        rule_name="missing_value_threshold",
                        message=f"{column['name']} has {missing_ratio:.1%} missing values.",
                        details={"column": column["name"], "missing_ratio": missing_ratio},
                    )
                )
            if column.get("semantic_role") == "id" and stats.get("cardinality_ratio", 0) < 0.95:
                findings.append(
                    ValidationFinding(
                        severity="error",
                        rule_name="identifier_uniqueness",
                        message=f"{column['name']} is ID-like but not unique.",
                        details={"column": column["name"], "cardinality_ratio": stats.get("cardinality_ratio")},
                    )
                )
        df = read_dataframe(version.cleaned_path or version.staged_path)
        if df.is_empty():
            findings.append(
                ValidationFinding(
                    severity="error",
                    rule_name="non_empty_dataset",
                    message="Dataset has no rows available for dashboard generation.",
                )
            )
        if not findings:
            findings.append(
                ValidationFinding(
                    severity="info",
                    rule_name="validation_passed",
                    message="No blocking validation findings detected.",
                )
            )
        return findings

