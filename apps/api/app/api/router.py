from fastapi import APIRouter

from app.api.routes import (
    artifacts,
    cleaning,
    collaboration,
    dashboard,
    datasets,
    projects,
    recommendations,
    semantic,
    validation,
)

api_router = APIRouter(prefix="/api")
api_router.include_router(projects.router)
api_router.include_router(datasets.router)
api_router.include_router(cleaning.router)
api_router.include_router(semantic.router)
api_router.include_router(recommendations.router)
api_router.include_router(dashboard.router)
api_router.include_router(validation.router)
api_router.include_router(artifacts.router)
api_router.include_router(collaboration.router)

