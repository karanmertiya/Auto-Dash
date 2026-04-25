.PHONY: api web test migrate

api:
	cd apps/api && uvicorn app.main:app --reload --port 8000

web:
	pnpm --filter @dashforge/web dev

test:
	cd apps/api && pytest

migrate:
	cd apps/api && alembic upgrade head

