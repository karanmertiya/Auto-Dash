"""Initial DashForge Core metadata schema."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202604250001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("owner_email", sa.String(255)),
        *timestamps(),
    )
    op.create_table(
        "datasets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("source_type", sa.String(64), nullable=False),
        sa.Column("current_version_id", sa.String(36)),
        sa.Column("status", sa.String(64), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_datasets_project_id", "datasets", ["project_id"])
    op.create_index("ix_datasets_current_version_id", "datasets", ["current_version_id"])
    op.create_table(
        "dataset_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("dataset_id", sa.String(36), sa.ForeignKey("datasets.id"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("raw_path", sa.Text(), nullable=False),
        sa.Column("staged_path", sa.Text(), nullable=False),
        sa.Column("cleaned_path", sa.Text()),
        sa.Column("schema_json", sa.JSON(), nullable=False),
        sa.Column("profile_json", sa.JSON(), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(128), nullable=False),
        *timestamps(),
        sa.UniqueConstraint("dataset_id", "version_number", name="uq_dataset_version"),
    )
    op.create_index("ix_dataset_versions_dataset_id", "dataset_versions", ["dataset_id"])
    op.create_table(
        "column_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "dataset_version_id", sa.String(36), sa.ForeignKey("dataset_versions.id"), nullable=False
        ),
        sa.Column("column_name", sa.String(255), nullable=False),
        sa.Column("inferred_type", sa.String(64), nullable=False),
        sa.Column("semantic_role", sa.String(64), nullable=False),
        sa.Column("stats_json", sa.JSON(), nullable=False),
        sa.Column("warnings_json", sa.JSON(), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_column_profiles_dataset_version_id", "column_profiles", ["dataset_version_id"])
    for table_name, extra_columns in {
        "cleaning_plans": [
            sa.Column("dataset_id", sa.String(36), sa.ForeignKey("datasets.id"), nullable=False),
            sa.Column(
                "dataset_version_id",
                sa.String(36),
                sa.ForeignKey("dataset_versions.id"),
                nullable=False,
            ),
            sa.Column("status", sa.String(64), nullable=False),
            sa.Column("summary", sa.Text(), nullable=False),
            sa.Column("script", sa.Text(), nullable=False),
            sa.Column("plan_json", sa.JSON(), nullable=False),
            sa.Column("generated_by", sa.String(64), nullable=False),
        ],
        "cleaning_executions": [
            sa.Column(
                "cleaning_plan_id", sa.String(36), sa.ForeignKey("cleaning_plans.id"), nullable=False
            ),
            sa.Column(
                "dataset_version_id",
                sa.String(36),
                sa.ForeignKey("dataset_versions.id"),
                nullable=False,
            ),
            sa.Column("status", sa.String(64), nullable=False),
            sa.Column("output_path", sa.Text()),
            sa.Column("error_message", sa.Text()),
            sa.Column("attempts", sa.Integer(), nullable=False),
            sa.Column("run_log_json", sa.JSON(), nullable=False),
        ],
        "semantic_models": [
            sa.Column("dataset_id", sa.String(36), sa.ForeignKey("datasets.id"), nullable=False),
            sa.Column(
                "dataset_version_id",
                sa.String(36),
                sa.ForeignKey("dataset_versions.id"),
                nullable=False,
            ),
            sa.Column("version_number", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(64), nullable=False),
            sa.Column("model_json", sa.JSON(), nullable=False),
            sa.Column("model_yaml", sa.Text(), nullable=False),
        ],
        "metric_definitions": [
            sa.Column(
                "semantic_model_id", sa.String(36), sa.ForeignKey("semantic_models.id"), nullable=False
            ),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("expression", sa.Text(), nullable=False),
            sa.Column("grain", sa.String(128), nullable=False),
            sa.Column("owner", sa.String(255)),
            sa.Column("version_number", sa.Integer(), nullable=False),
            sa.Column("metadata_json", sa.JSON(), nullable=False),
        ],
        "dashboard_plans": [
            sa.Column(
                "semantic_model_id", sa.String(36), sa.ForeignKey("semantic_models.id"), nullable=False
            ),
            sa.Column("user_goal", sa.Text(), nullable=False),
            sa.Column("plan_json", sa.JSON(), nullable=False),
            sa.Column("warnings_json", sa.JSON(), nullable=False),
        ],
        "dashboard_artifacts": [
            sa.Column(
                "dashboard_plan_id", sa.String(36), sa.ForeignKey("dashboard_plans.id"), nullable=False
            ),
            sa.Column("artifact_type", sa.String(64), nullable=False),
            sa.Column("path", sa.Text(), nullable=False),
            sa.Column("metadata_json", sa.JSON(), nullable=False),
        ],
        "validation_results": [
            sa.Column("dataset_id", sa.String(36), sa.ForeignKey("datasets.id"), nullable=False),
            sa.Column("dataset_version_id", sa.String(36), sa.ForeignKey("dataset_versions.id")),
            sa.Column("severity", sa.String(32), nullable=False),
            sa.Column("rule_name", sa.String(255), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("result_json", sa.JSON(), nullable=False),
        ],
        "audit_logs": [
            sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id")),
            sa.Column("actor", sa.String(255), nullable=False),
            sa.Column("action", sa.String(255), nullable=False),
            sa.Column("entity_type", sa.String(128), nullable=False),
            sa.Column("entity_id", sa.String(36), nullable=False),
            sa.Column("payload_json", sa.JSON(), nullable=False),
        ],
        "user_actions": [
            sa.Column("actor", sa.String(255), nullable=False),
            sa.Column("action", sa.String(255), nullable=False),
            sa.Column("entity_type", sa.String(128), nullable=False),
            sa.Column("entity_id", sa.String(36), nullable=False),
            sa.Column("details_json", sa.JSON(), nullable=False),
        ],
        "comments": [
            sa.Column("actor", sa.String(255), nullable=False),
            sa.Column("entity_type", sa.String(128), nullable=False),
            sa.Column("entity_id", sa.String(36), nullable=False),
            sa.Column("body", sa.Text(), nullable=False),
        ],
        "approvals": [
            sa.Column("actor", sa.String(255), nullable=False),
            sa.Column("entity_type", sa.String(128), nullable=False),
            sa.Column("entity_id", sa.String(36), nullable=False),
            sa.Column("status", sa.String(64), nullable=False),
            sa.Column("note", sa.Text()),
        ],
    }.items():
        op.create_table(table_name, sa.Column("id", sa.String(36), primary_key=True), *extra_columns, *timestamps())


def downgrade() -> None:
    for table_name in (
        "approvals",
        "comments",
        "user_actions",
        "audit_logs",
        "validation_results",
        "dashboard_artifacts",
        "dashboard_plans",
        "metric_definitions",
        "semantic_models",
        "cleaning_executions",
        "cleaning_plans",
        "column_profiles",
        "dataset_versions",
        "datasets",
        "projects",
    ):
        op.drop_table(table_name)
