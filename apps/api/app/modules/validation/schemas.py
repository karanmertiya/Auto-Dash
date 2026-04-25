from typing import Literal

from pydantic import BaseModel, Field


class ValidationFinding(BaseModel):
    severity: Literal["info", "warning", "error"]
    rule_name: str
    message: str
    details: dict = Field(default_factory=dict)


class ValidationReport(BaseModel):
    dataset_id: str
    dataset_version_id: str | None
    findings: list[ValidationFinding]

