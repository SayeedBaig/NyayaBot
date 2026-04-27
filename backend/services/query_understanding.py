"""
Query Understanding Module
Normalizes user input and handles common variations/typos.
"""

import re
from typing import Dict, List

# Common variations mapping
QUERY_VARIATIONS: Dict[str, List[str]] = {
    "salary not paid": [
        "salary not paid", "didn't get salary", "not getting salary",
        "salary pending", "wages not paid", "didn't receive salary",
        "salary delayed", "not paid salary", "salary due", "unpaid salary"
    ],
    "illegal eviction": [
        "evicting me", "forcing to vacate", "want to throw me out",
        "making me leave", "removing from house", "kicking me out"
    ],
    "deposit not returned": [
        "deposit not refunded", "security not returned", "advance not given back",
        "landlord not returning deposit", "refusing to return deposit"
    ],
    "defective product": [
        "product not working", "item defective", "bought item is broken",
        "product stopped working", "item damaged", "goods faulty"
    ],
    "refund not given": [
        "refund not processing", "money not refunded", "not giving refund",
        "refund rejected", "cancellation refund", "return not accepted"
    ],
    "wrongful termination": [
        "fired from job", "job terminated", "removed from position",
        "dismissed from work", "let go", "lost my job"
    ],
    "overtime nonpayment": [
        "overtime not paid", "extra hours not compensated", "working extra no pay",
        "late night hours", "overtime wages due"
    ],
    "landlord harassment": [
        "landlord misbehaving", "owner harassing", "landlord threats",
        "cutting water electricity", "entering without permission"
    ],
}

# Build reverse mapping for quick lookup
_VARIATION_TO_CANONICAL = {}
for canonical, variations in QUERY_VARIATIONS.items():
    for variation in variations:
        _VARIATION_TO_CANONICAL[variation] = canonical


def normalize_query(text: str) -> str:
    """
    Normalize user query by removing noise and standardizing format.

    Args:
        text: Raw user input

    Returns:
        Normalized text
    """
    if not text:
        return ""

    # Convert to lowercase
    text = text.lower()

    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Remove common filler words and noise
    noise_words = [
        "please", "kindly", "i want to", "i need to", "can i",
        "could you", "help me", "regarding", "about"
    ]
    for word in noise_words:
        text = re.sub(rf"\b{re.escape(word)}\b", "", text)

    # Clean up punctuation
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def find_variation_matches(text: str) -> List[str]:
    """
    Find canonical issue types that match user text variations.

    Args:
        text: Normalized user text

    Returns:
        List of matching canonical issue types
    """
    text = text.lower()
    matches = []

    for canonical, variations in QUERY_VARIATIONS.items():
        for variation in variations:
            if variation in text or text in variation:
                if canonical not in matches:
                    matches.append(canonical)
                break

    return matches


def expand_query(text: str) -> List[str]:
    """
    Expand query with variations for better matching.

    Args:
        text: Normalized user text

    Returns:
        List of query variations to try
    """
    queries = [text]

    # Add variations
    matches = find_variation_matches(text)
    for match in matches:
        queries.append(match)

    return queries


def extract_key_phrases(text: str) -> List[str]:
    """
    Extract important key phrases from the query.

    Args:
        text: Normalized user text

    Returns:
        List of key phrases
    """
    text = text.lower()

    # Important legal terms to look for
    key_terms = [
        "salary", "wages", "payment", "termination", "fired", "eviction",
        "deposit", "refund", "defect", "warranty", "harassment", "rent",
        "overtime", "pf", "esi", "landlord", "tenant", "consumer"
    ]

    found = [term for term in key_terms if term in text]
    return found


def understand_query(text: str) -> dict:
    """
    Full query understanding - normalize, find variations, extract key phrases.

    Args:
        text: Raw user input

    Returns:
        Dict with normalized text, key phrases, and variation matches
    """
    normalized = normalize_query(text)
    key_phrases = extract_key_phrases(normalized)
    variation_matches = find_variation_matches(normalized)
    expanded = expand_query(normalized)

    return {
        "original": text,
        "normalized": normalized,
        "key_phrases": key_phrases,
        "variation_matches": variation_matches,
        "expanded_queries": expanded,
    }