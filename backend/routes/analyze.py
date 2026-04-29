from uuid import uuid4

from fastapi import APIRouter

from services.classifier import predict_category
from services.conversation_manager import (
    add_collected_info,
    get_session,
    get_next_question,
    init_session,
    reset_session,
    update_session,
)
from services.input_parser import extract_entities
from services.knowledge_base import get_legal_info
from services.location_service import resolve_locations
from services.response_generator import generate_response

router = APIRouter()

def _get_or_init_session(session_id: str):
    resolved_session_id = session_id or str(uuid4())
    session = get_session(resolved_session_id)
    if session is None:
        session = init_session(resolved_session_id)
    return resolved_session_id, session


def _normalize_text(text: str) -> str:
    return (text or "").strip()


def _capture_answer(field: str, text: str):
    value = text.strip()
    lower = value.lower()

    if field == "city":
        return value
    if field == "duration":
        for keyword in ("day", "days", "week", "weeks", "month", "months", "year", "years"):
            if keyword in lower:
                return value
        return value
    if field == "employer_name":
        return value
    if field in {"proof_available", "rent_agreement"}:
        if any(word in lower for word in ("yes", "have", "available", "got")):
            return "yes"
        if any(word in lower for word in ("no", "not", "none", "don't")):
            return "no"
        return value
    if field in {"issue_type", "product/service", "date_of_issue", "proof"}:
        return value
    return value


def _merge_extracted_entities(session_id: str, text: str):
    extracted = extract_entities(text)
    print(f"[entity_extraction] input={text!r} extracted={extracted}")
    if not extracted:
        return

    collected_info = get_session(session_id).get("collected_info", {})
    field_mapping = {
        "duration": ("duration",),
        "organization": ("organization", "employer_name"),
        "employer": ("employer_name", "organization"),
    }

    for source_field, target_fields in field_mapping.items():
        value = extracted.get(source_field)
        if not value:
            continue

        for target_field in target_fields:
            if not collected_info.get(target_field):
                add_collected_info(session_id, target_field, value)
                collected_info[target_field] = value


def _remember_question(session_id: str, question: str):
    session = get_session(session_id)
    questions_asked = list(session.get("questions_asked", []))
    questions_asked.append(question)
    update_session(session_id, "questions_asked", questions_asked)


def _build_combined_query(session: dict) -> str:
    collected_info = session.get("collected_info", {})
    parts = [
        collected_info.get("issue_text", ""),
        f"Duration: {collected_info.get('duration', '')}",
        f"Employer: {collected_info.get('employer_name', '') or collected_info.get('organization', '')}",
        f"Proof: {collected_info.get('proof', '') or collected_info.get('proof_available', '')}",
        f"Issue Type: {collected_info.get('issue_type', '')}",
        f"Rent Agreement: {collected_info.get('rent_agreement', '')}",
        f"Product or Service: {collected_info.get('product/service', '')}",
        f"Date of Issue: {collected_info.get('date_of_issue', '')}",
        f"City: {session.get('city', '')}",
    ]
    return " ".join(part.strip() for part in parts if part and part.strip()).strip()


def _resolve_category_and_subcategory(session: dict, query: str):
    category = session.get("category")
    subcategory = session.get("subcategory")

    if not category:
        classification = predict_category(query)
        category = classification.get("category")
        subcategory = classification.get("subcategory")

    if category == "unknown":
        classification = predict_category(query)
        category = classification.get("category", category)
        subcategory = classification.get("subcategory", subcategory)

    return category, subcategory


def _build_follow_up_response(session_id: str, session: dict, question: str):
    return {
        "ok": True,
        "follow_up": True,
        "session_id": session_id,
        "stage": session.get("stage"),
        "category": session.get("category"),
        "subcategory": session.get("subcategory"),
        "question": question,
        "response": question,
        "collected_info": session.get("collected_info", {}),
        "questions_asked": session.get("questions_asked", []),
    }


