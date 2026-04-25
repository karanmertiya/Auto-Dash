from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    owner_email: str | None = None


class ProjectRead(ProjectCreate):
    id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SqlIngestRequest(BaseModel):
    connection_url: str
    query: str
    name: str
    project_id: str | None = None
    actor: str = "local-user"


class DatasetRead(BaseModel):
    id: str
    project_id: str
    name: str
    source_type: str
    status: str
    current_version_id: str | None
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DatasetVersionRead(BaseModel):
    id: str
    dataset_id: str
    version_number: int
    raw_path: str
    staged_path: str
    cleaned_path: str | None
    schema_payload: dict[str, Any] = Field(
        validation_alias="schema_json",
        serialization_alias="schema_json",
    )
    profile_json: dict[str, Any]
    row_count: int
    content_hash: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CleaningPlanRead(BaseModel):
    id: str
    dataset_id: str
    dataset_version_id: str
    status: str
    summary: str
    script: str
    plan_json: dict[str, Any]
    generated_by: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CleaningExecutionRead(BaseModel):
    id: str
    cleaning_plan_id: str
    dataset_version_id: str
    status: str
    output_path: str | None
    error_message: str | None
    attempts: int
    run_log_json: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class SemanticModelRead(BaseModel):
    id: str
    dataset_id: str
    dataset_version_id: str
    version_number: int
    status: str
    model_json: dict[str, Any]
    model_yaml: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DashboardPlanRead(BaseModel):
    id: str
    semantic_model_id: str
    user_goal: str
    plan_json: dict[str, Any]
    warnings_json: list[Any] = Field(default_factory=list)
    created_at: datetime

    model_config = {"from_attributes": True}


class DashboardArtifactRead(BaseModel):
    id: str
    dashboard_plan_id: str
    artifact_type: str
    path: str
    metadata_json: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class ValidationResultRead(BaseModel):
    id: str
    dataset_id: str
    dataset_version_id: str | None
    severity: str
    rule_name: str
    message: str
    result_json: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class CommentCreate(BaseModel):
    entity_type: str
    entity_id: str
    body: str
    actor: str = "local-user"


class ApprovalCreate(BaseModel):
    entity_type: str
    entity_id: str
    status: str
    actor: str = "local-user"
    note: str | None = None
