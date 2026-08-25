from sqlalchemy.orm import Session
from app.models import ActivityLogModel
from app.schemas import ActivityLogData
from typing import List, Any


def log_activity(
    project_id: int,
    user_id: int,
    action: str,
    details: dict[str, Any] | None,
    db: Session
) -> ActivityLogModel:
    log_entry = ActivityLogModel(
        project_id=project_id,
        user_id=user_id,
        action=action,
        details=details
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry


def query_project_activity_logs(
    project_id: int,
    db: Session,
    limit: int = 20,
    offset: int = 0
) -> List[ActivityLogData]:
    logs = (
        db.query(ActivityLogModel)
        .filter(ActivityLogModel.project_id == project_id)
        .order_by(ActivityLogModel.created_at.desc(), ActivityLogModel.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    result = []
    for log in logs:
        result.append(
            ActivityLogData(
                id=log.id,
                project_id=log.project_id,
                user_id=log.user_id,
                user_name=log.user.full_name if log.user else None,
                action=log.action,
                details=log.details,
                created_at=log.created_at
            )
        )
    return result
