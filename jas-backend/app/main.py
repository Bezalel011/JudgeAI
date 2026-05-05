from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, File, HTTPException, status, Query
from typing import List
import logging

from app.config import settings
from app.logger import setup_logger
from app.services.ingestion import ingestion_service
from app.services.pipeline import pipeline_orchestrator
from app.db import (
    SessionLocal,
    Action,
    Document,
    Review,
    AuditLog,
    create_review,
    ACTION_STATUS_PENDING,
    ACTION_STATUS_APPROVED,
    ACTION_STATUS_REJECTED,
    REVIEW_DECISION_APPROVED,
    REVIEW_DECISION_REJECTED,
)
from app.schemas import (
    DocumentUploadResponse,
    DocumentStatusResponse,
    MultipleDocumentsUploadResponse,
    ProcessingResultResponse,
    ActionDetailsResponse,
    DashboardStats,
    ReviewResponse,
    ActionHistoryResponse,
    DocumentInfoResponse,
    DocumentWithActionsResponse,
    AuditLogResponse,
)

# Initialize logger
logger = setup_logger(__name__)

app = FastAPI(
    title="Judgment-to-Action API",
    description="Robust document processing and action detection system",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for development)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ Health & Info Routes ============

@app.get("/")
def home():
    """Home endpoint - API status"""
    return {
        "message": "Judgment-to-Action API v2.0 running",
        "status": "operational",
        "version": "2.0.0"
    }


@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "healthy"}


# ============ Document Upload Routes ============

@app.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a single PDF document.
    
    Returns document ID and metadata.
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith(".pdf"):
            logger.warning(f"Invalid file type uploaded: {file.filename}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are supported"
            )
        
        # Read file content
        content = await file.read()
        
        # Validate file size
        max_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(content) > max_size_bytes:
            logger.warning(f"File too large: {file.filename}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit"
            )
        
        # Save document
        logger.info(f"Processing upload for: {file.filename}")
        document_id, success, message = ingestion_service.save_document(
            content,
            file.filename
        )
        
        if not success:
            logger.error(f"Failed to save document: {message}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=message
            )
        
        # Fetch document details
        db = SessionLocal()
        try:
            document = db.query(Document).filter(
                Document.id == document_id
            ).first()
            
            return DocumentUploadResponse(
                document_id=document_id,
                filename=file.filename,
                status="uploaded",
                message=message,
                upload_time=document.upload_time
            )
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during file upload: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@app.post("/upload-batch", response_model=MultipleDocumentsUploadResponse)
async def upload_multiple_documents(files: List[UploadFile] = File(...)):
    """
    Upload multiple PDF documents.
    
    Max files per request: configurable (default 5)
    """
    try:
        # Validate number of files
        if len(files) > settings.MAX_FILES_PER_UPLOAD:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum {settings.MAX_FILES_PER_UPLOAD} files per upload"
            )
        
        uploaded_documents = []
        failed_uploads = []
        
        for file in files:
            try:
                # Validate file type
                if not file.filename.lower().endswith(".pdf"):
                    failed_uploads.append({
                        "filename": file.filename,
                        "error": "Only PDF files supported"
                    })
                    continue
                
                # Read and save
                content = await file.read()
                document_id, success, message = ingestion_service.save_document(
                    content,
                    file.filename
                )
                
                if success:
                    db = SessionLocal()
                    try:
                        document = db.query(Document).filter(
                            Document.id == document_id
                        ).first()
                        
                        uploaded_documents.append(DocumentUploadResponse(
                            document_id=document_id,
                            filename=file.filename,
                            status="uploaded",
                            message=message,
                            upload_time=document.upload_time
                        ))
                    finally:
                        db.close()
                else:
                    failed_uploads.append({
                        "filename": file.filename,
                        "error": message
                    })
                    
            except Exception as e:
                logger.error(f"Error uploading {file.filename}: {str(e)}")
                failed_uploads.append({
                    "filename": file.filename,
                    "error": str(e)
                })
        
        return MultipleDocumentsUploadResponse(
            total_uploaded=len(uploaded_documents),
            documents=uploaded_documents,
            failed_uploads=failed_uploads,
            message=f"Uploaded {len(uploaded_documents)} file(s)"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch upload error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch upload failed: {str(e)}"
        )


# ============ Document Processing Routes ============

@app.post("/process/{document_id}", response_model=ProcessingResultResponse)
async def process_document(document_id: str):
    """
    Trigger processing pipeline for a document.
    
    Pipeline: OCR → Preprocessing → Action Detection
    """
    try:
        logger.info(f"Processing request for document: {document_id}")
        
        # Verify document exists
        db = SessionLocal()
        try:
            document = db.query(Document).filter(
                Document.id == document_id
            ).first()
            
            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document {document_id} not found"
                )
        finally:
            db.close()
        
        # Run processing pipeline
        result = pipeline_orchestrator.process_document(document_id)
        
        if result["success"]:
            return ProcessingResultResponse(**result)
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {str(e)}"
        )


@app.get("/document/{document_id}", response_model=DocumentStatusResponse)
async def get_document_status(document_id: str):
    """
    Get document status and metadata.
    """
    db = SessionLocal()
    try:
        document = db.query(Document).filter(
            Document.id == document_id
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )
        
        return DocumentStatusResponse(
            document_id=document.id,
            filename=document.filename,
            status=document.status,
            upload_time=document.upload_time,
            extracted_text=document.extracted_text,
            error_message=document.error_message,
        )
        
    finally:
        db.close()


# ============ Action Management Routes ============

