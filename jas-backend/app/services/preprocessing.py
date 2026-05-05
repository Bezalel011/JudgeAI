"""
Preprocessing Service - Handles text cleaning and normalization
"""

import re
import logging
from typing import List, Dict
from app.logger import setup_logger

logger = setup_logger(__name__)


class PreprocessingService:
    """Service for text preprocessing and normalization"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean extracted text by removing noise and normalizing.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        try:
            logger.debug("Starting text cleaning")
            
            # Remove multiple newlines
            text = re.sub(r'\n{3,}', '\n\n', text)
            
            # Remove leading/trailing whitespace from each line
            lines = [line.strip() for line in text.split('\n')]
            text = '\n'.join(lines)
            
            # Normalize whitespace (multiple spaces to single space)
            text = re.sub(r'[ \t]{2,}', ' ', text)
            
            # Remove form feed and other special characters
            text = re.sub(r'[\f\r\x00]', '', text)
            
            logger.debug("Text cleaning completed")
            return text
            
        except Exception as e:
            logger.error(f"Error during text cleaning: {str(e)}")
            return text
    
    @staticmethod
    def remove_headers_footers(text: str, threshold: int = 15) -> str:
        """
        Attempt to remove common headers and footers.
        
        Args:
            text: Cleaned text
            threshold: Maximum length for lines considered as headers/footers
            
        Returns:
            Text with headers/footers removed
        """
        try:
            lines = text.split('\n')
            filtered_lines = []
            
            for line in lines:
                # Keep non-empty lines that are reasonable length
                if line.strip() and len(line.strip()) > threshold:
                    filtered_lines.append(line)
            
            return '\n'.join(filtered_lines)
            
        except Exception as e:
            logger.warning(f"Error during header/footer removal: {str(e)}")
            return text
    
    @staticmethod
    def split_into_sentences(text: str) -> List[str]:
        """
        Split text into sentences.
        
        Args:
            text: Cleaned text
            
        Returns:
            List of sentences
        """
        try:
            # Split by common sentence endings
            sentences = re.split(r'(?<=[.!?])\s+', text)
            
            # Clean and filter sentences
            sentences = [s.strip() for s in sentences if s.strip()]
            
            logger.debug(f"Text split into {len(sentences)} sentences")
            return sentences
            
        except Exception as e:
            logger.error(f"Error during sentence splitting: {str(e)}")
            # Fallback: return text as single sentence
            return [text]
    
    @staticmethod
    def preprocess_pipeline(pages: List[Dict[str, str]]) -> List[Dict[str, object]]:
        """
        Complete preprocessing pipeline that preserves sentence metadata per page.

        Args:
            pages: List of page dicts {page: int, text: str}

        Returns:
            List of sentence metadata dicts with keys:
            - sentence, page, sentence_index, char_start, char_end
        """
        try:
            logger.info("Starting preprocessing pipeline")

            all_sentences: List[Dict[str, object]] = []

            for page_obj in pages:
                page_num = page_obj.get("page")
                page_text = page_obj.get("text", "") or ""

                # Clean and normalize page text
                page_text = PreprocessingService.clean_text(page_text)
                page_text = PreprocessingService.remove_headers_footers(page_text)

                # Split into sentences
                sentences = PreprocessingService.split_into_sentences(page_text)

                offset = 0
                for idx, sent in enumerate(sentences):
                    # Find sentence start from current offset to avoid duplicate matches
                    start = page_text.find(sent, offset)
                    if start == -1:
                        # fallback: try trimmed search
                        start = page_text.find(sent.strip(), offset)
                    if start == -1:
                        # give up and approximate
                        start = offset
                    end = start + len(sent)

                    all_sentences.append({
                        "sentence": sent,
                        "page": page_num,
                        "sentence_index": idx,
                        "char_start": start,
                        "char_end": end,
                    })

                    offset = end

            logger.info(f"Preprocessing complete. Extracted {len(all_sentences)} sentences")
            return all_sentences

        except Exception as e:
            logger.error(f"Error in preprocessing pipeline: {str(e)}")
            return []


preprocessing_service = PreprocessingService()
