"""
LLM Service Module
Uses OpenAI API to turn retrieved legal context into practical guidance.
IMPORTANT: LLM only uses facts already available in the pipeline context.
"""

import os
import re
from typing import Optional

# Load .env file FIRST before reading any environment variables
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, ".env"))
except ImportError:
    pass

# Try to import openai, but handle gracefully if not available
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Configure OpenAI - supports both API key and Azure OpenAI
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_ENDPOINT = os.environ.get("OPENAI_ENDPOINT", "")
OPENAI_DEPLOYMENT = os.environ.get("OPENAI_DEPLOYMENT", "gpt-35-turbo")
OPENAI_API_VERSION = os.environ.get("OPENAI_API_VERSION", "2023-05-15")

# Initialize OpenAI client if API key is available
_client = None


def _get_client():
    """Get or initialize OpenAI client."""
    global _client

    if _client is not None:
        return _client

    if not OPENAI_AVAILABLE:
        return None

    if OPENAI_ENDPOINT:
        # Azure OpenAI
        openai.api_type = "azure"
        openai.api_base = OPENAI_ENDPOINT
        openai.api_version = OPENAI_API_VERSION
        openai.api_key = OPENAI_API_KEY
    elif OPENAI_API_KEY:
        openai.api_key = OPENAI_API_KEY

    _client = openai
    return _client


SYSTEM_PROMPT = "You are a legal assistant."

USER_PROMPT_TEMPLATE = """Rewrite the given legal guidance clearly and professionally.

Rules:
- Use simple English
- Fix grammar mistakes
- Keep sentences short and clear
- Do NOT add new legal facts
- Do NOT change meaning
- Make it sound confident and helpful

Format:
- First 1-2 lines: summary
- Then clear explanation

Input:
{response}

Output only improved text."""


def _cleanup_refined_text(text: str) -> str:
    cleaned = (text or "").strip()
    if not cleaned:
        return cleaned

    cleaned = cleaned.replace("start by keep", "start by keeping")
    cleaned = re.sub(r"\b(\w+)(\s+\1\b)+", r"\1", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned[0].upper() + cleaned[1:] if cleaned else cleaned
    return cleaned


def refine_response(
    summary: str,
    category: str,
    subcategory: str,
    rights: list,
    steps: list,
    user_query: str,
    entities: Optional[dict] = None,
) -> dict:
    """
    Refine legal response using LLM for better readability.

    Args:
        summary: Generated summary
        category: Predicted legal category
        subcategory: Predicted legal subcategory
        rights: List of legal rights
        steps: List of action steps
        user_query: Original user query
        entities: Extracted entities for personalization

    Returns:
        Dict with refined response components
    """
    client = _get_client()

    def _fallback_response():
        lines = [summary]
        if rights:
            lines.append(f"Your key right is: {rights[0]}")
        if steps:
            lines.append(f"Next step: {steps[0]}")
        if len(steps) > 1:
            lines.append(f"After that: {steps[1]}")
        if len(lines) < 4 and len(rights) > 1:
            lines.append(f"Also keep in mind: {rights[1]}")
        return "\n".join(lines[:6]).strip()

    if not client or not OPENAI_API_KEY:
        # Fallback: return original response
        return {
            "refined": False,
            "summary": summary,
            "response": _cleanup_refined_text(_fallback_response()),
        }

    try:
        prompt = USER_PROMPT_TEMPLATE.format(
            response=_fallback_response(),
        )

        if OPENAI_ENDPOINT:
            response = client.ChatCompletion.create(
                engine=OPENAI_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=300,
            )
            refined_text = _cleanup_refined_text(response.choices[0].message.content.strip())
        else:
            response = client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=300,
            )
            refined_text = _cleanup_refined_text(response.choices[0].message.content.strip())

        return {
            "refined": True,
            "summary": summary,
            "response": refined_text,
        }

    except Exception as e:
        # Fallback on any error
        return {
            "refined": False,
            "summary": summary,
            "response": _cleanup_refined_text(_fallback_response()),
        }


def is_llm_available() -> bool:
    """Check if LLM service is available."""
    return OPENAI_AVAILABLE and bool(OPENAI_API_KEY)
