from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import ApprovalCreate, CommentCreate
from app.db.models import AuditLog, UserAction
from app.db.session import get_session
from app.modules.collaboration.service import CollaborationService

router = APIRouter(prefix="/governance", tags=["governance"])


@router.post("/comments")
def add_comment(payload: CommentCreate, session: Session = Depends(get_session)) -> dict:
    comment = CollaborationService(session).add_comment(**payload.model_dump())
    return {"id": comment.id, "created_at": comment.created_at}


@router.post("/approvals")
def add_approval(payload: ApprovalCreate, session: Session = Depends(get_session)) -> dict:
    approval = CollaborationService(session).approve(**payload.model_dump())
    return {"id": approval.id, "status": approval.status, "created_at": approval.created_at}


@router.get("/history")
def history(session: Session = Depends(get_session)) -> dict:
    audit_logs = list(session.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(100)))
    user_actions = list(
        session.scalars(select(UserAction).order_by(UserAction.created_at.desc()).limit(100))
    )
    return {
        "audit_logs": [
            {
                "id": item.id,
                "actor": item.actor,
                "action": item.action,
                "entity_type": item.entity_type,
                "entity_id": item.entity_id,
                "payload": item.payload_json,
                "created_at": item.created_at,
            }
            for item in audit_logs
        ],
        "user_actions": [
            {
                "id": item.id,
                "actor": item.actor,
                "action": item.action,
                "entity_type": item.entity_type,
                "entity_id": item.entity_id,
                "details": item.details_json,
                "created_at": item.created_at,
            }
            for item in user_actions
        ],
    }