def _build_final_response(session_id: str, session: dict):
    combined_query = _build_combined_query(session)
    category, subcategory = _resolve_category_and_subcategory(session, combined_query)

    if category and category != session.get("category"):
        update_session(session_id, "category", category)
    if subcategory and subcategory != session.get("subcategory"):
        update_session(session_id, "subcategory", subcategory)

    legal_info = get_legal_info(category or "unknown", subcategory, combined_query)
    final_subcategory = legal_info.get("subcategory", subcategory or "unknown")
    if final_subcategory != session.get("subcategory"):
        update_session(session_id, "subcategory", final_subcategory)

    collected_info = session.get("collected_info", {})
    entities = extract_entities(collected_info.get("issue_text", combined_query))
    if collected_info.get("duration"):
        entities["duration"] = collected_info["duration"]
    if collected_info.get("organization") and not entities.get("organization"):
        entities["organization"] = collected_info["organization"]
    if collected_info.get("employer_name") and not entities.get("employer"):
        entities["employer"] = collected_info["employer_name"]
    if collected_info.get("issue_text") and not entities.get("issue_description"):
        entities["issue_description"] = collected_info["issue_text"]

    generated = generate_response(
        {
            "category": category or "unknown",
            "subcategory": final_subcategory,
            "entities": entities,
            "rights": legal_info.get("rights", []),
            "law": legal_info.get("law", []),
            "steps": legal_info.get("steps", []),
            "documents": legal_info.get("documents", []),
        }
    )

    response_payload = {
        "ok": True,
        "follow_up": False,
        "session_id": session_id,
        "stage": session.get("stage"),
        "category": category or "unknown",
        "subcategory": final_subcategory,
        "summary": generated.get("summary", ""),
        "rights": legal_info.get("rights", []),
        "steps": legal_info.get("steps", []),
        "documents": legal_info.get("documents", []),
        "next_actions": ["Generate Report", "View Locations"],
        "response": generated.get("response", ""),
        "rights": legal_info.get("rights", []),
        "law": legal_info.get("law", []),
        "steps": legal_info.get("steps", []),
        "documents": legal_info.get("documents", []),
        "collected_info": collected_info,
        "questions_asked": session.get("questions_asked", []),
    }

    if session.get("city"):
        location_result = resolve_locations(category or "unknown", session.get("city"))
        response_payload["locations"] = location_result.get("locations", [])
        if location_result.get("fallback_used") and location_result.get("matched_city"):
            response_payload["location_note"] = (
                f"No exact office match was found for {session.get('city')}. "
                f"Showing nearest major city offices from {location_result.get('matched_city')}."
            )

    return response_payload


def _build_report_payload(final_response: dict, session: dict):
    collected_info = session.get("collected_info", {})
    extracted_entities = extract_entities(collected_info.get("issue_text", ""))
    case_summary = {
        "organization": collected_info.get("organization") or collected_info.get("employer_name", ""),
        "duration": collected_info.get("duration", ""),
        "issue": extracted_entities.get("issue") or final_response.get("subcategory") or final_response.get("category") or "",
        "issue_description": collected_info.get("issue_text", ""),
    }

    return {
        "summary": final_response.get("summary", ""),
        "response": final_response.get("response", ""),
        "category": final_response.get("category", session.get("category")),
        "subcategory": final_response.get("subcategory", session.get("subcategory")),
        "rights": final_response.get("rights", []),
        "law": final_response.get("law", []),
        "actions": final_response.get("steps", []),
        "documents": final_response.get("documents", []),
        "locations": final_response.get("locations", []),
        "collected_info": collected_info,
        "case_summary": case_summary,
        "city": session.get("city"),
    }


