from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.modules.artifacts.service import ArtifactExportService

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


@router.get("/semantic-models/{semantic_model_id}.{fmt}")
def export_semantic_model(
    semantic_model_id: str,
    fmt: str,
    session: Session = Depends(get_session),
) -> FileResponse:
    path = ArtifactExportService(session).export_semantic_model(semantic_model_id, fmt)
    return _file(path)


@router.get("/cleaning-plans/{cleaning_plan_id}.py")
def export_cleaning_script(
    cleaning_plan_id: str,
    session: Session = Depends(get_session),
) -> FileResponse:
    path = ArtifactExportService(session).export_cleaning_script(cleaning_plan_id)
    return _file(path)


@router.get("/dashboards/{dashboard_artifact_id}.zip")
def export_dashboard_artifact(
    dashboard_artifact_id: str,
    session: Session = Depends(get_session),
) -> FileResponse:
    path = ArtifactExportService(session).export_dashboard_zip(dashboard_artifact_id)
    return _file(path)


def _file(path: Path) -> FileResponse:
    return FileResponse(path, filename=path.name)

