from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.schemas import DashboardPlanRead
from app.db.models import DashboardPlan
from app.db.session import get_session
from app.modules.recommendation.schemas import KpiPlanRequest
from app.modules.recommendation.service import RecommendationService

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/semantic-models/{semantic_model_id}/dashboard-plan", response_model=DashboardPlanRead)
def generate_dashboard_plan(
    semantic_model_id: str,
    payload: KpiPlanRequest,
    session: Session = Depends(get_session),
) -> DashboardPlan:
    return RecommendationService(session).generate_dashboard_plan(
        semantic_model_id=semantic_model_id,
        goal=payload.goal,
        actor=payload.actor,
    )