@app.get("/actions", response_model=List[ActionDetailsResponse])
def get_all_actions(document_id: str = None, status_filter: str = None):
    """
    Get all detected actions with optional filtering.
    
    Query parameters:
    - document_id: Filter by document
    - status_filter: Filter by status (PENDING, APPROVED, REJECTED)
    """
    db = SessionLocal()
    try:
        query = db.query(Action)
        
        if document_id:
            query = query.filter(Action.document_id == document_id)
        
        if status_filter:
            query = query.filter(Action.status == status_filter)
        
        actions = query.order_by(Action.created_at.desc()).all()
        return [ActionDetailsResponse.from_orm(a) for a in actions]
        
    finally:
        db.close()


@app.get("/actions/{action_id}", response_model=ActionDetailsResponse)
def get_action(action_id: int):
    """
    Get a specific action by ID.
    """
    db = SessionLocal()
    try:
        action = db.query(Action).filter(Action.id == action_id).first()
        
        if not action:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Action {action_id} not found"
            )
        
        return ActionDetailsResponse.from_orm(action)
        
    finally:
        db.close()


@app.post("/actions/{action_id}/review")
def review_action(
    action_id: int,
    action_status: str = Query(..., alias="status"),
    reviewer_name: str = "human_reviewer",
    comments: str | None = None,
):
    """
    Update action status (approve/reject).
    
    Valid statuses: PENDING, APPROVED, REJECTED
    """
    if action_status not in [ACTION_STATUS_PENDING, ACTION_STATUS_APPROVED, ACTION_STATUS_REJECTED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be PENDING, APPROVED, or REJECTED"
        )
    
    db = SessionLocal()
    try:
        action = db.query(Action).filter(Action.id == action_id).first()
        
        if not action:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Action {action_id} not found"
            )
        
        if action_status == ACTION_STATUS_PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Review decision must be APPROVED or REJECTED"
            )

        if action.status in [ACTION_STATUS_APPROVED, ACTION_STATUS_REJECTED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Action already finalized as {action.status}"
            )

        decision = (
            REVIEW_DECISION_APPROVED
            if action_status == ACTION_STATUS_APPROVED
            else REVIEW_DECISION_REJECTED
        )
        review = create_review(
            action_id=action_id,
            decision=decision,
            reviewer=reviewer_name,
            comments=comments,
            db=db,
        )
        db.commit()

        logger.info(f"Action {action_id} reviewed by {reviewer_name}: {action_status}")
        
        return {
            "success": True,
            "message": f"Action {action_id} updated to {action_status}",
            "review": ReviewResponse.from_orm(review).model_dump(),
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating action: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Update failed: {str(e)}"
        )
    finally:
        db.close()


@app.post("/review/{action_id}")
def review_action_compat(
    action_id: int,
    action_status: str = Query(..., alias="status"),
    reviewer_name: str = "human_reviewer",
    comments: str | None = None,
):
    """Backward-compatible review endpoint for older frontend calls."""
    return review_action(action_id, action_status, reviewer_name, comments)


@app.get("/actions/{action_id}/history", response_model=ActionHistoryResponse)
def get_action_history(action_id: int):
    """Get action details with review and audit history."""
    db = SessionLocal()
    try:
        action = db.query(Action).filter(Action.id == action_id).first()
        if not action:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Action {action_id} not found"
            )

        reviews = db.query(Review).filter(Review.action_id == action_id).order_by(Review.timestamp.desc()).all()
        audits = db.query(AuditLog).filter(AuditLog.action_id == action_id).order_by(AuditLog.timestamp.desc()).all()

        return ActionHistoryResponse(
            action=ActionDetailsResponse.from_orm(action),
            reviews=[ReviewResponse.from_orm(r) for r in reviews],
            audits=[AuditLogResponse.from_orm(a) for a in audits],
        )
    finally:
        db.close()


@app.get("/documents/{document_id}/details", response_model=DocumentWithActionsResponse)
def get_document_details(document_id: str):
    """Get document info with generated actions and document-level audits."""
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )

        actions = db.query(Action).filter(Action.document_id == document_id).order_by(Action.created_at.desc()).all()
        audits = db.query(AuditLog).filter(AuditLog.document_id == document_id).order_by(AuditLog.timestamp.desc()).all()

        return DocumentWithActionsResponse(
            document=DocumentInfoResponse.from_orm(document),
            actions=[ActionDetailsResponse.from_orm(a) for a in actions],
            audits=[AuditLogResponse.from_orm(a) for a in audits],
        )
    finally:
        db.close()


# ============ Dashboard & Analytics Routes ============

@app.get("/dashboard", response_model=DashboardStats)
def dashboard():
    """
    Get dashboard statistics and summary.
    """
    db = SessionLocal()
    try:
        # Document stats
        total_documents = db.query(Document).count()
        processed_documents = db.query(Document).filter(
            Document.status == "processed"
        ).count()
        processing_documents = db.query(Document).filter(
            Document.status == "processing"
        ).count()
        failed_documents = db.query(Document).filter(
            Document.status == "failed"
        ).count()
        
        # Action stats
        total_actions = db.query(Action).count()
        pending_actions = db.query(Action).filter(
            Action.status == "PENDING"
        ).count()
        approved_actions = db.query(Action).filter(
            Action.status == "APPROVED"
        ).count()
        rejected_actions = db.query(Action).filter(
            Action.status == "REJECTED"
        ).count()
        
        return DashboardStats(
            total_documents=total_documents,
            processed_documents=processed_documents,
            processing_documents=processing_documents,
            failed_documents=failed_documents,
            total_actions=total_actions,
            pending_actions=pending_actions,
            approved_actions=approved_actions,
            rejected_actions=rejected_actions
        )
        
    finally:
        db.close()