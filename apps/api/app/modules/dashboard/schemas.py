from pydantic import BaseModel, Field


class DashboardArtifactDocument(BaseModel):
    dashboard_plan_id: str
    framework: str = "nextjs"
    files: dict[str, str]
    instructions: list[str] = Field(default_factory=list)


class DashboardGenerationRequest(BaseModel):
    actor: str = "local-user"

