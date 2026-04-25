from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.errors import not_found
from app.db.models import DashboardPlan, SemanticModel
from app.modules.collaboration.audit import AuditService
from app.modules.recommendation.schemas import (
    ChartRecommendation,
    DashboardLayoutItem,
    DashboardPlanDocument,
    KpiCandidate,
)


class RecommendationService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.audit = AuditService(session)

    def generate_dashboard_plan(
        self,
        *,
        semantic_model_id: str,
        goal: str,
        actor: str = "local-user",
    ) -> DashboardPlan:
        semantic = self.session.get(SemanticModel, semantic_model_id)
        if semantic is None:
            raise not_found("SemanticModel", semantic_model_id)
        document = self._plan_from_semantic(semantic.model_json, goal)
        record = DashboardPlan(
            semantic_model_id=semantic.id,
            user_goal=goal,
            plan_json=document.model_dump(mode="json"),
            warnings_json=document.warnings,
        )
        self.session.add(record)
        self.audit.log(
            action="dashboard_plan.generated",
            entity_type="dashboard_plan",
            entity_id=record.id,
            actor=actor,
            payload={"semantic_model_id": semantic.id, "goal": goal},
        )
        self.session.commit()
        self.session.refresh(record)
        return record

    def _plan_from_semantic(self, semantic_json: dict, goal: str) -> DashboardPlanDocument:
        metrics = semantic_json.get("metrics", [])
        entity = semantic_json.get("entities", [{}])[0]
        fields = entity.get("fields", [])
        time_fields = [field["source_column"] for field in fields if field.get("role") == "time"]
        dimensions = [
            field["source_column"]
            for field in fields
            if field.get("role") in {"dimension", "entity_key"} and field.get("source_column")
        ]
        warnings: list[str] = []
        if not metrics:
            warnings.append("No governed metrics are available. Define metrics before generating charts.")
        if not goal.strip():
            warnings.append("No goal supplied; recommendations are generic and should be reviewed.")
        selected = metrics[:7]
        kpis: list[KpiCandidate] = []
        charts: list[ChartRecommendation] = []
        layout: list[DashboardLayoutItem] = []
        for metric in selected:
            confidence = 0.74 if metric.get("warnings") else 0.86
            kpis.append(
                KpiCandidate(
                    name=metric["name"],
                    metric_expression=metric["expression"],
                    business_question=f"Track {metric['label']} for: {goal}",
                    aggregation=metric.get("aggregation", "sum"),
                    confidence=confidence,
                    warnings=metric.get("warnings", []),
                )
            )
        for index, metric in enumerate(selected[:4]):
            time_dimension = time_fields[0] if time_fields else None
            dimension = dimensions[index % len(dimensions)] if dimensions else None
            chart_type = "line" if time_dimension else ("bar" if dimension else "kpi_card")
            charts.append(
                ChartRecommendation(
                    title=metric["label"],
                    chart_type=chart_type,
                    metric=metric["name"],
                    dimension=dimension,
                    time_dimension=time_dimension,
                    filters=dimensions[:3],
                    drilldowns=dimensions[:3],
                    rationale="Uses governed metric expression and available semantic dimensions.",
                )
            )
        for index, chart in enumerate(charts):
            layout.append(
                DashboardLayoutItem(
                    id=f"viz_{index + 1}",
                    title=chart.title,
                    component="MetricCard" if chart.chart_type == "kpi_card" else "ChartPanel",
                    x=(index % 2) * 6,
                    y=(index // 2) * 4,
                    w=6,
                    h=4,
                    chart=chart,
                )
            )
        return DashboardPlanDocument(goal=goal, kpis=kpis, charts=charts, layout=layout, warnings=warnings)
