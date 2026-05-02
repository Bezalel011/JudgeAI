import re
from datetime import datetime, timedelta

def extract_days(sentence):
    match = re.search(r'within\s+(\d+)\s+days', sentence.lower())
    return int(match.group(1)) if match else None

def compute_deadline(days):
    if not days:
        return None
    return (datetime.today() + timedelta(days=days)).date().isoformat()

def detect_actions(sentences):
    actions = []

    for s in sentences:
        s_lower = s.lower()
        days = extract_days(s)
        deadline = compute_deadline(days)

        # COMPLIANCE
        if any(k in s_lower for k in ["shall", "must", "directed to"]):
            actions.append({
                "type": "COMPLIANCE",
                "task": s,
                "deadline": deadline,
                "confidence": 0.9,
                "evidence": s
            })

        # APPEAL
        if "appeal" in s_lower and any(k in s_lower for k in ["may", "liberty"]):
            actions.append({
                "type": "APPEAL",
                "task": "Consider filing appeal",
                "deadline": deadline,
                "confidence": 0.8,
                "evidence": s
            })

    return actions