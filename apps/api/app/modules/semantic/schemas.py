from typing import Literal

from pydantic import BaseModel, Field


class SemanticField(BaseModel):
    source_column: str
    name: str
    type: str
    role: Literal["entity_key", "dimension", "measure", "time", "text"]
    description: str


class SemanticMetric(BaseModel):
    name: str
    label: str
    expression: str
    aggregation: str
    source_column: str
    grain: str = "dataset"
    owner: str = "unassigned"
    warnings: list[str] = Field(default_factory=list)


class SemanticJoin(BaseModel):
    left_entity: str
    left_key: str
    right_entity: str
    right_key: str
    relationship: str
    confidence: float = Field(ge=0, le=1)


class SemanticEntity(BaseModel):
    name: str
    source_dataset_id: str
    primary_key: str | None = None
    fields: list[SemanticField]


class SemanticModelDocument(BaseModel):
    name: str
    version: int
    dataset_id: str
    entities: list[SemanticEntity]
    metrics: list[SemanticMetric]
    joins: list[SemanticJoin] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SemanticGoalRequest(BaseModel):
    goal: str = "Create a governed semantic model from the profiled dataset."
    actor: str = "local-user"

