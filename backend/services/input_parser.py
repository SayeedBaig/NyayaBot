import re

ISSUE_KEYWORDS = {
    "unpaid salary": ["unpaid salary", "not paid salary", "salary", "wages", "payment delayed"],
    "wrongful termination": ["fired", "terminated", "removed", "dismissed"],
    "overtime nonpayment": ["overtime", "extra hours", "late night"],
    "illegal eviction": ["evict", "vacate", "forcing me to vacate", "force me to leave", "throw out"],
    "deposit not returned": ["deposit", "security amount", "advance"],
    "landlord harassment": ["harass", "threat", "water", "electricity", "lock"],
    "defective product": ["defective", "broken", "damaged", "not working", "faulty"],
    "refund not given": ["refund", "money back", "cancelled"],
    "service deficiency": ["bad service", "poor service", "service not provided"],
}


def _extract_duration(text):
    match = re.search(
        r"\b(\d+\s*(?:day|days|week|weeks|month|months|year|years))\b",
        text,
        flags=re.IGNORECASE,
    )
    return match.group(1) if match else None


def _extract_employer(text):
    patterns = [
        r"\bemployer\s+([A-Z][A-Za-z0-9&.\s]{1,40}?\s+company)\b",
        r"\b([A-Z][A-Za-z0-9&.\s]{1,40}?\s+company)\b",
        r"\bemployer\s+([A-Z][A-Za-z0-9&.\s]{1,40}?)(?:\s+(?:did|has|have|is|was|for|not)\b|$)",
        r"\bcompany\s+([A-Z][A-Za-z0-9&.\s]{1,40}?)(?:\s+(?:did|has|have|is|was|for|not)\b|$)",
        r"\b([A-Z][A-Za-z0-9&.]+(?:\s+[A-Z][A-Za-z0-9&.]+){0,3})\s+company\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            value = match.group(1).strip(" .")
            if value.lower() not in {"my", "the"}:
                return value
    return None


def _extract_opposite_party(text):
    lower = text.lower()
    if "landlord" in lower or "owner" in lower:
        return "landlord"
    if "seller" in lower:
        return "seller"
    if "amazon" in lower:
        return "Amazon"
    if "flipkart" in lower:
        return "Flipkart"
    employer = _extract_employer(text)
    if employer:
        return employer
    return None


def _extract_issue(text):
    text_lower = text.lower()
    for issue, keywords in ISSUE_KEYWORDS.items():
        if any(keyword in text_lower for keyword in keywords):
            return issue
    return None


def extract_entities(text):
    clean_text = re.sub(r"\s+", " ", text or "").strip()
    employer = _extract_employer(clean_text)
    opposite_party = _extract_opposite_party(clean_text)
    duration = _extract_duration(clean_text)
    issue = _extract_issue(clean_text)

    return {
        "employer": employer,
        "organization": employer,
        "opposite_party": opposite_party,
        "duration": duration,
        "issue": issue,
        "issue_description": issue.replace("_", " ") if issue else None,
        "issue_keywords": [
            issue for issue, keywords in ISSUE_KEYWORDS.items()
            if any(keyword in clean_text.lower() for keyword in keywords)
        ],
    }
