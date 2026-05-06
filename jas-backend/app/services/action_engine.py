"""
Advanced Action Engine Service
Improved legal workflow extraction engine
"""

import logging
import re

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from app.logger import setup_logger

logger = setup_logger(__name__)


class ActionEngine:

    # ---------------------------------------------------------
    # DEPARTMENT MAPPING
    # ---------------------------------------------------------

    DEPARTMENT_MAP = {
        "revenue": "Revenue Department",
        "finance": "Finance Department",
        "payment": "Finance Department",
        "compensation": "Finance Department",

        "police": "Police Department",
        "investigation": "Police Department",

        "municipality": "Municipal Corporation",
        "municipal": "Municipal Corporation",

        "health": "Health Department",
        "medical": "Health Department",

        "education": "Education Department",
        "school": "Education Department",

        "court": "Judicial Authority",
        "judge": "Judicial Authority",
        "high court": "High Court",
        "supreme court": "Supreme Court",
    }

    PRIORITY_WEIGHTS = {
        "compliance": 0.9,
        "escalation": 0.8,
        "appeal": 0.6,
        "review": 0.4,
    }

    # ---------------------------------------------------------
    # ACTION KEYWORDS
    # ---------------------------------------------------------

    ACTION_KEYWORDS = [

        # Generic directives
        "shall",
        "must",
        "directed to",
        "required to",

        # Financial
        "shall pay",
        "pay rs",
        "cost",
        "costs",
        "entitled to",

        # Property / delivery
        "shall deliver",
        "shall be delivered",
        "handed over",
        "shall be handed over",

        # Court procedural
        "shall determine",
        "shall decide",
        "shall direct",

        # Possession
        "deliver possession",
        "put in possession",

        # Appeals
        "may file appeal",
    ]

    def __init__(self):
        logger.info("Advanced Action Engine initialized")

    # ---------------------------------------------------------
    # STRICT FILTERING
    # ---------------------------------------------------------

    def _is_valid_action_sentence(self, sentence: str) -> bool:

        s = sentence.lower()

        # Ignore huge reasoning paragraphs
        if len(s.split()) > 40:
            return False

        # Ignore legal reasoning / arguments
        ignore_phrases = [

            # Legal reasoning
            "it is held",
            "it is observed",
            "it is settled law",
            "learned counsel",
            "the prosecution",
            "the appellant contended",
            "the witness stated",
            "evidence on record",
            "cross examination",
            "dying declaration",

            # Arguments
            "it is urged",
            "it is submitted",
            "the contention",
            "the court has considered",

            # Citations
            "supra",
            "vs.",
            "v.",
            "section ",
            "order ii rule",

            # Generic discussion
            "this court is of the view",
            "cause of action",

            # Procedural junk
            "registry is directed",
            "copy of the",
            "hand over copies",
            "supply a copy",
        ]

        for phrase in ignore_phrases:
            if phrase in s:
                return False

        # Strong directive patterns
        for keyword in self.ACTION_KEYWORDS:
            if keyword in s:
                return True

        return False

    # ---------------------------------------------------------
    # MAIN GENERATION
    # ---------------------------------------------------------

    def generate_actions(self, nlp_output: Dict[str, Any]) -> List[Dict[str, Any]]:

        try:

            actions = []

            actionable_sentences = nlp_output.get(
                "actionable_sentences",
                []
            )

            entities = nlp_output.get("entities", {})
            dates = nlp_output.get("dates", [])

            order_mode = False

            for sentence_data in actionable_sentences:

                sentence = sentence_data.get("sentence", "")

                s = sentence.lower()

                # Detect ORDER section
                if "order" in s:
                    order_mode = True

                # Filter
                if not self._is_valid_action_sentence(sentence):
                    continue

                action = self._create_action(
                    sentence_data,
                    entities,
                    dates,
                    order_mode
                )

                if action:
                    actions.append(action)

            logger.info(f"Generated {len(actions)} actions")

            return actions

        except Exception as e:
            logger.error(f"Action generation failed: {e}")
            return []

    # ---------------------------------------------------------
    # CREATE ACTION
    # ---------------------------------------------------------

    def _create_action(
        self,
        sentence_data: Dict[str, Any],
        entities: Dict[str, List[str]],
        dates: List[Dict[str, Any]],
        order_mode: bool
    ) -> Optional[Dict[str, Any]]:

        try:

            sentence = sentence_data.get("sentence", "")
            base_confidence = sentence_data.get("confidence", 0.75)

            confidence_bonus = 0.15 if order_mode else 0

            sentence_lower = sentence.lower()

            directive_score = min(1.0, float(base_confidence) + confidence_bonus)
            entity_score = 0.2
            if any(name.lower() in sentence_lower for name in entities.get("organizations", [])):
                entity_score += 0.4
            if any(name.lower() in sentence_lower for name in entities.get("persons", [])):
                entity_score += 0.2
            if entities.get("legal_sections"):
                entity_score += 0.1
            entity_score = min(1.0, entity_score)

            deadline_score = 0.0
            if self._assign_deadline(sentence):
                deadline_score = 1.0

            confidence = min(
                1.0,
                round((directive_score * 0.55) + (entity_score * 0.25) + (deadline_score * 0.2), 2)
            )

            page = sentence_data.get("page")
            sentence_index = sentence_data.get("sentence_index")
            char_start = sentence_data.get("char_start")
            char_end = sentence_data.get("char_end")

            action_type = self._classify_action(sentence)

            task = self._generate_task(sentence)

            department = self._assign_department(
                sentence,
                entities
            )

            deadline = self._assign_deadline(
                sentence
            )

            priority = self._compute_priority(
                deadline,
                action_type,
                confidence
            )

            return {
                "action_type": action_type,
                "task": task,
                "department": department,
                "deadline": deadline,
                "priority": priority,
                "confidence": round(confidence, 2),
                "confidence_components": {
                    "overall": round(confidence, 2),
                    "directive_score": round(directive_score, 2),
                    "entity_score": round(entity_score, 2),
                    "deadline_score": round(deadline_score, 2),
                    "notes": "Heuristic confidence derived from directive, entity, and deadline signals",
                },

                "evidence": {
                    "text": sentence,
                    "page": page,
                    "sentence_index": sentence_index,
                    "char_start": char_start,
                    "char_end": char_end,
                },

                "created_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Action creation failed: {e}")
            return None

    # ---------------------------------------------------------
    # CLASSIFICATION
    # ---------------------------------------------------------

    def _classify_action(self, sentence: str) -> str:

        s = sentence.lower()

        if "appeal" in s:
            return "appeal"

        elif "review" in s or "reconsider" in s:
            return "review"

        elif "escalate" in s or "refer" in s:
            return "escalation"

        return "compliance"

    # ---------------------------------------------------------
    # SMART TASK GENERATION
    # ---------------------------------------------------------

    def _generate_task(self, sentence: str) -> str:

        s = sentence.lower()

        # Structure value
        if "determine the value" in s:
            return "Determine structure value"

        # Compensation
        elif "pay the same to the appellants" in s:
            return "Pay compensation to appellants"

        # Property possession
        elif "shall be delivered" in s:
            return "Deliver property possession"

        # Handover
        elif "handed over" in s:
            return "Hand over property"

        # Payment
        elif "shall pay" in s or "pay rs" in s or "cost" in s:
            return "Process court-ordered payment"

        # Service records
        elif "service records" in s:
            return "Update service records"

        # Payment release
        elif "release the pending payment" in s:
            return "Release pending payment"

        # Compensation
        elif "award compensation" in s:
            return "Award compensation"

        # Appeals
        elif "appeal" in s:
            return "Consider filing appeal"

        # Compliance reports
        elif "submit report" in s:
            return "Submit compliance report"

        # Possession
        elif "deliver possession" in s:
            return "Deliver possession"

        # Determine / decide
        elif "shall determine" in s:
            return "Determine court-directed issue"

        elif "shall decide" in s:
            return "Decide pending issue"

        return "Implement the ordered action"

    # ---------------------------------------------------------
    # DEPARTMENT
    # ---------------------------------------------------------

    def _assign_department(
        self,
        sentence: str,
        entities: Dict[str, List[str]]
    ) -> str:

        s = sentence.lower()

        organizations = entities.get("organizations", [])

        for org in organizations:

            org_lower = org.lower()

            for keyword, dept in self.DEPARTMENT_MAP.items():

                if keyword in org_lower:
                    return dept

        for keyword, dept in self.DEPARTMENT_MAP.items():

            if keyword in s:
                return dept

        return "Concerned Authority"

    # ---------------------------------------------------------
    # DEADLINE EXTRACTION
    # ---------------------------------------------------------

    def _assign_deadline(
        self,
        sentence: str
    ) -> Optional[str]:

        try:

            match = re.search(
                r'within\s+(\d+)\s+days?',
                sentence,
                re.IGNORECASE
            )

            if match:

                days = int(match.group(1))

                deadline = (
                    datetime.today() + timedelta(days=days)
                ).date().isoformat()

                return deadline

            return None

        except:
            return None

    # ---------------------------------------------------------
    # PRIORITY
    # ---------------------------------------------------------

    def _compute_priority(
        self,
        deadline: Optional[str],
        action_type: str,
        confidence: float
    ) -> str:

        score = self.PRIORITY_WEIGHTS.get(
            action_type,
            0.5
        )

        if deadline:

            try:

                deadline_date = datetime.fromisoformat(
                    deadline
                ).date()

                days_left = (
                    deadline_date - datetime.today().date()
                ).days

                if days_left <= 7:
                    score += 0.2

                elif days_left <= 30:
                    score += 0.1

            except:
                pass

        score *= confidence

        if score >= 0.75:
            return "High"

        elif score >= 0.45:
            return "Medium"

        return "Low"


# ---------------------------------------------------------
# GLOBAL INSTANCE
# ---------------------------------------------------------

action_engine = ActionEngine()


def get_action_engine() -> ActionEngine:
    return action_engine