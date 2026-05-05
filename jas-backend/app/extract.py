"""
DEPRECATED: This module is kept for backward compatibility only.

Use app.services.ocr_service.OCRService instead.

This file will be removed in v3.0.0
"""

import warnings
from app.services.ocr_service import ocr_service

warnings.warn(
    "app.extract module is deprecated. Use app.services.ocr_service instead.",
    DeprecationWarning,
    stacklevel=2
)


def pdf_to_text(path):
    """
    Extract text from PDF file.
    
    DEPRECATED: Use ocr_service.extract_text() instead.
    
    Args:
        path: Path to PDF file
        
    Returns:
        Extracted text as string
    """
    text, success = ocr_service.extract_text(path)
    return text if success else ""