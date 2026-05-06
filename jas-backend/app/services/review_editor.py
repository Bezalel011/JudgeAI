"""
Review Editor - Apply human edits to AI-generated actions and preserve revision history.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from app.db import (
    SessionLocal,
    Action,
    ActionRevision,
    create_review,
    REVIEW_DECISION_EDITED,
)
from app.logger import setup_logger

logger = setup_logger(__name__)


class ReviewEditor:
    ALLOWED_FIELDS = {"task", "department", "deadline", "priority"}

    @staticmethod
    def validate_action_patch(patch: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(patch, dict):
            raise ValueError("patch must be an object")

        filtered = {key: value for key, value in patch.items() if key in ReviewEditor.ALLOWED_FIELDS and value is not None}
        if not filtered:
            raise ValueError("patch must include at least one editable field")

        return filtered

    @staticmethod
    def apply_action_edit(action_id: int, patch: Dict[str, Any], reviewer: str, comments: str | None = None) -> Dict[str, Any]:
        patch = ReviewEditor.validate_action_patch(patch)

        db = SessionLocal()
        try:
            action = db.query(Action).filter(Action.id == action_id).first()
            if not action:
                raise ValueError(f"Action {action_id} not found")

            before = {
                "task": action.task,
                "department": action.department,
                "deadline": action.deadline,
                "priority": action.priority,
                "status": action.status,
            }

            for field, value in patch.items():
                setattr(action, field, value)

            action.updated_at = datetime.utcnow()
            db.flush()

            revision = ActionRevision(
                action_id=action_id,
                reviewer_name=reviewer,
                before_json=before,
                after_json={
                    "task": action.task,
                    "department": action.department,
                    "deadline": action.deadline,
                    "priority": action.priority,
                    "status": action.status,
                },
                comments=comments,
                timestamp=datetime.utcnow(),
            )
            db.add(revision)
            db.flush()

            review = create_review(
                action_id=action_id,
                decision=REVIEW_DECISION_EDITED,
                reviewer=reviewer,
                comments=comments,
                db=db,
            )

            db.commit()
            db.refresh(action)
            db.refresh(revision)
            db.refresh(review)

            return {
                "action": action,
                "revision": revision,
                "review": review,
            }
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()


review_editor = ReviewEditor()