from sqlalchemy.orm import Session

from app.db.models import AuditLog, UserAction


class AuditService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def log(
        self,
        *,
        action: str,
        entity_type: str,
        entity_id: str,
        actor: str = "system",
        project_id: str | None = None,
        payload: dict | None = None,
    ) -> None:
        self.session.add(
            AuditLog(
                project_id=project_id,
                actor=actor,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                payload_json=payload or {},
            )
        )
        self.session.add(
            UserAction(
                actor=actor,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details_json=payload or {},
            )
        )

