from typing import Any, Literal

from pydantic import BaseModel, Field

SemanticRole = Literal["id", "date", "metric", "dimension", "text", "unknown"]


class ColumnStats(BaseModel):
    row_count: int
    missing_count: int
    missing_ratio: float
    distinct_count: int
    cardinality_ratio: float
    sample_values: list[Any] = Field(default_factory=list)
    numeric: dict[str, float | int | None] = Field(default_factory=dict)
    temporal: dict[str, str | None] = Field(default_factory=dict)
    text: dict[str, float | int | None] = Field(default_factory=dict)
    mixed_type_signals: dict[str, float] = Field(default_factory=dict)


class ColumnProfileModel(BaseModel):
    name: str
    inferred_type: str
    semantic_role: SemanticRole
    stats: ColumnStats
    warnings: list[str] = Field(default_factory=list)


class RelationshipHint(BaseModel):
    left_column: str
    right_dataset: str | None = None
    right_column: str | None = None
    confidence: float = Field(ge=0, le=1)
    rationale: str


class DatasetProfileModel(BaseModel):
    dataset_id: str | None = None
    version_id: str | None = None
    row_count: int
    column_count: int
    duplicate_row_count: int
    columns: list[ColumnProfileModel]
    relationship_hints: list[RelationshipHint] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    profile_version: str = "1.0"


class DatasetSchemaModel(BaseModel):
    columns: dict[str, str]
    role_map: dict[str, SemanticRole]
    candidate_ids: list[str] = Field(default_factory=list)
    candidate_dates: list[str] = Field(default_factory=list)
    candidate_metrics: list[str] = Field(default_factory=list)
    candidate_dimensions: list[str] = Field(default_factory=list)

