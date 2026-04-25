from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import ValidationResultRead
from app.db.models import ValidationResult
from app.db.session import get_session
from app.modules.validation.schemas import ValidationReport
from app.modules.validation.service import ValidationService

router = APIRouter(prefix="/validation", tags=["validation"])


@router.post("/datasets/{dataset_id}", response_model=ValidationReport)
def validate_dataset(dataset_id: str, session: Session = Depends(get_session)) -> ValidationReport:
    return ValidationService(session).validate_dataset(dataset_id=dataset_id)


@router.get("/datasets/{dataset_id}", response_model=list[ValidationResultRead])
def validation_results(dataset_id: str, session: Session = Depends(get_session)) -> list[ValidationResult]:
    return list(
        session.scalars(
            select(ValidationResult)
            .where(ValidationResult.dataset_id == dataset_id)
            .order_by(ValidationResult.created_at.desc())
        )
    )

