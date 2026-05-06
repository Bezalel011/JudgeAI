"""
Notification Service - Finds due actions and creates reminder notifications.
"""

from __future__ import annotations

from datetime import datetime, timedelta, time
from typing import Dict, List, Optional

from app.db import SessionLocal, Action, Notification, log_event, AUDIT_ENTITY_ACTION
from app.logger import setup_logger
from app.services.deadline_engine import deadline_engine

logger = setup_logger(__name__)


class NotificationService:
    @staticmethod
    def list_due_actions(window_hours: int = 72) -> List[Dict[str, object]]:
        db = SessionLocal()
        try:
            now = datetime.utcnow()
            cutoff = now + timedelta(hours=window_hours)
            due_items: List[Dict[str, object]] = []

            actions = db.query(Action).filter(Action.status == "PENDING").all()
            for action in actions:
                if not action.deadline:
                    continue

                try:
                    deadline_date = datetime.fromisoformat(action.deadline).date()
                except ValueError:
                    try:
                        deadline_date = datetime.strptime(action.deadline, "%Y-%m-%d").date()
                    except ValueError:
                        continue

                due_at = datetime.combine(deadline_date, time.max)
                if due_at <= cutoff:
                    due_items.append({
                        "id": action.id,
                        "document_id": action.document_id,
                        "type": action.type,
                        "task": action.task,
                        "deadline": action.deadline,
                        "status": action.status,
                        "department": action.department,
                        "priority": action.priority,
                        "confidence": action.confidence_score,
                        "evidence": action.evidence,
                        "urgency": deadline_engine.compute_urgency(action.deadline),
                        "due_at": due_at.isoformat(),
                    })

            return due_items
        finally:
            db.close()

    @staticmethod
    def create_reminder_events(window_hours: int = 72, channel: str = "in_app") -> List[Notification]:
        db = SessionLocal()
        created: List[Notification] = []
        try:
            due_actions = NotificationService.list_due_actions(window_hours)
            for item in due_actions:
                action_id = int(item["id"])
                due_at = datetime.fromisoformat(str(item["due_at"]))

                existing = db.query(Notification).filter(
                    Notification.action_id == action_id,
                    Notification.channel == channel,
                    Notification.status.in_(["PENDING", "SENT"]),
                ).first()
                if existing:
                    continue

                notification = Notification(
                    action_id=action_id,
                    due_at=due_at,
                    channel=channel,
                    status="PENDING",
                    payload=item,
                )
                db.add(notification)
                db.flush()
                log_event(
                    entity_type="action",
                    entity_id=str(action_id),
                    action="notification_created",
                    performed_by="system",
                    details={"channel": channel, "due_at": due_at.isoformat()},
                    action_id=action_id,
                    db=db,
                )
                created.append(notification)

            db.commit()
            for notification in created:
                db.refresh(notification)
            return created
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def dispatch_notifications(channel: str = "in_app") -> List[Notification]:
        db = SessionLocal()
        dispatched: List[Notification] = []
        try:
            notifications = db.query(Notification).filter(
                Notification.channel == channel,
                Notification.status == "PENDING",
            ).order_by(Notification.due_at.asc()).all()

            for notification in notifications:
                notification.status = "SENT"
                notification.sent_at = datetime.utcnow()
                dispatched.append(notification)
                log_event(
                    entity_type="action",
                    entity_id=str(notification.action_id),
                    action="notification_sent",
                    performed_by="system",
                    details={"channel": channel, "notification_id": notification.id},
                    action_id=notification.action_id,
                    db=db,
                )

            db.commit()
            for notification in dispatched:
                db.refresh(notification)
            return dispatched
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def acknowledge_notification(notification_id: int) -> Notification:
        db = SessionLocal()
        try:
            notification = db.query(Notification).filter(Notification.id == notification_id).first()
            if not notification:
                raise ValueError(f"Notification {notification_id} not found")

            notification.status = "ACKNOWLEDGED"
            notification.sent_at = notification.sent_at or datetime.utcnow()
            db.commit()
            db.refresh(notification)
            return notification
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def snooze_notification(notification_id: int, snooze_minutes: int = 60) -> Notification:
        db = SessionLocal()
        try:
            notification = db.query(Notification).filter(Notification.id == notification_id).first()
            if not notification:
                raise ValueError(f"Notification {notification_id} not found")

            notification.status = "SNOOZED"
            notification.due_at = datetime.utcnow() + timedelta(minutes=snooze_minutes)
            db.commit()
            db.refresh(notification)
            return notification
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()


notification_service = NotificationService()