import re


def _extract_duration(text: str):
    match = re.search(
        r"\b(\d+\s*(?:day|days|week|weeks|month|months|year|years))\b",
        text or "",
        flags=re.IGNORECASE,
    )
    return match.group(1) if match else None


def _extract_organization(text: str):
    patterns = [
        r"\bcompany\s+([A-Za-z0-9&.\- ]{2,50})",
        r"\bemployer\s+([A-Za-z0-9&.\- ]{2,50})",
        r"\bfrom\s+([A-Za-z0-9&.\- ]{2,50})",
    ]

    stop_words = {
        "for", "since", "about", "because", "regarding", "did", "has", "have",
        "is", "was", "not", "on", "in", "with", "my", "the",
    }

    for pattern in patterns:
        match = re.search(pattern, text or "", flags=re.IGNORECASE)
        if not match:
            continue

        value = re.split(
            r"\b(?:for|since|about|because|regarding|did|has|have|is|was|not|on|in|with)\b",
            match.group(1),
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0].strip(" .,-")

        if value and value.lower() not in stop_words:
            return value

    return None


def _extract_issue(text: str):
    lowered = (text or "").lower()
    if "salary" in lowered:
        return "unpaid_salary"
    if "rent" in lowered:
        return "tenant_issue"
    if "refund" in lowered:
        return "consumer_issue"
    return None


def extract_entities(text: str):
    clean_text = re.sub(r"\s+", " ", text or "").strip()
    return {
        "duration": _extract_duration(clean_text),
        "organization": _extract_organization(clean_text),
        "issue": _extract_issue(clean_text),
    }
