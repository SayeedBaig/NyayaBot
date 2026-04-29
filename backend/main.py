import os
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.analyze import router as analyze_router
from routes.document import router as document_router
from routes.locations import router as locations_router

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

# Configure OpenAI - supports both API key and Azure OpenAI
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_ENDPOINT = os.environ.get("OPENAI_ENDPOINT", "")
OPENAI_DEPLOYMENT = os.environ.get("OPENAI_DEPLOYMENT", "gpt-35-turbo")
OPENAI_API_VERSION = os.environ.get("OPENAI_API_VERSION", "2023-05-15")

app = FastAPI(title="NyayaBot API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:5173",
        "http://127.0.0.1",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(analyze_router)
app.include_router(document_router)
app.include_router(locations_router)

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


REFINE_PROMPT = """You are a legal guidance assistant for Indian users. Your job is to explain legal rights and steps clearly and practically. Use simple language. Do not give vague answers. If user input is short, still try to give best possible guidance. Do NOT say 'need more details' unless absolutely necessary. Be helpful and action-oriented."""


def refine_response(
    summary: str,
    rights: list,
    steps: list,
    user_query: str,
    entities: Optional[dict] = None,
) -> dict:
    """
    Refine legal response using LLM for better readability.

    Args:
        summary: Generated summary
        rights: List of legal rights
        steps: List of action steps
        user_query: Original user query
        entities: Extracted entities for personalization

    Returns:
        Dict with refined response components
    """
    client = _get_client()

    if not client or not OPENAI_API_KEY:
        # Fallback: return original response
        return {
            "refined": False,
            "summary": summary,
            "response": f"{summary} {' '.join(rights[:1])}",
        }

    try:
        rights_text = "\n".join(f"- {r}" for r in rights[:2])
        steps_text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps[:2]))

        # Add personalization if available
        personalization = ""
        if entities:
            employer = entities.get("employer")
            opposite_party = entities.get("opposite_party")
            if employer:
                personalization = f"\nContext: Your issue is with {employer}."
            elif opposite_party:
                personalization = f"\nContext: Your issue is with {opposite_party}."

        # Update prompt used for LLM
        prompt = REFINE_PROMPT + user_query + personalization

        if OPENAI_ENDPOINT:
            response = client.ChatCompletion.create(
                engine=OPENAI_DEPLOYMENT,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300,
            )
            refined_text = response.choices[0].message.content.strip()
        else:
            response = client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300,
            )
            refined_text = response.choices[0].message.content.strip()

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
            "response": f"{summary} {' '.join(rights[:1])}",
        }


def is_llm_available() -> bool:
    """Check if LLM service is available."""
    return OPENAI_AVAILABLE and bool(OPENAI_API_KEY)
