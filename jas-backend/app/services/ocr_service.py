"""
OCR Service - Handles text extraction from PDFs
Supports both text-based and scanned PDFs with fallback logic
"""

import pytesseract
import pdfplumber
from typing import Tuple, List, Dict
import logging
from app.config import settings
from app.logger import setup_logger

logger = setup_logger(__name__)

# Configure tesseract path from environment
pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD


class OCRService:
    """Service for extracting text from PDF documents"""
    
    @staticmethod
    def extract_text(file_path: str) -> Tuple[List[Dict[str, str]], bool]:
        """
        Extract text from PDF file and return per-page text blocks.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Tuple[str, bool]: (extracted_text, success)
        """
        try:
            logger.info(f"Starting OCR extraction for: {file_path}")
            pages: List[Dict[str, str]] = []

            with pdfplumber.open(file_path) as pdf:
                logger.info(f"PDF has {len(pdf.pages)} pages")

                for page_num, page in enumerate(pdf.pages, 1):
                    # Try text extraction first
                    page_text = page.extract_text()

                    if page_text and page_text.strip():
                        logger.debug(f"Extracted text from page {page_num}")
                        pages.append({"page": page_num, "text": page_text})
                    else:
                        # Fallback to OCR for scanned pages
                        logger.debug(f"No text found on page {page_num}, attempting OCR")
                        try:
                            ocr_text = OCRService._ocr_page(page, page_num)
                            pages.append({"page": page_num, "text": ocr_text})
                        except Exception as e:
                            logger.warning(f"OCR failed on page {page_num}: {str(e)}")
                            pages.append({"page": page_num, "text": ""})
            
            if not any(p.get("text") for p in pages):
                logger.warning(f"No text extracted from {file_path}")
                return [], False

            total_chars = sum(len(p.get("text", "")) for p in pages)
            logger.info(f"Successfully extracted text from {file_path} ({total_chars} characters across {len(pages)} pages)")
            return pages, True
            
        except Exception as e:
            logger.error(f"Error during OCR extraction for {file_path}: {str(e)}")
            return [], False  # ✅ FIXED: Return empty list, not empty string (consistent with success case)
    
    @staticmethod
    def _ocr_page(page, page_num: int) -> str:
        """
        Perform OCR on a single PDF page.
        
        Args:
            page: pdfplumber page object
            page_num: Page number for logging
            
        Returns:
            Extracted text from OCR
        """
        try:
            image = page.to_image().original
            ocr_text = pytesseract.image_to_string(image)
            return ocr_text
        except Exception as e:
            logger.error(f"OCR failed for page {page_num}: {str(e)}")
            raise


ocr_service = OCRService()
