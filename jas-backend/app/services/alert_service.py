"""Background alert generation for action deadlines."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from dateutil.parser import parse as parse_datetime
from sqlalchemy.orm import Session

from app.config import settings
from app.db import (
    Action,
    Alert,
    SessionLocal,
    ACTION_STATUS_PENDING,
    ACTION_STATUS_OVERDUE,
    ALERT_TYPE_UPCOMING,
    ALERT_TYPE_OVERDUE,
)


def _parse_deadline(deadline: str | None) -> datetime | None:
    if not deadline:
        return None

    try:
        parsed = parse_datetime(str(deadline))
    except (ValueError, TypeError, OverflowError):
        return None

    return parsed


def _build_message(action: Action, alert_type: str, deadline_dt: datetime) -> str:
    deadline_text = deadline_dt.strftime("%Y-%m-%d")
    task_text = (action.task or "Unnamed action").strip()
    if alert_type == ALERT_TYPE_OVERDUE:
        return f"Action #{action.id} is overdue. Deadline was {deadline_text}. Task: {task_text}"
    return f"Action #{action.id} is due soon. Deadline is {deadline_text}. Task: {task_text}"


def generate_alerts(db: Session | None = None) -> dict[str, Any]:
    """Scan pending actions, generate alerts, and mark overdue items."""
    own_session = db is None
    session = db or SessionLocal()
    created = 0
    skipped = 0
    overdue_updated = 0

    today = datetime.utcnow().date()
    lookahead = today + timedelta(days=settings.ALERT_LOOKAHEAD_DAYS)

    try:
        pending_actions = (
            session.query(Action)
            .filter(Action.status == ACTION_STATUS_PENDING)
            .order_by(Action.created_at.asc())
            .all()
        )

        for action in pending_actions:
            deadline_dt = _parse_deadline(action.deadline)
            if deadline_dt is None:
                continue

            deadline_date = deadline_dt.date()
            if deadline_date < today:
                alert_type = ALERT_TYPE_OVERDUE
                action.status = ACTION_STATUS_OVERDUE
                action.updated_at = datetime.utcnow()
                overdue_updated += 1
            elif deadline_date <= lookahead:
                alert_type = ALERT_TYPE_UPCOMING
            else:
                continue

            existing_alert = (
                session.query(Alert)
                .filter(Alert.action_id == action.id, Alert.type == alert_type)
                .first()
            )
            if existing_alert:
                skipped += 1
                continue

            alert = Alert(
                action_id=action.id,
                type=alert_type,
                message=_build_message(action, alert_type, deadline_dt),
                created_at=datetime.utcnow(),
                is_read=False,
            )
            session.add(alert)
            created += 1

        if own_session:
            session.commit()
        else:
            session.flush()

        return {
            "success": True,
            "created": created,
            "skipped": skipped,
            "overdue_updated": overdue_updated,
        }
    except Exception:
        if own_session:
            session.rollback()
        raise
    finally:
        if own_session:
            session.close()
