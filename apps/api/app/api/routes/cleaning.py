from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.schemas import CleaningExecutionRead, CleaningPlanRead
from app.db.session import get_session
from app.modules.cleaning.schemas import CleaningExecutionRequest
from app.modules.cleaning.service import CleaningService

router = APIRouter(prefix="/cleaning", tags=["cleaning"])


@router.post("/datasets/{dataset_id}/plan", response_model=CleaningPlanRead)
def generate_cleaning_plan(
    dataset_id: str,
    actor: str = "local-user",
    session: Session = Depends(get_session),
):
    return CleaningService(session).generate_plan(dataset_id=dataset_id, actor=actor)


@router.post("/plans/{cleaning_plan_id}/execute", response_model=CleaningExecutionRead)
def execute_cleaning_plan(
    cleaning_plan_id: str,
    payload: CleaningExecutionRequest,
    session: Session = Depends(get_session),
):
    return CleaningService(session).execute_plan(
        cleaning_plan_id=cleaning_plan_id,
        actor=payload.actor,
        script_override=payload.script,
    )

