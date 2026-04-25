# DashForge Core

DashForge Core is an expert-in-the-loop data-to-dashboard accelerator. It keeps generated logic visible, editable, versioned, and exportable across ingestion, profiling, cleaning, semantic modeling, KPI planning, dashboard generation, validation, and governance.

## Repository Tree

```text
dashforge-core/
  apps/
    api/
      app/
        ai/                     # provider abstraction, structured-output validation, prompts
        api/routes/             # REST API surface
        core/                   # settings, logging, errors
        db/                     # SQLAlchemy models and sessions
        modules/
          artifacts/            # export services
          cleaning/             # plan generation, AST guard, subprocess runner
          collaboration/        # comments, approvals, audit logging
          dashboard/            # editable Next.js dashboard artifact generation
          ingestion/            # CSV, Excel, JSON, Parquet, SQL snapshot ingestion
          orchestration/        # local background-job adapter
          profiling/            # Polars profile and schema inference
          recommendation/       # KPI and chart plan generation
          semantic/             # governed semantic model generation
          validation/           # freshness, schema, quality checks
      migrations/               # Alembic metadata schema
      tests/                    # core service tests
    web/
      app/                      # Next.js workbench pages
      components/               # inspector, code editor, shell, KPI plan views
      lib/                      # API client
  artifacts/examples/           # example generated outputs
  sample-data/                  # messy business input data
```

## Local Setup

```bash
cd dashforge-core
cp .env.example .env
cd apps/api
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

In another terminal:

```bash
cd dashforge-core
corepack enable
pnpm install
pnpm --filter @dashforge/web dev
```

Open `http://localhost:3000`. The API is served at `http://localhost:8000`, with OpenAPI docs at `http://localhost:8000/docs`.

## Test Commands

```bash
cd dashforge-core/apps/api
pytest
```

Optional frontend checks after installing Node dependencies:

```bash
cd dashforge-core
pnpm --filter @dashforge/web lint
pnpm --filter @dashforge/web build
```

## Workflow

1. Upload `sample-data/messy_orders.csv`.
2. Inspect profile JSON and column warnings.
3. Generate a cleaning plan, edit the Polars script, then execute it.
4. Generate a semantic model and export JSON/YAML.
5. Generate a KPI/chart plan from a business goal.
6. Generate editable Next.js dashboard code and export the artifact zip.
7. Run validation and inspect audit history.

## API Highlights

```text
POST /api/datasets/upload
POST /api/datasets/sql
GET  /api/datasets
GET  /api/datasets/{dataset_id}/profile
POST /api/datasets/{dataset_id}/profile
POST /api/cleaning/datasets/{dataset_id}/plan
POST /api/cleaning/plans/{cleaning_plan_id}/execute
POST /api/semantic-models/datasets/{dataset_id}
POST /api/recommendations/semantic-models/{semantic_model_id}/dashboard-plan
POST /api/dashboards/plans/{dashboard_plan_id}/generate
POST /api/validation/datasets/{dataset_id}
GET  /api/artifacts/semantic-models/{semantic_model_id}.yaml
GET  /api/artifacts/semantic-models/{semantic_model_id}.json
GET  /api/artifacts/cleaning-plans/{cleaning_plan_id}.py
GET  /api/artifacts/dashboards/{dashboard_artifact_id}.zip
GET  /api/governance/history
```

## Architecture Decisions

- Raw uploads are immutable. DashForge writes staged Parquet and cleaned Parquet separately.
- Profiling is deterministic with Polars and persists structured JSON per dataset version.
- Cleaning plans are drafts. The generated `transform(df)` script is shown, editable, AST-validated, and run in a timed subprocess.
- AI is optional and isolated behind an OpenAI-compatible provider boundary. Local deterministic fallbacks keep the app runnable without API keys.
- Semantic models store entities, fields, metric expressions, warnings, JSON, and YAML.
- KPI and chart recommendations only reference existing governed metrics.
- Dashboard generation emits editable Next.js code with visible metric expressions.
- Audit logs and user actions are persisted for reproducibility and governance.

## Production Notes

The current orchestration adapter uses FastAPI background tasks for local-first development. A production deployment should swap that adapter for Celery, Dramatiq, Arq, or Temporal; add object storage for artifacts; add a real identity provider; and harden script execution with containers, seccomp/AppArmor, and resource quotas.

