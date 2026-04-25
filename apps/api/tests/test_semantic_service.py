from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.models import Base, Dataset, DatasetVersion, Project
from app.modules.semantic.service import SemanticModelService


def test_semantic_model_uses_profiled_metric_columns() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        project = Project(name="Test")
        dataset = Dataset(
            project=project,
            name="Orders",
            source_type="csv",
            status="profiled",
            metadata_json={},
        )
        version = DatasetVersion(
            dataset=dataset,
            version_number=1,
            raw_path="raw.csv",
            staged_path="staged.parquet",
            schema_json={},
            profile_json={
                "columns": [
                    {"name": "order_id", "semantic_role": "id", "inferred_type": "String"},
                    {"name": "order_date", "semantic_role": "date", "inferred_type": "String"},
                    {"name": "revenue", "semantic_role": "metric", "inferred_type": "Float64"},
                    {"name": "region", "semantic_role": "dimension", "inferred_type": "String"},
                ]
            },
            row_count=10,
            content_hash="abc",
        )
        session.add_all([project, dataset, version])
        session.flush()
        dataset.current_version_id = version.id
        session.commit()

        model = SemanticModelService(session).generate_model(
            dataset_id=dataset.id,
            goal="Revenue dashboard",
        )

        metric_names = {metric["name"] for metric in model.model_json["metrics"]}
        assert "sum_revenue" in metric_names
        assert "avg_revenue" in metric_names