@router.post("/analyze")
def analyze(data: dict):
    text = _normalize_text(data.get("text"))
    session_id, session = _get_or_init_session(data.get("session_id"))
    request_next_question = bool(data.get("request_next_question"))
    reset_after_completion = bool(data.get("reset_after_completion"))
    provided_city = _normalize_text(data.get("city"))

    if provided_city and not session.get("city"):
        update_session(session_id, "city", provided_city)
        session = get_session(session_id)

    if text:
        _merge_extracted_entities(session_id, text)
        session = get_session(session_id)

    if request_next_question:
        next_item = get_next_question(session)
        if next_item:
            update_session(session_id, "awaiting_field", next_item["field"])
            if next_item["question"] not in session.get("questions_asked", []):
                _remember_question(session_id, next_item["question"])
            session = get_session(session_id)
            return _build_follow_up_response(session_id, session, next_item["question"])
        return _build_final_response(session_id, session) if session.get("stage") == "ready" else {
            "ok": False,
            "session_id": session_id,
            "stage": session.get("stage"),
            "message": "No next question available.",
        }

    if not text and session.get("stage") != "ready":
        return {
            "ok": False,
            "error": "empty_input",
            "message": "Please describe your issue",
            "response": "Please describe your issue",
            "session_id": session_id,
            "stage": session.get("stage"),
            "rights": [],
            "law": [],
            "steps": [],
            "documents": [],
            "locations": [],
        }

    try:
        if session.get("stage") == "initial":
            classification = predict_category(text)
            legal_info = get_legal_info(
                classification.get("category", "unknown"),
                classification.get("subcategory"),
                text,
            )

            update_session(session_id, "category", classification.get("category"))
            update_session(session_id, "subcategory", legal_info.get("subcategory"))
            update_session(session_id, "stage", "collecting")
            if not session.get("collected_info", {}).get("issue_text"):
                add_collected_info(session_id, "issue_text", text)

            session = get_session(session_id)
            next_item = get_next_question(session)
            if not next_item:
                update_session(session_id, "stage", "ready")
                session = get_session(session_id)
                return _build_final_response(session_id, session)

            update_session(session_id, "awaiting_field", next_item["field"])
            _remember_question(session_id, next_item["question"])
            session = get_session(session_id)
            return _build_follow_up_response(session_id, session, next_item["question"])

        if session.get("stage") == "collecting":
            awaiting_field = session.get("awaiting_field")
            if awaiting_field:
                captured_value = _capture_answer(awaiting_field, text)
                if awaiting_field == "city":
                    if not session.get("city"):
                        update_session(session_id, "city", captured_value)
                        session = get_session(session_id)
                elif not session.get("collected_info", {}).get(awaiting_field):
                    add_collected_info(session_id, awaiting_field, captured_value)
                    session = get_session(session_id)

            session = get_session(session_id)
            next_item = get_next_question(session)
            if next_item:
                update_session(session_id, "awaiting_field", next_item["field"])
                _remember_question(session_id, next_item["question"])
                session = get_session(session_id)
                return _build_follow_up_response(session_id, session, next_item["question"])

            update_session(session_id, "awaiting_field", None)
            update_session(session_id, "stage", "ready")
            session = get_session(session_id)
            final_response = _build_final_response(session_id, session)
            if reset_after_completion:
                reset_session(session_id)
            return final_response

        session = get_session(session_id)
        final_response = _build_final_response(session_id, session)
        if reset_after_completion:
            reset_session(session_id)
        return final_response

    except Exception:
        return {
            "ok": False,
            "error": "server_error",
            "message": "Something went wrong while analyzing your issue.",
            "response": "Something went wrong while analyzing your issue.",
            "session_id": session_id,
            "stage": session.get("stage"),
            "rights": [],
            "law": [],
            "steps": [],
            "documents": [],
            "locations": [],
        }


@router.post("/generate-report")
def generate_report(data: dict):
    session_id = data.get("session_id")
    resolved_session_id, session = _get_or_init_session(session_id)

    try:
        if session.get("stage") != "ready":
            next_item = get_next_question(session)
            next_question = next_item["question"] if next_item else ""
            return {
                "ok": False,
                "follow_up": bool(next_question),
                "session_id": resolved_session_id,
                "stage": session.get("stage"),
                "question": next_question,
                "message": "The report is not ready yet. Please complete the conversation first.",
                "report": None,
            }

        final_response = _build_final_response(resolved_session_id, session)
        final_response["report"] = _build_report_payload(final_response, session)
        return final_response

    except Exception:
        return {
            "ok": False,
            "error": "server_error",
            "message": "Something went wrong while generating the legal report.",
            "response": "Something went wrong while generating the legal report.",
            "report": None,
        }
