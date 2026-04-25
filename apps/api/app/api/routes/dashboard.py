from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.schemas import DashboardArtifactRead
from app.db.models import DashboardArtifact
from app.db.session import get_session
from app.modules.dashboard.schemas import DashboardGenerationRequest
from app.modules.dashboard.service import DashboardGenerationService

router = APIRouter(prefix="/dashboards", tags=["dashboards"])


@router.post("/plans/{dashboard_plan_id}/generate", response_model=DashboardArtifactRead)
def generate_dashboard_artifact(
    dashboard_plan_id: str,
    payload: DashboardGenerationRequest,
    session: Session = Depends(get_session),
) -> DashboardArtifact:
    return DashboardGenerationService(session).generate_nextjs_artifact(
        dashboard_plan_id=dashboard_plan_id,
        actor=payload.actor,
    )

