from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    event,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session
from datetime import datetime
import uuid
from app.config import settings

DATABASE_URL = settings.DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


DOCUMENT_STATUS_UPLOADED = "uploaded"
DOCUMENT_STATUS_PROCESSING = "processing"
DOCUMENT_STATUS_PROCESSED = "processed"
DOCUMENT_STATUS_FAILED = "failed"

ACTION_STATUS_PENDING = "PENDING"
ACTION_STATUS_APPROVED = "APPROVED"
ACTION_STATUS_REJECTED = "REJECTED"

REVIEW_DECISION_APPROVED = "approved"
REVIEW_DECISION_REJECTED = "rejected"
REVIEW_DECISION_EDITED = "edited"

AUDIT_ENTITY_DOCUMENT = "document"
AUDIT_ENTITY_ACTION = "action"
AUDIT_ENTITY_REVIEW = "review"


if "sqlite" in DATABASE_URL:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


class Document(Base):
    """Document model for storing uploaded PDFs and their metadata"""
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, index=True)
    file_path = Column(String)
    upload_time = Column(DateTime, default=datetime.utcnow, index=True)
    status = Column(String, default="uploaded", index=True)  # uploaded, processing, processed, failed
    extracted_text = Column(Text, nullable=True)
    error_message = Column(String, nullable=True)

    actions = relationship("Action", back_populates="document", cascade="all, delete-orphan")
    audits = relationship("AuditLog", back_populates="document", cascade="all, delete-orphan")


class Action(Base):
    """Action model for storing extracted actions from documents"""
    __tablename__ = "actions"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False)
    type = Column(String)
    task = Column(Text)
    department = Column(String, nullable=True)
    deadline = Column(String)
    priority = Column(String, nullable=True)
    status = Column(String, default="PENDING", index=True)  # PENDING / APPROVED / REJECTED
    confidence = Column(String, nullable=True)
    # Evidence stored as structured fields for explainability
    evidence_text = Column(Text, nullable=True)
    evidence_page = Column(String, nullable=True)
    evidence_index = Column(Integer, nullable=True)
    evidence_start = Column(Integer, nullable=True)
    evidence_end = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)

    document = relationship("Document", back_populates="actions")
    reviews = relationship("Review", back_populates="action", cascade="all, delete-orphan")
    audits = relationship("AuditLog", back_populates="action_ref")

    @property
    def evidence(self):
        """Return structured evidence dict for API responses and UI."""
        return {
            "text": self.evidence_text,
            "page": int(self.evidence_page) if self.evidence_page is not None and str(self.evidence_page).isdigit() else self.evidence_page,
            "sentence_index": self.evidence_index,
            "char_start": self.evidence_start,
            "char_end": self.evidence_end,
        }


class Review(Base):
    """Human review history for actions."""
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    action_id = Column(Integer, ForeignKey("actions.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_name = Column(String, nullable=False)
    decision = Column(String, nullable=False, index=True)  # approved/rejected/edited
    comments = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    action = relationship("Action", back_populates="reviews")
    audits = relationship("AuditLog", back_populates="review_ref")


class AuditLog(Base):
    """System-wide audit log for document/action/review lifecycle events."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String, nullable=False, index=True)  # document/action/review
    entity_id = Column(String, nullable=False, index=True)
    action = Column(String, nullable=False, index=True)  # created/updated/deleted/approved/rejected
    performed_by = Column(String, default="system", nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    details = Column(JSON, nullable=True)

    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), nullable=True, index=True)
    action_id = Column(Integer, ForeignKey("actions.id", ondelete="SET NULL"), nullable=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id", ondelete="SET NULL"), nullable=True, index=True)

    document = relationship("Document", back_populates="audits")
    action_ref = relationship("Action", back_populates="audits")
    review_ref = relationship("Review", back_populates="audits")


def log_event(
    entity_type: str,
    entity_id: str,
    action: str,
    performed_by: str = "system",
    details: dict | None = None,
    document_id: str | None = None,
    action_id: int | None = None,
    review_id: int | None = None,
    db: Session | None = None,
) -> AuditLog:
    """Create an audit log entry; commits only when no external session is provided."""
    own_session = db is None
    session = db or SessionLocal()
    try:
        entry = AuditLog(
            entity_type=entity_type,
            entity_id=str(entity_id),
            action=action,
            performed_by=performed_by,
            details=details,
            document_id=document_id,
            action_id=action_id,
            review_id=review_id,
        )
        session.add(entry)
        if own_session:
            session.commit()
            session.refresh(entry)
        return entry
    except Exception:
        if own_session:
            session.rollback()
        raise
    finally:
        if own_session:
            session.close()


def create_review(
    action_id: int,
    decision: str,
    reviewer: str,
    comments: str | None = None,
    db: Session | None = None,
) -> Review:
    """Create a review for an action, update action status, and add audit logs."""
    if decision not in {REVIEW_DECISION_APPROVED, REVIEW_DECISION_REJECTED, REVIEW_DECISION_EDITED}:
        raise ValueError("decision must be approved, rejected, or edited")

    own_session = db is None
    session = db or SessionLocal()
    try:
        action_obj = session.query(Action).filter(Action.id == action_id).first()
        if not action_obj:
            raise ValueError(f"Action {action_id} not found")

        if decision == REVIEW_DECISION_APPROVED:
            action_obj.status = ACTION_STATUS_APPROVED
            action_event = "approved"
        elif decision == REVIEW_DECISION_REJECTED:
            action_obj.status = ACTION_STATUS_REJECTED
            action_event = "rejected"
        else:
            action_event = "updated"

        action_obj.updated_at = datetime.utcnow()

        review = Review(
            action_id=action_id,
            reviewer_name=reviewer,
            decision=decision,
            comments=comments,
            timestamp=datetime.utcnow(),
        )
        session.add(review)
        session.flush()

        log_event(
            entity_type=AUDIT_ENTITY_REVIEW,
            entity_id=str(review.id),
            action="created",
            performed_by=reviewer,
            details={"decision": decision, "comments": comments},
            document_id=action_obj.document_id,
            action_id=action_obj.id,
            review_id=review.id,
            db=session,
        )

        log_event(
            entity_type=AUDIT_ENTITY_ACTION,
            entity_id=str(action_obj.id),
            action=action_event,
            performed_by=reviewer,
            details={"new_status": action_obj.status, "decision": decision},
            document_id=action_obj.document_id,
            action_id=action_obj.id,
            review_id=review.id,
            db=session,
        )

        if own_session:
            session.commit()
            session.refresh(review)
        return review
    except Exception:
        if own_session:
            session.rollback()
        raise
    finally:
        if own_session:
            session.close()


# Create all tables
Base.metadata.create_all(bind=engine)