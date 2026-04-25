from __future__ import annotations

import json
import zipfile
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import not_found
from app.db.models import CleaningPlan, DashboardArtifact, SemanticModel


class ArtifactExportService:
    def __init__(self, session: Session, settings: Settings | None = None) -> None:
        self.session = session
        self.settings = settings or get_settings()

    def export_semantic_model(self, semantic_model_id: str, fmt: str) -> Path:
        model = self.session.get(SemanticModel, semantic_model_id)
        if model is None:
            raise not_found("SemanticModel", semantic_model_id)
        target = self.settings.storage_dir / "artifacts" / f"semantic_model_{model.id}.{fmt}"
        target.parent.mkdir(parents=True, exist_ok=True)
        if fmt == "json":
            target.write_text(json.dumps(model.model_json, indent=2), encoding="utf-8")
        elif fmt in {"yaml", "yml"}:
            target.write_text(model.model_yaml, encoding="utf-8")
        else:
            raise ValueError("fmt must be json or yaml")
        return target

    def export_cleaning_script(self, cleaning_plan_id: str) -> Path:
        plan = self.session.get(CleaningPlan, cleaning_plan_id)
        if plan is None:
            raise not_found("CleaningPlan", cleaning_plan_id)
        target = self.settings.storage_dir / "artifacts" / f"cleaning_plan_{plan.id}.py"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            "import pandas as pd\nimport polars as pl\n\n" + plan.script,
            encoding="utf-8",
        )
        return target

    def export_dashboard_zip(self, dashboard_artifact_id: str) -> Path:
        artifact = self.session.get(DashboardArtifact, dashboard_artifact_id)
        if artifact is None:
            raise not_found("DashboardArtifact", dashboard_artifact_id)
        source = Path(artifact.path)
        target = self.settings.storage_dir / "artifacts" / f"dashboard_artifact_{artifact.id}.zip"
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
            for file_path in source.rglob("*"):
                if file_path.is_file():
                    archive.write(file_path, file_path.relative_to(source))
        return target
