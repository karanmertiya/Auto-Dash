from __future__ import annotations

import re

import yaml
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import not_found
from app.db.models import Dataset, DatasetVersion, MetricDefinition, SemanticModel
from app.modules.collaboration.audit import AuditService
from app.modules.semantic.schemas import (
    SemanticEntity,
    SemanticField,
    SemanticMetric,
    SemanticModelDocument,
)


class SemanticModelService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.audit = AuditService(session)

    def generate_model(
        self,
        *,
        dataset_id: str,
        goal: str,
        actor: str = "local-user",
    ) -> SemanticModel:
        dataset = self.session.get(Dataset, dataset_id)
        if dataset is None or dataset.current_version_id is None:
            raise not_found("Dataset", dataset_id)
        version = self.session.get(DatasetVersion, dataset.current_version_id)
        if version is None:
            raise not_found("DatasetVersion", dataset.current_version_id)
        next_version = self._next_version(dataset_id)
        document = self._document_from_profile(dataset, version, next_version, goal)
        model_yaml = yaml.safe_dump(document.model_dump(mode="json"), sort_keys=False)
        record = SemanticModel(
            dataset_id=dataset.id,
            dataset_version_id=version.id,
            version_number=next_version,
            status="draft",
            model_json=document.model_dump(mode="json"),
            model_yaml=model_yaml,
        )
        self.session.add(record)
        self.session.flush()
        for metric in document.metrics:
            self.session.add(
                MetricDefinition(
                    semantic_model_id=record.id,
                    name=metric.name,
                    expression=metric.expression,
                    grain=metric.grain,
                    owner=metric.owner,
                    version_number=1,
                    metadata_json=metric.model_dump(mode="json"),
                )
            )
        self.audit.log(
            action="semantic_model.generated",
            entity_type="semantic_model",
            entity_id=record.id,
            actor=actor,
            project_id=dataset.project_id,
            payload={"dataset_id": dataset.id, "goal": goal, "metric_count": len(document.metrics)},
        )
        self.session.commit()
        self.session.refresh(record)
        return record

    def _document_from_profile(
        self,
        dataset: Dataset,
        version: DatasetVersion,
        version_number: int,
        goal: str,
    ) -> SemanticModelDocument:
        profile = version.profile_json
        fields: list[SemanticField] = []
        metrics: list[SemanticMetric] = []
        primary_key: str | None = None
        warnings = [
            "Semantic model is generated as a draft. Owners must approve business naming and metric grain."
        ]
        for column in profile.get("columns", []):
            name = column["name"]
            role = column.get("semantic_role", "unknown")
            semantic_name = self._semantic_name(name)
            if role == "id" and primary_key is None:
                primary_key = name
            field_role = {
                "id": "entity_key",
                "date": "time",
                "metric": "measure",
                "dimension": "dimension",
                "text": "text",
                "unknown": "dimension",
            }.get(role, "dimension")
            fields.append(
                SemanticField(
                    source_column=name,
                    name=semantic_name,
                    type=column.get("inferred_type", "unknown"),
                    role=field_role,
                    description=f"Mapped from source column '{name}'.",
                )
            )
            if role == "metric":
                metric_name = f"sum_{self._metric_slug(name)}"
                metrics.append(
                    SemanticMetric(
                        name=metric_name,
                        label=f"Total {semantic_name}",
                        expression=f"sum({name})",
                        aggregation="sum",
                        source_column=name,
                        warnings=["Generated from numeric source field; confirm the additive grain."],
                    )
                )
                metrics.append(
                    SemanticMetric(
                        name=f"avg_{self._metric_slug(name)}",
                        label=f"Average {semantic_name}",
                        expression=f"avg({name})",
                        aggregation="avg",
                        source_column=name,
                        warnings=["Generated from numeric source field; confirm this average is meaningful."],
                    )
                )
        if not metrics:
            warnings.append("No numeric measure candidates were detected; metric definitions require user input.")
        entity = SemanticEntity(
            name=self._metric_slug(dataset.name) or "dataset",
            source_dataset_id=dataset.id,
            primary_key=primary_key,
            fields=fields,
        )
        return SemanticModelDocument(
            name=f"{dataset.name} semantic model",
            version=version_number,
            dataset_id=dataset.id,
            entities=[entity],
            metrics=metrics,
            joins=[],
            warnings=warnings,
        )

    def _next_version(self, dataset_id: str) -> int:
        current = self.session.scalar(
            select(func.max(SemanticModel.version_number)).where(SemanticModel.dataset_id == dataset_id)
        )
        return int(current or 0) + 1

    def _semantic_name(self, column: str) -> str:
        return re.sub(r"\s+", " ", column.replace("_", " ").replace("-", " ")).strip().title()

    def _metric_slug(self, value: str) -> str:
        slug = re.sub(r"[^0-9A-Za-z]+", "_", value.strip()).strip("_").lower()
        return slug or "metric"

