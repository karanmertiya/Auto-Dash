from typing import Literal

from pydantic import BaseModel, Field


class CleaningOperation(BaseModel):
    operation: str
    column: str | None = None
    target_column: str | None = None
    rationale: str
    expression: str
    risk_level: Literal["low", "medium", "high"] = "low"


class CleaningPlanModel(BaseModel):
    summary: str
    operations: list[CleaningOperation]
    script: str
    warnings: list[str] = Field(default_factory=list)
    requires_approval: bool = True


class CleaningExecutionRequest(BaseModel):
    script: str | None = None
    actor: str = "local-user"


class CleaningExecutionResult(BaseModel):
    status: Literal["succeeded", "failed"]
    output_path: str | None = None
    preview_rows: list[dict] = Field(default_factory=list)
    error_message: str | None = None
    attempts: int
    run_log: dict = Field(default_factory=dict)

