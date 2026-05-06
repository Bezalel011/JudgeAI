import re
from datetime import datetime, timedelta

# ✅ Strong directive keywords only
DIRECTIVE_KEYWORDS = [
    "is hereby directed to",
    "shall release payment",
    "shall pay",
    "is ordered to",
    "shall comply with this order",
    "file an appeal",
    "consider filing appeal",
    "reinstate the employee",
    "submit compliance report",
]

# ✅ Ignore legal reasoning / observations
IGNORE_PHRASES = [
    "we are compelled",
    "we conclude",
    "it is observed",
    "it appears",
    "the evidence shows",
    "learned counsel",
    "aggravating circumstances",
    "mitigating circumstances",
    "we appreciate",
    "it is argued",
    "contention",
    "it is submitted",
    "the prosecution",
    "the accused",
    "the appellant contended",
    "the respondent contended",
    "this court observed",
    "the witness stated",
    "it cannot be said",
]


# ✅ Extract days from sentence
def extract_days(sentence):

    match = re.search(r'within\s+(\d+)\s+days', sentence.lower())

    if match:
        return int(match.group(1))

    return None


# ✅ Convert deadline to date
def compute_deadline(days):

    if not days:
        return None

    return (datetime.today() + timedelta(days=days)).date().isoformat()


# ✅ Determine whether sentence is actionable
def is_actionable(sentence):

    s = sentence.lower()

    # ❌ Ignore very long sentences (usually reasoning)
    if len(s.split()) > 40:
        return False

    # ❌ Ignore reasoning phrases
    for phrase in IGNORE_PHRASES:
        if phrase in s:
            return False

    # ✅ Detect strong directives only
    for keyword in DIRECTIVE_KEYWORDS:
        if keyword in s:
            return True

    return False


# ✅ Generate meaningful task names
def generate_task(sentence):

    s = sentence.lower()

    if "release" in s and "payment" in s:
        return "Release pending payment"

    elif "appeal" in s:
        return "Consider filing appeal"

    elif "reinstate" in s:
        return "Reinstate employee/service"

    elif "submit" in s:
        return "Submit compliance report"

    elif "pay" in s:
        return "Process court-ordered payment"

    elif "comply" in s:
        return "Ensure compliance with court order"

    else:
        return "Review court directive"


# ✅ Main action detection function
def detect_actions(sentences):

    actions = []

    for s in sentences:

        # Skip non-actionable sentences
        if not is_actionable(s):
            continue

        s_lower = s.lower()

        days = extract_days(s)
        deadline = compute_deadline(days)

        # Default type
        action_type = "COMPLIANCE"

        # Appeal detection
        if "appeal" in s_lower:
            action_type = "APPEAL"

        action = {
            "type": action_type,
            "task": generate_task(s),
            "deadline": deadline,
            "confidence": 0.9 if action_type == "COMPLIANCE" else 0.8,
            "evidence": s
        }

        actions.append(action)

    return actions