from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Approval, Comment
from app.modules.collaboration.audit import AuditService


class CollaborationService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.audit = AuditService(session)

    def add_comment(self, *, entity_type: str, entity_id: str, body: str, actor: str) -> Comment:
        comment = Comment(actor=actor, entity_type=entity_type, entity_id=entity_id, body=body)
        self.session.add(comment)
        self.audit.log(
            action="comment.created",
            entity_type=entity_type,
            entity_id=entity_id,
            actor=actor,
            payload={"comment": body},
        )
        self.session.commit()
        self.session.refresh(comment)
        return comment

    def approve(self, *, entity_type: str, entity_id: str, status: str, actor: str, note: str | None) -> Approval:
        approval = Approval(
            actor=actor,
            entity_type=entity_type,
            entity_id=entity_id,
            status=status,
            note=note,
        )
        self.session.add(approval)
        self.audit.log(
            action=f"approval.{status}",
            entity_type=entity_type,
            entity_id=entity_id,
            actor=actor,
            payload={"note": note},
        )
        self.session.commit()
        self.session.refresh(approval)
        return approval

    def comments_for(self, *, entity_type: str, entity_id: str) -> list[Comment]:
        return list(
            self.session.scalars(
                select(Comment)
                .where(Comment.entity_type == entity_type, Comment.entity_id == entity_id)
                .order_by(Comment.created_at.desc())
            )
        )
