"""
Pydantic schemas for API request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any, Literal
from datetime import datetime


class ConfidenceBreakdown(BaseModel):
    overall: float = Field(..., ge=0.0, le=1.0)
    directive_score: float = Field(..., ge=0.0, le=1.0)
    entity_score: float = Field(..., ge=0.0, le=1.0)
    deadline_score: float = Field(..., ge=0.0, le=1.0)
    notes: Optional[str] = None


# ============ Document Schemas ============

class DocumentUploadResponse(BaseModel):
    """Response schema for document upload"""
    document_id: str
    filename: str
    status: str = "uploaded"
    message: str
    upload_time: datetime
    
    class Config:
        from_attributes = True


class DocumentStatusResponse(BaseModel):
    """Response schema for document status"""
    document_id: str
    filename: str
    status: str
    upload_time: datetime
    extracted_text: Optional[str] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True


class DocumentInfoResponse(BaseModel):
    """Complete document information"""
    id: str
    filename: str
    file_path: str
    upload_time: datetime
    status: str
    extracted_text: Optional[str] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class MultipleDocumentsUploadResponse(BaseModel):
    """Response schema for multiple document uploads"""
    total_uploaded: int
    documents: List[DocumentUploadResponse]
    failed_uploads: List[dict] = []
    message: str


# ============ Action Schemas ============

class ActionResponse(BaseModel):
    """Enhanced response schema for detected action"""
    action_type: str = Field(..., description="Type: compliance, appeal, review, escalation")
    task: str = Field(..., description="Clean task description")
    department: str = Field(..., description="Responsible department")
    deadline: Optional[str] = Field(None, description="ISO format deadline")
    priority: str = Field("Medium", description="High/Medium/Low")
    confidence: float = Field(..., description="Confidence score 0.0-1.0")
    confidence_components: Optional[ConfidenceBreakdown] = None
    evidence: Any = Field(..., description="Structured evidence: {text,page,sentence_index,char_start,char_end}")
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ActionDetailsResponse(BaseModel):
    """Detailed action information for queries"""
    id: int
    document_id: str
    type: str
    task: str
    deadline: Optional[str] = None
    status: str = "PENDING"
    department: Optional[str] = None
    priority: Optional[str] = "Medium"
    confidence: Optional[str] = None
    confidence_score: Optional[float] = None
    confidence_components: Optional[ConfidenceBreakdown] = None
    evidence: Optional[Any] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ProcessingResultResponse(BaseModel):
    """Response schema for document processing results"""
    success: bool
    document_id: str
    message: str
    sentence_count: Optional[int] = None
    action_count: Optional[int] = None
    actions: List[ActionResponse] = []


class ReviewResponse(BaseModel):
    """Action review details"""
    id: int
    action_id: int
    reviewer_name: str
    decision: str
    comments: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class ActionEditRequest(BaseModel):
    task: Optional[str] = None
    department: Optional[str] = None
    deadline: Optional[str] = None
    priority: Optional[str] = None
    reviewer_name: str = "human_reviewer"
    comments: Optional[str] = None


class AuditLogResponse(BaseModel):
    """Audit log entry details"""
    id: int
    entity_type: str
    entity_id: str
    action: str
    performed_by: str
    timestamp: datetime
    details: Optional[dict] = None

    class Config:
        from_attributes = True


class NotificationResponse(BaseModel):
    id: int
    action_id: int
    due_at: datetime
    sent_at: Optional[datetime] = None
    channel: str
    status: str
    payload: Optional[dict] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class ActionHistoryResponse(BaseModel):
    """Action with review and audit trail"""
    action: ActionDetailsResponse
    reviews: List[ReviewResponse] = []
    audits: List[AuditLogResponse] = []


class DocumentWithActionsResponse(BaseModel):
    """Document with generated actions and audits"""
    document: DocumentInfoResponse
    actions: List[ActionDetailsResponse] = []
    audits: List[AuditLogResponse] = []
    
    class Config:
        from_attributes = True


# ============ Dashboard Schemas ============

class DashboardStats(BaseModel):
    """Dashboard statistics"""
    total_documents: int
    processed_documents: int
    processing_documents: int
    failed_documents: int
    total_actions: int
    pending_actions: int
    approved_actions: int
    rejected_actions: int


class AlertsResponse(BaseModel):
    due_actions: List[ActionDetailsResponse] = []
    notifications: List[NotificationResponse] = []
    window_hours: int = 72
