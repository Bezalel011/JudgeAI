"""
Action Engine Service - Converts NLP analysis into structured action plans
Transforms raw NLP outputs into decision-ready, explainable actions
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from app.logger import setup_logger

logger = setup_logger(__name__)


class ActionEngine:
    """Converts NLP outputs into structured, actionable decision plans"""
    
    # Department mapping from entities and keywords
    DEPARTMENT_MAP = {
        # Revenue/Finance related
        "revenue": "Revenue Department",
        "finance": "Finance Department",
        "treasury": "Finance Department",
        "payment": "Finance Department",
        "compensation": "Finance Department",
        "tax": "Tax Department",
        "customs": "Customs Department",
        
        # Law enforcement
        "police": "Police Department",
        "crime": "Police Department",
        "investigation": "Police Department",
        "fir": "Police Department",
        
        # Local administration
        "municipality": "Municipal Corporation",
        "municipal": "Municipal Corporation",
        "corporation": "Municipal Corporation",
        "civic": "Municipal Corporation",
        "local": "Local Administration",
        
        # Health & Welfare
        "health": "Health Department",
        "medical": "Health Department",
        "hospital": "Health Department",
        "welfare": "Welfare Department",
        "social": "Social Welfare",
        
        # Education
        "education": "Education Department",
        "school": "Education Department",
        "college": "Education Department",
        "university": "Education Department",
        
        # Water & Sanitation
        "water": "Water Supply Department",
        "sewerage": "Sewerage Department",
        "sanitation": "Sanitation Department",
        
        # Infrastructure
        "roads": "Public Works Department",
        "highways": "Public Works Department",
        "construction": "Public Works Department",
        "infrastructure": "Public Works Department",
        
        # Environment
        "environment": "Environment Department",
        "pollution": "Environment Department",
        "forest": "Forest Department",
        "wildlife": "Forest Department",
        
        # Court/Judicial
        "court": "Judicial Authority",
        "judge": "Judicial Authority",
        "magistrate": "Judicial Authority",
        "district court": "District Court",
        "high court": "High Court",
        "supreme court": "Supreme Court",
    }
    
    # Priority rules
    PRIORITY_WEIGHTS = {
        "compliance": 0.9,      # Highest priority
        "escalation": 0.8,      # High priority
        "appeal": 0.6,          # Medium priority
        "review": 0.4,          # Lower priority
    }
    
    # Task generation templates
    TASK_TEMPLATES = {
        "compliance": {
            "default": "Ensure compliance with court directives",
            "submit": "Submit required documents/report",
            "pay": "Process payment as ordered",
            "appear": "Appear before the court/authority",
            "provide": "Provide requested information/documents",
            "implement": "Implement the ordered action",
            "follow": "Follow the prescribed procedure",
        },
        "appeal": {
            "default": "File appeal to higher court",
            "file": "File appeal petition",
            "challenge": "Challenge the order in appellate court",
            "review": "Request review of the decision",
        },
        "review": {
            "default": "Review the matter",
            "reconsider": "Reconsider the case",
            "examine": "Examine all aspects",
            "reassess": "Reassess the situation",
        },
        "escalation": {
            "default": "Escalate to higher authority",
            "refer": "Refer to competent authority",
            "report": "Report to superior",
            "escalate": "Escalate the matter",
        }
    }
    
    def __init__(self):
        """Initialize Action Engine"""
        logger.info("Action Engine initialized")
    
    def generate_actions(self, nlp_output: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate structured actions from NLP analysis output
        
        Args:
            nlp_output: Dictionary containing:
                - entities: extracted entities
                - directives: detected directives
                - actionable_sentences: classified sentences
                - dates: normalized dates
        
        Returns:
            List of structured action dictionaries
        """
        try:
            logger.info("Starting action generation from NLP output")
            actions = []
            
            # Extract components from NLP output
            actionable_sentences = nlp_output.get("actionable_sentences", [])
            entities = nlp_output.get("entities", {})
            dates = nlp_output.get("dates", [])
            directives = nlp_output.get("directives", [])
            
            # Generate actions from actionable sentences
            for sentence_data in actionable_sentences:
                action = self._create_action_from_sentence(
                    sentence_data,
                    entities,
                    dates,
                    directives
                )
                if action:
                    actions.append(action)
            
            # Also generate actions from directives if not covered
            # Compare using evidence text to avoid unhashable dict types
            directive_sentences = set()
            for a in actions:
                ev = a.get("evidence")
                if isinstance(ev, dict):
                    directive_sentences.add(ev.get("text"))
                else:
                    directive_sentences.add(ev)

            for directive in directives:
                directive_sentence = directive.get("sentence", "")
                if directive_sentence not in directive_sentences:
                    action = self._create_action_from_directive(
                        directive,
                        entities,
                        dates
                    )
                    if action:
                        actions.append(action)
            
            logger.info(f"Generated {len(actions)} actions from NLP output")
            return actions
        
        except Exception as e:
            logger.error(f"Error generating actions: {e}")
            return []
    
    def _create_action_from_sentence(
        self,
        sentence_data: Dict[str, Any],
        entities: Dict[str, List[str]],
        dates: List[Dict[str, Any]],
        directives: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Create a structured action from an actionable sentence
        
        Args:
            sentence_data: Actionable sentence with classification
            entities: Extracted entities
            dates: Normalized dates
            directives: Detected directives
        
        Returns:
            Structured action dictionary
        """
        try:
            sentence = sentence_data.get("sentence", "")
            # Preserve metadata if present
            page = sentence_data.get("page")
            sentence_index = sentence_data.get("sentence_index")
            char_start = sentence_data.get("char_start")
            char_end = sentence_data.get("char_end")
            action_type = sentence_data.get("action_type", "compliance").lower()
            confidence = sentence_data.get("confidence", 0.8)
            
            # Generate task from sentence
            task = self._generate_task(sentence, action_type)
            
            # Assign department
            department = self._assign_department(sentence, entities)
            
            # Assign deadline
            deadline = self._assign_deadline(sentence, dates)
            
            # Compute priority
            priority = self._compute_priority(deadline, action_type, confidence)
            
            # Enhance confidence based on signals
            enhanced_confidence = self._compute_confidence(
                sentence_data,
                entities,
                deadline,
                directives
            )
            
            action = {
                "action_type": action_type,
                "task": task,
                "department": department,
                "deadline": deadline,
                "priority": priority,
                "confidence": enhanced_confidence,
                "evidence": {
                    "text": sentence,
                    "page": page,
                    "sentence_index": sentence_index,
                    "char_start": char_start,
                    "char_end": char_end,
                },
                "created_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Created {action_type} action: {task}")
            return action
        
        except Exception as e:
            logger.error(f"Error creating action from sentence: {e}")
            return None
    
    def _create_action_from_directive(
        self,
        directive: Dict[str, Any],
        entities: Dict[str, List[str]],
        dates: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Create a structured action from a detected directive
        
        Args:
            directive: Detected directive with verb
            entities: Extracted entities
            dates: Normalized dates
        
        Returns:
            Structured action dictionary
        """
        try:
            sentence = directive.get("sentence", "")
            page = directive.get("page")
            sentence_index = directive.get("sentence_index")
            char_start = directive.get("char_start")
            char_end = directive.get("char_end")
            verb = directive.get("verb", "")
            confidence = directive.get("confidence", 0.85)
            
            # Determine action type from verb
            action_type = self._classify_from_verb(verb)
            
            # Generate task
            task = self._generate_task(sentence, action_type)
            
            # Assign department
            department = self._assign_department(sentence, entities)
            
            # Assign deadline
            deadline = self._assign_deadline(sentence, dates)
            
            # Compute priority
            priority = self._compute_priority(deadline, action_type, confidence)
            
            # Enhanced confidence
            enhanced_confidence = self._compute_confidence_from_directive(
                directive,
                entities,
                deadline
            )
            
            action = {
                "action_type": action_type,
                "task": task,
                "department": department,
                "deadline": deadline,
                "priority": priority,
                "confidence": enhanced_confidence,
                "evidence": {
                    "text": sentence,
                    "page": page,
                    "sentence_index": sentence_index,
                    "char_start": char_start,
                    "char_end": char_end,
                },
                "created_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Created directive-based {action_type} action: {task}")
            return action
        
        except Exception as e:
            logger.error(f"Error creating action from directive: {e}")
            return None
    
    def _generate_task(self, sentence: str, action_type: str) -> str:
        """
        Generate a clean, summarized task from a sentence
        
        Args:
            sentence: Original sentence
            action_type: Type of action
        
        Returns:
            Clean task description
        """
        try:
            sentence_lower = sentence.lower()
            
            # Extract key verbs for task generation
            verb_map = {
                "submit": "Submit required documents/reports",
                "pay": "Process payment as ordered",
                "appear": "Appear before the court",
                "provide": "Provide requested information",
                "implement": "Implement the ordered action",
                "comply": "Ensure compliance with directives",
                "file": "File appeal/petition",
                "appeal": "File appeal to higher court",
                "challenge": "Challenge the order",
                "review": "Review the matter",
                "reconsider": "Reconsider the case",
                "refer": "Refer to competent authority",
                "report": "Report to superior authority",
                "release": "Release as ordered",
                "award": "Award compensation as directed",
                "direct": "Execute the court directive",
                "ordered": "Execute the court order",
            }
            
            # Find matching verb in sentence
            for verb, task_template in verb_map.items():
                if verb in sentence_lower:
                    return task_template
            
            # Fallback to template-based generation
            templates = self.TASK_TEMPLATES.get(action_type, {})
            default_task = templates.get("default", f"Execute {action_type} action")
            
            return default_task
        
        except Exception as e:
            logger.warning(f"Error generating task: {e}")
            return f"Execute {action_type} action"
    
    def _assign_department(
        self,
        sentence: str,
        entities: Dict[str, List[str]]
    ) -> str:
        """
        Assign responsible department using entity extraction
        
        Args:
            sentence: Original sentence
            entities: Extracted entities
        
        Returns:
            Department name
        """
        try:
            sentence_lower = sentence.lower()
            
            # Check organizations extracted
            organizations = entities.get("organizations", [])
            for org in organizations:
                org_lower = org.lower()
                for keyword, dept in self.DEPARTMENT_MAP.items():
                    if keyword in org_lower:
                        logger.info(f"Mapped organization '{org}' to department '{dept}'")
                        return dept
            
            # Check sentence for department keywords
            for keyword, dept in self.DEPARTMENT_MAP.items():
                if keyword in sentence_lower:
                    logger.info(f"Mapped keyword '{keyword}' to department '{dept}'")
                    return dept
            
            # Default to Generic Authority
            return "Concerned Authority"
        
        except Exception as e:
            logger.warning(f"Error assigning department: {e}")
            return "Concerned Authority"
    
    def _assign_deadline(self, sentence: str, dates: List[Dict[str, Any]]) -> Optional[str]:
        """
        Assign deadline from normalized dates
        
        Args:
            sentence: Original sentence
            dates: List of normalized dates from NLP
        
        Returns:
            ISO format deadline or None
        """
        try:
            # Look for dates in the list
            for date_obj in dates:
                # Check if date is within reasonable range (not in past)
                normalized = date_obj.get("normalized")
                if normalized:
                    try:
                        deadline_date = datetime.fromisoformat(normalized).date()
                        today = datetime.today().date()
                        
                        # Accept if deadline is in future or within 2 days past (for processing)
                        if (deadline_date - today).days >= -2:
                            logger.info(f"Assigned deadline: {normalized}")
                            return normalized
                    except:
                        pass
            
            # Fallback: Extract days from sentence
            import re
            match = re.search(r'within\s+(\d+)\s+days?', sentence, re.IGNORECASE)
            if match:
                days = int(match.group(1))
                deadline = (datetime.today() + timedelta(days=days)).date().isoformat()
                logger.info(f"Calculated deadline from sentence: {deadline}")
                return deadline
            
            return None
        
        except Exception as e:
            logger.warning(f"Error assigning deadline: {e}")
            return None
    
    def _compute_priority(
        self,
        deadline: Optional[str],
        action_type: str,
        confidence: float
    ) -> str:
        """
        Compute priority based on deadline and action type
        
        Args:
            deadline: ISO format deadline
            action_type: Type of action
            confidence: Confidence score
        
        Returns:
            Priority level: High, Medium, Low
        """
        try:
            # Base priority from action type
            base_priority = self.PRIORITY_WEIGHTS.get(action_type, 0.5)
            
            # Adjust based on deadline
            if deadline:
                try:
                    deadline_date = datetime.fromisoformat(deadline).date()
                    days_until = (deadline_date - datetime.today().date()).days
                    
                    if days_until <= 7:
                        base_priority += 0.2  # Urgent
                    elif days_until <= 30:
                        base_priority += 0.1  # Important
                except:
                    pass
            
            # Adjust based on confidence
            base_priority *= confidence
            
            # Map to priority level
            if base_priority >= 0.75:
                return "High"
            elif base_priority >= 0.45:
                return "Medium"
            else:
                return "Low"
        
        except Exception as e:
            logger.warning(f"Error computing priority: {e}")
            return "Medium"
    
    def _compute_confidence(
        self,
        sentence_data: Dict[str, Any],
        entities: Dict[str, List[str]],
        deadline: Optional[str],
        directives: List[Dict[str, Any]]
    ) -> float:
        """
        Compute enhanced confidence score based on multiple signals
        
        Args:
            sentence_data: Sentence classification data
            entities: Extracted entities
            deadline: Assigned deadline
            directives: Detected directives
        
        Returns:
            Confidence score (0.0-1.0)
        """
        try:
            # Base confidence from NLP
            base_confidence = sentence_data.get("confidence", 0.7)
            confidence = base_confidence
            
            # Signal 1: Entity presence (entities = clearer action)
            entity_count = sum(len(v) for v in entities.values())
            entity_signal = min(0.1, entity_count * 0.02)
            confidence += entity_signal
            
            # Signal 2: Deadline specified (deadline = clearer action)
            if deadline:
                confidence += 0.05
            
            # Signal 3: Directive presence (directives = official action)
            if directives:
                confidence += 0.05
            
            # Cap at 0.99 (never 1.0 - always uncertain in NLP)
            return min(0.99, confidence)
        
        except Exception as e:
            logger.warning(f"Error computing confidence: {e}")
            return 0.8
    
    def _compute_confidence_from_directive(
        self,
        directive: Dict[str, Any],
        entities: Dict[str, List[str]],
        deadline: Optional[str]
    ) -> float:
        """
        Compute confidence for directive-based actions
        
        Args:
            directive: Directive data
            entities: Extracted entities
            deadline: Assigned deadline
        
        Returns:
            Confidence score
        """
        try:
            # Directives are high confidence by nature
            base_confidence = directive.get("confidence", 0.85)
            confidence = base_confidence
            
            # Entity presence
            entity_count = sum(len(v) for v in entities.values())
            entity_signal = min(0.1, entity_count * 0.02)
            confidence += entity_signal
            
            # Deadline presence
            if deadline:
                confidence += 0.05
            
            return min(0.99, confidence)
        
        except Exception as e:
            logger.warning(f"Error computing directive confidence: {e}")
            return 0.85
    
    def _classify_from_verb(self, verb: str) -> str:
        """
        Classify action type from directive verb
        
        Args:
            verb: Directive verb
        
        Returns:
            Action type classification
        """
        compliance_verbs = {"directed", "ordered", "shall", "must", "required", "instructed", "mandated"}
        appeal_verbs = {"appeal", "challenged", "may file"}
        review_verbs = {"review", "reconsider", "examine", "reassess"}
        escalation_verbs = {"referred", "escalate", "superior"}
        
        verb_lower = verb.lower()
        
        if verb_lower in compliance_verbs:
            return "compliance"
        elif verb_lower in appeal_verbs:
            return "appeal"
        elif verb_lower in review_verbs:
            return "review"
        elif verb_lower in escalation_verbs:
            return "escalation"
        else:
            return "compliance"  # Default


# Global instance
action_engine = ActionEngine()


def get_action_engine() -> ActionEngine:
    """Get or create Action Engine instance"""
    return action_engine
