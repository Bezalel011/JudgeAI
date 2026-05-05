"""
Document Ingestion Service - Handles file uploads and metadata storage
"""

import os
import uuid
from datetime import datetime
from typing import List, Tuple
import logging
from app.config import settings
from app.logger import setup_logger
from app.db import (
    SessionLocal,
    Document,
    log_event,
    AUDIT_ENTITY_DOCUMENT,
    DOCUMENT_STATUS_UPLOADED,
    DOCUMENT_STATUS_PROCESSING,
    DOCUMENT_STATUS_PROCESSED,
    DOCUMENT_STATUS_FAILED,
)

logger = setup_logger(__name__)


class IngestionService:
    """Service for ingesting and storing documents"""

    VALID_DOCUMENT_STATUS_FLOW = {
        DOCUMENT_STATUS_UPLOADED: {DOCUMENT_STATUS_PROCESSING, DOCUMENT_STATUS_FAILED},
        DOCUMENT_STATUS_PROCESSING: {DOCUMENT_STATUS_PROCESSED, DOCUMENT_STATUS_FAILED},
        DOCUMENT_STATUS_PROCESSED: set(),
        DOCUMENT_STATUS_FAILED: {DOCUMENT_STATUS_PROCESSING},
    }
    
    @staticmethod
    def save_document(file_content: bytes, filename: str) -> Tuple[str, bool, str]:
        """
        Save an uploaded file to storage and create database record.
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            
        Returns:
            Tuple[document_id, success, message]
        """
        try:
            # Generate unique document ID
            document_id = str(uuid.uuid4())
            
            # Create file path
            file_extension = os.path.splitext(filename)[1]
            stored_filename = f"{document_id}{file_extension}"
            file_path = os.path.join(settings.DOCUMENTS_DIR, stored_filename)
            
            # Save file
            os.makedirs(settings.DOCUMENTS_DIR, exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            logger.info(f"File saved to {file_path}")
            
            # Create database record
            db = SessionLocal()
            try:
                document = Document(
                    id=document_id,
                    filename=filename,
                    file_path=file_path,
                    upload_time=datetime.utcnow(),
                    status=DOCUMENT_STATUS_UPLOADED
                )
                db.add(document)
                db.flush()

                log_event(
                    entity_type=AUDIT_ENTITY_DOCUMENT,
                    entity_id=document_id,
                    action="created",
                    performed_by="system",
                    details={"filename": filename, "status": DOCUMENT_STATUS_UPLOADED},
                    document_id=document_id,
                    db=db,
                )
                db.commit()
                logger.info(f"Document record created with ID: {document_id}")
                
                return document_id, True, f"Document {filename} uploaded successfully"
                
            except Exception as e:
                db.rollback()
                logger.error(f"Database error while saving document: {str(e)}")
                # Clean up file if database operation fails
                if os.path.exists(file_path):
                    os.remove(file_path)
                return "", False, f"Database error: {str(e)}"
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error during file ingestion: {str(e)}")
            return "", False, f"Ingestion error: {str(e)}"
    
    @staticmethod
    def get_document_path(document_id: str) -> Tuple[str, bool]:
        """
        Retrieve document file path from database.
        
        Args:
            document_id: Unique document identifier
            
        Returns:
            Tuple[file_path, exists]
        """
        db = SessionLocal()
        try:
            document = db.query(Document).filter(
                Document.id == document_id
            ).first()
            
            if not document:
                logger.warning(f"Document not found: {document_id}")
                return "", False
            
            if not os.path.exists(document.file_path):
                logger.error(f"Document file not found on disk: {document.file_path}")
                return "", False
            
            return document.file_path, True
            
        finally:
            db.close()
    
    @staticmethod
    def update_document_status(document_id: str, status: str, 
                               extracted_text: str = None, 
                               error_message: str = None) -> bool:
        """
        Update document status and optionally store extracted text.
        
        Args:
            document_id: Unique document identifier
            status: New status (uploaded, processing, processed, failed)
            extracted_text: Extracted text content
            error_message: Error message if processing failed
            
        Returns:
            Success boolean
        """
        db = SessionLocal()
        try:
            document = db.query(Document).filter(
                Document.id == document_id
            ).first()
            
            if not document:
                logger.warning(f"Document not found for update: {document_id}")
                return False

            prev_status = document.status
            allowed = IngestionService.VALID_DOCUMENT_STATUS_FLOW.get(prev_status, set())
            if status != prev_status and status not in allowed:
                logger.warning(
                    f"Invalid document status transition for {document_id}: {prev_status} -> {status}"
                )
                return False
            
            document.status = status
            if extracted_text is not None:
                document.extracted_text = extracted_text
            if error_message is not None:
                document.error_message = error_message

            log_event(
                entity_type=AUDIT_ENTITY_DOCUMENT,
                entity_id=document_id,
                action="updated",
                performed_by="system",
                details={
                    "from_status": prev_status,
                    "to_status": status,
                    "has_extracted_text": extracted_text is not None,
                    "error_message": error_message,
                },
                document_id=document_id,
                db=db,
            )
            
            db.commit()
            logger.info(f"Document {document_id} status updated to: {status}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating document status: {str(e)}")
            return False
        finally:
            db.close()


ingestion_service = IngestionService()
