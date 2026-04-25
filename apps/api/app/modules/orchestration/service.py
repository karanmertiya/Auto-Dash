from __future__ import annotations

from fastapi import BackgroundTasks


class OrchestrationService:
    """Thin local-first job adapter.

    Production deployments can replace this with Celery, Dramatiq, Arq, or Temporal
    while keeping service interfaces stable.
    """

    def enqueue(self, background_tasks: BackgroundTasks, func, *args, **kwargs) -> None:
        background_tasks.add_task(func, *args, **kwargs)

