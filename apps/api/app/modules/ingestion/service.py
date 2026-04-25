from __future__ import annotations

import hashlib
import re
from pathlib import Path
from uuid import uuid4

import pandas as pd
import polars as pl
from fastapi import UploadFile
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import bad_request
from app.db.models import ColumnProfile, Dataset, DatasetVersion, Project
from app.modules.collaboration.audit import AuditService
from app.modules.profiling.service import DatasetProfiler

SUPPORTED_FILE_SUFFIXES = {".csv", ".xlsx", ".xls", ".json", ".ndjson", ".parquet"}


class IngestionService:
    def __init__(self, session: Session, settings: Settings | None = None) -> None:
        self.session = session
        self.settings = settings or get_settings()
        self.profiler = DatasetProfiler()
        self.audit = AuditService(session)

    async def ingest_upload(
        self,
        *,
        file: UploadFile,
        project_id: str | None = None,
        actor: str = "local-user",
    ) -> Dataset:
        filename = file.filename or "upload.csv"
        suffix = Path(filename).suffix.lower()
        if suffix not in SUPPORTED_FILE_SUFFIXES:
            raise bad_request(
                f"Unsupported file type '{suffix}'. Supported: {sorted(SUPPORTED_FILE_SUFFIXES)}",
                "unsupported_file_type",
            )
        project = self._project(project_id)
        dataset_id = str(uuid4())
        raw_path = self.settings.storage_dir / "raw" / dataset_id / self._safe_filename(filename)
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        content = await file.read()
        raw_path.write_bytes(content)
        return self._create_dataset_from_file(
            project=project,
            dataset_id=dataset_id,
            raw_path=raw_path,
            name=Path(filename).stem,
            source_type=suffix.lstrip("."),
            actor=actor,
            metadata={"original_filename": filename},
        )

    def ingest_sql_snapshot(
        self,
        *,
        connection_url: str,
        query: str,
        name: str,
        project_id: str | None = None,
        actor: str = "local-user",
    ) -> Dataset:
        if not query.strip().lower().startswith("select"):
            raise bad_request("Only SELECT statements are allowed for SQL ingestion.", "unsafe_sql")
        project = self._project(project_id)
        dataset_id = str(uuid4())
        engine = create_engine(connection_url)
        frame = pd.read_sql_query(query, engine)
        raw_path = self.settings.storage_dir / "raw" / dataset_id / f"{self._safe_filename(name)}.parquet"
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        pl.from_pandas(frame).write_parquet(raw_path)
        return self._create_dataset_from_file(
            project=project,
            dataset_id=dataset_id,
            raw_path=raw_path,
            name=name,
            source_type="sql",
            actor=actor,
            metadata={"query": query},
        )

    def get_dataframe_for_version(self, version: DatasetVersion, prefer_cleaned: bool = False) -> pl.DataFrame:
        path = Path(version.cleaned_path) if prefer_cleaned and version.cleaned_path else Path(version.staged_path)
        return read_dataframe(path)

    def _create_dataset_from_file(
        self,
        *,
        project: Project,
        dataset_id: str,
        raw_path: Path,
        name: str,
        source_type: str,
        actor: str,
        metadata: dict,
    ) -> Dataset:
        df = read_dataframe(raw_path)
        staged_path = self.settings.storage_dir / "staged" / dataset_id / "v1.parquet"
        staged_path.parent.mkdir(parents=True, exist_ok=True)
        df.write_parquet(staged_path)
        profile = self.profiler.profile(df)
        schema = self.profiler.schema_from_profile(profile)

        dataset = Dataset(
            id=dataset_id,
            project_id=project.id,
            name=name,
            source_type=source_type,
            status="profiled",
            metadata_json=metadata,
        )
        version = DatasetVersion(
            dataset_id=dataset_id,
            version_number=1,
            raw_path=str(raw_path),
            staged_path=str(staged_path),
            schema_json=schema.model_dump(mode="json"),
            profile_json=profile.model_dump(mode="json"),
            row_count=df.height,
            content_hash=file_hash(raw_path),
        )
        self.session.add(dataset)
        self.session.add(version)
        self.session.flush()
        dataset.current_version_id = version.id
        self._persist_column_profiles(version.id, profile)
        self.audit.log(
            action="dataset.ingested",
            entity_type="dataset",
            entity_id=dataset.id,
            actor=actor,
            project_id=project.id,
            payload={"source_type": source_type, "row_count": df.height, "columns": df.columns},
        )
        self.session.commit()
        self.session.refresh(dataset)
        return dataset

    def _persist_column_profiles(self, version_id: str, profile) -> None:
        for column in profile.columns:
            self.session.add(
                ColumnProfile(
                    dataset_version_id=version_id,
                    column_name=column.name,
                    inferred_type=column.inferred_type,
                    semantic_role=column.semantic_role,
                    stats_json=column.stats.model_dump(mode="json"),
                    warnings_json=column.warnings,
                )
            )

    def _project(self, project_id: str | None) -> Project:
        if project_id:
            project = self.session.get(Project, project_id)
            if project is None:
                raise bad_request(f"Project '{project_id}' does not exist.", "invalid_project")
            return project
        project = self.session.scalar(select(Project).where(Project.name == "Default Project"))
        if project:
            return project
        project = Project(name="Default Project", description="Local DashForge Core workspace")
        self.session.add(project)
        self.session.flush()
        return project

    def next_version_number(self, dataset_id: str) -> int:
        current = self.session.scalar(
            select(func.max(DatasetVersion.version_number)).where(DatasetVersion.dataset_id == dataset_id)
        )
        return int(current or 0) + 1

    def _safe_filename(self, value: str) -> str:
        sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
        return sanitized or "dataset"


def read_dataframe(path: str | Path) -> pl.DataFrame:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pl.read_csv(path, infer_schema_length=2000, ignore_errors=True)
    if suffix in {".xlsx", ".xls"}:
        return pl.from_pandas(pd.read_excel(path))
    if suffix in {".json", ".ndjson"}:
        try:
            return pl.read_json(path)
        except Exception:
            return pl.from_pandas(pd.read_json(path, lines=suffix == ".ndjson"))
    if suffix == ".parquet":
        return pl.read_parquet(path)
    raise bad_request(f"Unsupported file type '{suffix}'.", "unsupported_file_type")


def file_hash(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

