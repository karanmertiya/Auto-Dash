from typing import Literal

from pydantic import BaseModel, Field


class KpiCandidate(BaseModel):
    name: str
    metric_expression: str
    business_question: str
    aggregation: str
    confidence: float = Field(ge=0, le=1)
    warnings: list[str] = Field(default_factory=list)


class ChartRecommendation(BaseModel):
    title: str
    chart_type: Literal["kpi_card", "line", "bar", "area", "scatter", "table"]
    metric: str
    dimension: str | None = None
    time_dimension: str | None = None
    filters: list[str] = Field(default_factory=list)
    drilldowns: list[str] = Field(default_factory=list)
    rationale: str


class DashboardLayoutItem(BaseModel):
    id: str
    title: str
    component: str
    x: int
    y: int
    w: int
    h: int
    chart: ChartRecommendation


class DashboardPlanDocument(BaseModel):
    goal: str
    kpis: list[KpiCandidate]
    charts: list[ChartRecommendation]
    layout: list[DashboardLayoutItem]
    warnings: list[str] = Field(default_factory=list)


class KpiPlanRequest(BaseModel):
    goal: str
    actor: str = "local-user"

