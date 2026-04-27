from fastapi import APIRouter

from services.placeholder_service import process_user_input

router = APIRouter()


@router.post("/analyze")
def analyze(data: dict):
    text = (data.get("text") or "").strip()
    city = data.get("city", "Bengaluru")

    if not text:
        return {
            "ok": False,
            "error": "empty_input",
            "message": "Please describe your issue",
            "response": "Please describe your issue",
            "rights": [],
            "law": [],
            "steps": [],
            "documents": [],
            "locations": [],
        }

    try:
        return process_user_input(text, city)
    except Exception:
        return {
            "ok": False,
            "error": "server_error",
            "message": "Something went wrong while analyzing your issue.",
            "response": "Something went wrong while analyzing your issue.",
            "rights": [],
            "law": [],
            "steps": [],
            "documents": [],
            "locations": [],
        }
