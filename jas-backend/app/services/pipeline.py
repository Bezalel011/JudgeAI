"""
Pipeline Orchestrator - Coordinates the document processing workflow
"""

import logging
from typing import Dict, List, Any
from app.logger import setup_logger
from app.services.ingestion import ingestion_service
from app.services.ocr_service import ocr_service
from app.services.preprocessing import preprocessing_service
from app.services.nlp_service import get_nlp_service
from app.services.action_engine import get_action_engine
from app.db import SessionLocal, Action, log_event, AUDIT_ENTITY_ACTION

logger = setup_logger(__name__)


class PipelineOrchestrator:
    """Orchestrates the complete document processing pipeline"""
    
    @staticmethod
    def _convert_nlp_analysis_to_actions(nlp_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Convert NLP analysis results into structured actions using Action Engine
        
        Args:
            nlp_analysis: Dictionary containing NLP analysis results
            
        Returns:
            List of structured action dictionaries
        """
        try:
            # Use Action Engine to generate structured actions
            action_engine = get_action_engine()
            actions = action_engine.generate_actions(nlp_analysis)
            
            logger.info(f"Generated {len(actions)} structured actions using Action Engine")
            return actions
            
        except Exception as e:
            logger.error(f"Error converting NLP analysis to actions: {e}")
            return []
    
    @staticmethod
    def process_document(document_id: str) -> Dict[str, Any]:
        """
        Complete document processing pipeline.
        
        Workflow:
        1. Load document from database
        2. Run OCR extraction
        3. Preprocess text
        4. Detect actions
        5. Store results
        
        Args:
            document_id: Unique document identifier
            
        Returns:
            Dictionary with processing results and status
        """
        try:
            logger.info(f"Starting document processing for: {document_id}")
            
            # Step 1: Load document
            file_path, exists = ingestion_service.get_document_path(document_id)
            if not exists:
                logger.error(f"Document not found: {document_id}")
                ingestion_service.update_document_status(
                    document_id, 
                    "failed",
                    error_message="Document file not found"
                )
                return {
                    "success": False,
                    "document_id": document_id,
                    "message": "Document not found",
                    "actions": []
                }
            
            # Update status to processing
            ingestion_service.update_document_status(document_id, "processing")
            
            # Step 2: Run OCR (returns per-page text blocks)
            logger.info(f"Running OCR for document: {document_id}")
            pages, ocr_success = ocr_service.extract_text(file_path)

            if not ocr_success or not pages:
                logger.error(f"OCR extraction failed for: {document_id}")
                ingestion_service.update_document_status(
                    document_id,
                    "failed",
                    error_message="OCR extraction failed"
                )
                return {
                    "success": False,
                    "document_id": document_id,
                    "message": "OCR extraction failed",
                    "actions": []
                }
            
            # Step 3: Preprocess text (preserves page & char metadata)
            logger.info(f"Preprocessing text for document: {document_id}")
            full_text = "\n".join([p.get("text", "") for p in pages])
            sentences = preprocessing_service.preprocess_pipeline(pages)
            
            if not sentences:
                logger.warning(f"No sentences extracted after preprocessing: {document_id}")
                ingestion_service.update_document_status(
                    document_id,
                    "processed",
                    extracted_text=full_text
                )
                return {
                    "success": True,
                    "document_id": document_id,
                    "message": "Processing completed (no sentences found)",
                    "actions": [],
                    "sentence_count": 0
                }
            
            # Step 4: NLP Analysis - Extract entities, directives, dates
            logger.info(f"Running NLP analysis for document: {document_id}")
            nlp_service = get_nlp_service()
            nlp_analysis = nlp_service.analyze_document(full_text, sentences)
            logger.info(f"NLP analysis complete: {len(nlp_analysis.get('directives', []))} directives, "
                       f"{len(nlp_analysis.get('actionable_sentences', []))} actionable sentences")
            
            # Step 5: Detect actions using Action Engine
            logger.info(f"Detecting actions from {len(sentences)} sentences")
            nlp_actions = PipelineOrchestrator._convert_nlp_analysis_to_actions(nlp_analysis)
            
            actions = nlp_actions
            logger.info(f"Found {len(actions)} actions")
            
            # Step 5: Store extracted text and update status
            ingestion_service.update_document_status(
                document_id,
                "processed",
                extracted_text=full_text
            )
            
            # Step 6: Save actions to database
            PipelineOrchestrator._save_actions(document_id, actions)
            
            logger.info(f"Document processing completed successfully: {document_id}")
            
            return {
                "success": True,
                "document_id": document_id,
                "message": "Document processed successfully",
                "sentence_count": len(sentences),
                "actions": actions,
                "action_count": len(actions)
            }
            
        except Exception as e:
            logger.error(f"Error during pipeline processing: {str(e)}")
            ingestion_service.update_document_status(
                document_id,
                "failed",
                error_message=str(e)
            )
            return {
                "success": False,
                "document_id": document_id,
                "message": f"Processing error: {str(e)}",
                "actions": []
            }
    
    @staticmethod
    def _save_actions(document_id: str, actions: List[Dict[str, Any]]) -> int:
        """
        Save structured actions to the database.
        
        Actions now include: action_type, task, department, deadline, priority, confidence, evidence
        
        Args:
            document_id: Document identifier
            actions: List of action dictionaries from Action Engine
            
        Returns:
            Number of actions saved
        """
        db = SessionLocal()
        count = 0
        
        try:
            for action_data in actions:
                # Evidence may be a structured dict with text/page/index/span
                ev = action_data.get("evidence") or {}
                ev_text = ev.get("text") if isinstance(ev, dict) else ev

                action = Action(
                    document_id=document_id,
                    type=action_data.get("action_type", "UNKNOWN"),
                    task=action_data.get("task", ""),
                    department=action_data.get("department"),
                    deadline=action_data.get("deadline"),
                    priority=action_data.get("priority"),
                    confidence=str(action_data.get("confidence", 0.0)),
                    confidence_components=action_data.get("confidence_components"),
                    evidence_text=ev_text,
                    evidence_page=ev.get("page") if isinstance(ev, dict) else None,
                    evidence_index=ev.get("sentence_index") if isinstance(ev, dict) else None,
                    evidence_start=ev.get("char_start") if isinstance(ev, dict) else None,
                    evidence_end=ev.get("char_end") if isinstance(ev, dict) else None,
                    status="PENDING"
                )
                db.add(action)
                count += 1
            
                db.flush()

                log_event(
                    entity_type=AUDIT_ENTITY_ACTION,
                    entity_id=str(action.id),
                    action="created",
                    performed_by="system",
                    details={
                        "type": action.type,
                        "status": action.status,
                        "confidence": action.confidence,
                    },
                    document_id=document_id,
                    action_id=action.id,
                    db=db,
                )

            db.commit()
            logger.info(f"Saved {count} structured actions to database for document: {document_id}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving actions: {str(e)}")
        finally:
            db.close()
        
        return count


pipeline_orchestrator = PipelineOrchestrator()
