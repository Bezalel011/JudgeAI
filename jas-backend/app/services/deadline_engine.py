"""
Deadline Engine - Reference date extraction, deadline normalization, and urgency scoring.
"""

from __future__ import annotations

import re
from datetime import datetime, date, timedelta, time
from typing import Any, Dict, Optional


class DeadlineEngine:
    @staticmethod
    def parse_reference_date(full_text: str, entities: Dict[str, Any]) -> Optional[date]:
        date_candidates = []

        for raw in entities.get("dates", []) or []:
            if isinstance(raw, dict):
                raw = raw.get("normalized") or raw.get("original")
            if not raw:
                continue
            parsed = DeadlineEngine._parse_date_value(str(raw))
            if parsed:
                date_candidates.append(parsed)

        if date_candidates:
            return sorted(date_candidates)[0]

        patterns = [
            r"\b(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})\b",
            r"\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b",
        ]

        for pattern in patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                parsed = DeadlineEngine._parse_date_value(match.group(1))
                if parsed:
                    return parsed

        return None

    @staticmethod
    def normalize_deadline(expression: str, reference_date: Optional[date]) -> Optional[str]:
        if not expression:
            return None

        match = re.search(r"within\s+(\d+)\s+days?", expression, re.IGNORECASE)
        if match:
            days = int(match.group(1))
            base = reference_date or datetime.utcnow().date()
            return (base + timedelta(days=days)).isoformat()

        parsed = DeadlineEngine._parse_date_value(expression)
        if parsed:
            return parsed.isoformat()

        return None

    @staticmethod
    def compute_urgency(deadline_iso: Optional[str]) -> str:
        if not deadline_iso:
            return "low"

        try:
            deadline_date = datetime.fromisoformat(deadline_iso).date()
        except ValueError:
            try:
                deadline_date = date.fromisoformat(deadline_iso)
            except ValueError:
                return "low"

        delta_days = (deadline_date - datetime.utcnow().date()).days
        if delta_days <= 3:
            return "critical"
        if delta_days <= 7:
            return "high"
        if delta_days <= 30:
            return "medium"
        return "low"

    @staticmethod
    def _parse_date_value(value: str) -> Optional[date]:
        value = value.strip()

        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d %B %Y", "%d %b %Y", "%B %d %Y", "%b %d %Y"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue

        try:
            from dateparser import parse

            parsed = parse(value)
            if parsed:
                return parsed.date()
        except Exception:
            return None

        return None


deadline_engine = DeadlineEngine()