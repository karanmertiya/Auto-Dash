from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import SemanticModelRead
from app.db.models import SemanticModel
from app.db.session import get_session
from app.modules.semantic.schemas import SemanticGoalRequest
from app.modules.semantic.service import SemanticModelService

router = APIRouter(prefix="/semantic-models", tags=["semantic-models"])


@router.post("/datasets/{dataset_id}", response_model=SemanticModelRead)
def generate_semantic_model(
    dataset_id: str,
    payload: SemanticGoalRequest,
    session: Session = Depends(get_session),
) -> SemanticModel:
    return SemanticModelService(session).generate_model(
        dataset_id=dataset_id,
        goal=payload.goal,
        actor=payload.actor,
    )


@router.get("/datasets/{dataset_id}", response_model=list[SemanticModelRead])
def list_semantic_models(dataset_id: str, session: Session = Depends(get_session)) -> list[SemanticModel]:
    return list(
        session.scalars(
            select(SemanticModel)
            .where(SemanticModel.dataset_id == dataset_id)
            .order_by(SemanticModel.version_number.desc())
        )
    )

