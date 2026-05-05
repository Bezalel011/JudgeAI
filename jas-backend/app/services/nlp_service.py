"""
NLP Service - Legal information extraction using spaCy
Extracts entities, directives, dates, and actionable sentences from legal documents
"""

import re
import logging
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
import dateparser
import spacy
from spacy.matcher import Matcher

from app.logger import setup_logger

logger = setup_logger(__name__)


class NLPService:
    """Service for NLP-based legal document analysis"""
    
    # Directive verbs that indicate actionable content
    DIRECTIVE_VERBS = {
        "directed", "ordered", "shall", "must", "required", "is required to",
        "instructed", "commanded", "mandated", "compelled", "obligated",
        "directed to", "ordered to", "required to", "mandated to"
    }
    
    # Action type keywords for classification
    ACTION_KEYWORDS = {
        "compliance": [
            "shall", "must", "required", "directed", "ordered", "comply",
            "conform", "adhere", "follow", "implement", "execute"
        ],
        "appeal": [
            "appeal", "challenged", "may file", "liberty to", "entitled to appeal",
            "right to appeal", "appellate", "higher court"
        ],
        "review": [
            "review", "reconsider", "revisit", "examine", "scrutinize",
            "reassess", "re-evaluation", "rehear"
        ],
        "escalation": [
            "referred", "escalate", "higher authority", "superior court",
            "next level", "appeals court", "superior judge"
        ]
    }
    
    def __init__(self):
        """Initialize NLP service with spaCy model"""
        self.nlp = None
        self.matcher = None
        self._load_model()
    
    def _load_model(self):
        """Load spaCy model with fallback strategy"""
        models = ["en_core_web_trf", "en_core_web_lg", "en_core_web_sm"]
        
        for model in models:
            try:
                logger.info(f"Attempting to load spaCy model: {model}")
                self.nlp = spacy.load(model)
                logger.info(f"Successfully loaded spaCy model: {model}")
                self._setup_matcher()
                return
            except OSError:
                logger.warning(f"Model {model} not found, trying next...")
                continue
        
        # Fallback: Load minimal model
        logger.error("Could not load any pre-trained spaCy model")
        self.nlp = spacy.blank("en")
        logger.info("Loaded blank English spaCy model (no NER)")
        self._setup_matcher()
    
    def _setup_matcher(self):
        """Set up spaCy Matcher for legal patterns"""
        self.matcher = Matcher(self.nlp.vocab)
        
        # Pattern for legal sections/articles/rules
        section_pattern = [
            {"LOWER": {"IN": ["section", "article", "rule", "clause", "para", "paragraph"]}},
            {"IS_DIGIT": True}
        ]
        self.matcher.add("LEGAL_SECTION", [section_pattern])
        
        # Pattern for directives (shall X)
        directive_pattern = [
            {"LOWER": {"IN": ["shall", "must", "directed"]}}
        ]
        self.matcher.add("DIRECTIVE", [directive_pattern])
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract named entities from legal text
        
        Args:
            text: Full legal document text
            
        Returns:
            Dictionary with entity types and values
        """
        doc = self.nlp(text)
        
        entities = {
            "persons": [],
            "organizations": [],
            "dates": [],
            "legal_sections": []
        }
        
        try:
            # Extract NER entities if model supports it
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    if ent.text not in entities["persons"]:
                        entities["persons"].append(ent.text)
                elif ent.label_ == "ORG":
                    if ent.text not in entities["organizations"]:
                        entities["organizations"].append(ent.text)
                elif ent.label_ in ["DATE", "TIME"]:
                    if ent.text not in entities["dates"]:
                        entities["dates"].append(ent.text)
        except Exception as e:
            logger.warning(f"Error extracting NER entities: {e}")
        
        # Extract legal sections using matcher
        matches = self.matcher(doc)
        for match_id, start, end in matches:
            rule_name = self.nlp.vocab.strings[match_id]
            if rule_name == "LEGAL_SECTION":
                span = doc[start:end]
                section_text = span.text
                if section_text not in entities["legal_sections"]:
                    entities["legal_sections"].append(section_text)
        
        # Fallback: Extract legal sections using regex
        section_pattern = r"(?:Section|Article|Rule|Clause|Para(?:graph)?)\s+(\d+(?:[A-Za-z]*)?)"
        regex_matches = re.findall(section_pattern, text, re.IGNORECASE)
        for match in regex_matches:
            section_text = f"Section {match}" if match else None
            if section_text and section_text not in entities["legal_sections"]:
                entities["legal_sections"].append(section_text)
        
        logger.info(f"Extracted entities: {len(entities['persons'])} persons, "
                   f"{len(entities['organizations'])} orgs, "
                   f"{len(entities['legal_sections'])} legal sections")
        
        return entities
    
    def extract_directives(self, sentences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract directive/order sentences from document
        
        Args:
            sentences: List of preprocessed sentences
            
        Returns:
            List of directive dictionaries with sentence, type, and verb
        """
        directives: List[Dict[str, Any]] = []

        for s in sentences:
            sentence = s.get("sentence", "")
            sentence_lower = sentence.lower()

            # Check for directive verbs
            for verb in self.DIRECTIVE_VERBS:
                if verb in sentence_lower:
                    directives.append({
                        "sentence": sentence,
                        "page": s.get("page"),
                        "sentence_index": s.get("sentence_index"),
                        "char_start": s.get("char_start"),
                        "char_end": s.get("char_end"),
                        "type": "directive",
                        "verb": verb,
                        "confidence": 0.85
                    })
                    break

        logger.info(f"Extracted {len(directives)} directives")
        return directives
    
    def normalize_dates(self, text: str) -> List[Dict[str, Any]]:
        """
        Normalize and extract dates from legal text
        
        Args:
            text: Full document text
            
        Returns:
            List of normalized dates with original and ISO formats
        """
        normalized_dates = []
        
        # Parse dates using dateparser
        try:
            settings = {"STRICT_PARSING": False, "RETURN_AS_TIMEZONE_AWARE": False}
            
            # Extract date expressions
            date_patterns = [
                r"(?:within\s+(\d+)\s+days?)",
                r"(?:before|on|by|within)\s+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
                r"(?:\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})",
            ]
            
            for pattern in date_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    original_text = match.group(0)
                    
                    # Parse relative dates (e.g., "within 30 days")
                    days_match = re.match(r"within\s+(\d+)\s+days?", original_text, re.IGNORECASE)
                    if days_match:
                        days = int(days_match.group(1))
                        deadline = (datetime.today() + timedelta(days=days)).date().isoformat()
                        normalized_dates.append({
                            "original": original_text,
                            "normalized": deadline,
                            "type": "relative_deadline"
                        })
                    else:
                        # Try to parse absolute dates
                        parsed = dateparser.parse(original_text, settings=settings)
                        if parsed:
                            iso_date = parsed.date().isoformat()
                            normalized_dates.append({
                                "original": original_text,
                                "normalized": iso_date,
                                "type": "absolute_date"
                            })
            
            logger.info(f"Extracted and normalized {len(normalized_dates)} dates")
        except Exception as e:
            logger.error(f"Error normalizing dates: {e}")
        
        return normalized_dates
    
    def classify_actionable_sentences(self, sentences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Classify sentences as actionable and identify action types
        
        Args:
            sentences: List of preprocessed sentences
            
        Returns:
            List of actionable sentences with their classification
        """
        actionable: List[Dict[str, Any]] = []

        for s in sentences:
            sentence = s.get("sentence", "")
            sentence_lower = sentence.lower()

            # Check against action keywords
            for action_type, keywords in self.ACTION_KEYWORDS.items():
                for keyword in keywords:
                    if keyword in sentence_lower:
                        # Avoid duplicates
                        if not any(a.get("sentence") == sentence for a in actionable):
                            actionable.append({
                                "sentence": sentence,
                                "page": s.get("page"),
                                "sentence_index": s.get("sentence_index"),
                                "char_start": s.get("char_start"),
                                "char_end": s.get("char_end"),
                                "action_type": action_type,
                                "confidence": 0.8,
                                "keyword_match": keyword
                            })
                        break

        logger.info(f"Classified {len(actionable)} actionable sentences")
        return actionable
    
    def analyze_document(self, full_text: str, sentences: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Complete NLP analysis of legal document
        
        Args:
            full_text: Complete extracted text from document
            sentences: List of preprocessed sentences
            
        Returns:
            Dictionary with all NLP analysis results
        """
        try:
            logger.info("Starting NLP document analysis")
            
            analysis = {
                "entities": self.extract_entities(full_text),
                "directives": self.extract_directives(sentences),
                "actionable_sentences": self.classify_actionable_sentences(sentences),
                "dates": self.normalize_dates(full_text)
            }
            
            logger.info(f"NLP analysis complete: {len(analysis['directives'])} directives, "
                       f"{len(analysis['actionable_sentences'])} actionable sentences, "
                       f"{len(analysis['dates'])} dates")
            
            return analysis
        
        except Exception as e:
            logger.error(f"Error during NLP analysis: {e}")
            return {
                "entities": {"persons": [], "organizations": [], "dates": [], "legal_sections": []},
                "directives": [],
                "actionable_sentences": [],
                "dates": [],
                "error": str(e)
            }


# Global instance
nlp_service = NLPService()


def get_nlp_service() -> NLPService:
    """Get or create NLP service instance"""
    return nlp_service
