from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import DatasetRead, DatasetVersionRead, SqlIngestRequest
from app.core.errors import not_found
from app.db.models import ColumnProfile, Dataset, DatasetVersion
from app.db.session import get_session
from app.modules.ingestion.service import IngestionService, read_dataframe
from app.modules.profiling.service import DatasetProfiler

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("/upload", response_model=DatasetRead)
async def upload_dataset(
    file: UploadFile = File(...),
    project_id: str | None = Form(default=None),
    actor: str = Form(default="local-user"),
    session: Session = Depends(get_session),
) -> Dataset:
    return await IngestionService(session).ingest_upload(file=file, project_id=project_id, actor=actor)


@router.post("/sql", response_model=DatasetRead)
def ingest_sql(payload: SqlIngestRequest, session: Session = Depends(get_session)) -> Dataset:
    return IngestionService(session).ingest_sql_snapshot(**payload.model_dump())


@router.get("", response_model=list[DatasetRead])
def list_datasets(session: Session = Depends(get_session)) -> list[Dataset]:
    return list(session.scalars(select(Dataset).order_by(Dataset.created_at.desc())))


@router.get("/{dataset_id}", response_model=DatasetRead)
def get_dataset(dataset_id: str, session: Session = Depends(get_session)) -> Dataset:
    dataset = session.get(Dataset, dataset_id)
    if dataset is None:
        raise not_found("Dataset", dataset_id)
    return dataset


@router.get("/{dataset_id}/versions", response_model=list[DatasetVersionRead])
def dataset_versions(dataset_id: str, session: Session = Depends(get_session)) -> list[DatasetVersion]:
    return list(
        session.scalars(
            select(DatasetVersion)
            .where(DatasetVersion.dataset_id == dataset_id)
            .order_by(DatasetVersion.version_number.desc())
        )
    )


@router.get("/{dataset_id}/profile")
def get_profile(dataset_id: str, session: Session = Depends(get_session)) -> dict:
    dataset = session.get(Dataset, dataset_id)
    if dataset is None or dataset.current_version_id is None:
        raise not_found("Dataset", dataset_id)
    version = session.get(DatasetVersion, dataset.current_version_id)
    if version is None:
        raise not_found("DatasetVersion", dataset.current_version_id)
    return version.profile_json


@router.post("/{dataset_id}/profile")
def refresh_profile(dataset_id: str, session: Session = Depends(get_session)) -> dict:
    dataset = session.get(Dataset, dataset_id)
    if dataset is None or dataset.current_version_id is None:
        raise not_found("Dataset", dataset_id)
    version = session.get(DatasetVersion, dataset.current_version_id)
    if version is None:
        raise not_found("DatasetVersion", dataset.current_version_id)
    df = read_dataframe(version.cleaned_path or version.staged_path)
    profiler = DatasetProfiler()
    profile = profiler.profile(df, dataset_id=dataset.id, version_id=version.id)
    schema = profiler.schema_from_profile(profile)
    version.profile_json = profile.model_dump(mode="json")
    version.schema_json = schema.model_dump(mode="json")
    session.query(ColumnProfile).filter(ColumnProfile.dataset_version_id == version.id).delete()
    for column in profile.columns:
        session.add(
            ColumnProfile(
                dataset_version_id=version.id,
                column_name=column.name,
                inferred_type=column.inferred_type,
                semantic_role=column.semantic_role,
                stats_json=column.stats.model_dump(mode="json"),
                warnings_json=column.warnings,
            )
        )
    session.commit()
    return version.profile_json

