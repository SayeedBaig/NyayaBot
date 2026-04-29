from services.classifier import predict_category
from services.conversation_state import get_or_create_session, public_session_state
from services.input_parser import extract_entities
from services.knowledge_base import get_legal_info
from services.llm_service import refine_response, is_llm_available
from services.location_service import resolve_locations
from services.query_understanding import understand_query
from services.response_generator import generate_response
from services.translator import (
    detect_language,
    translate_to_english,
    translate_to_target,
)


LOW_CONFIDENCE_THRESHOLD = 0.6
DETAIL_STEPS = [
    ("duration", "How long has this been happening?"),
    ("proof", "Do you have any proof?"),
    ("city", "Please tell me your city to find nearest legal office"),
]


def _translate_list(items, target_lang):
    if target_lang == "en":
        return items
    return [translate_to_target(item, target_lang) for item in items]


def _calculate_combined_confidence(classifier_confidence: float, retrieval_similarity: float) -> float:
    if retrieval_similarity > 0:
        combined = (classifier_confidence * 0.6) + (retrieval_similarity * 0.4)
        return min(0.99, combined)
    return classifier_confidence


def _enhance_personalization(response: str, entities: dict) -> str:
    if not entities:
        return response

    employer = entities.get("employer")
    opposite_party = entities.get("opposite_party")

    if employer and "with " + employer.lower() not in response.lower():
        response = f"Based on your issue with {employer}, {response}"
    elif opposite_party and "with " + opposite_party.lower() not in response.lower():
        response = f"Based on your issue with {opposite_party}, {response}"

    return response


def _build_useful_fallback_response(summary: str, rights: list, steps: list) -> str:
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


def _get_missing_detail(session: dict):
    collected_keys = {item.get("key") for item in session.get("details_collected", [])}
    for key, question in DETAIL_STEPS:
        if key not in collected_keys:
            return key, question
    return None, None


def _build_follow_up_response(session_id: str, session: dict, question: str, message: str):
    return {
        "ok": False,
        "follow_up": True,
        "session_id": session_id,
        "stage": session["stage"],
        "session_state": public_session_state(session),
        "question": question,
        "message": message,
        "response": message,
        "report": None,
        "rights": [],
        "law": [],
        "steps": [],
        "documents": [],
        "locations": [],
    }


def _get_confidence_follow_up_question(category: str, entities: dict, text: str) -> str:
    text_lower = (text or "").lower()

    if category == "consumer":
        if "refund" in text_lower:
            return "Can you clarify if this is about a product return, a cancelled order, or a service payment?"
        return "Can you clarify if this is related to a product or a service?"

    if category == "tenant":
        if "vacate" in text_lower or "evict" in text_lower:
            return "Can you clarify whether the landlord asked you to vacate, cut services, or is holding your deposit?"
        return "Can you clarify if this is about rent, eviction, deposit, or landlord harassment?"

    if category == "labour":
        if entities.get("employer"):
            return "Can you clarify whether this is about salary, termination, overtime, or PF and ESI?"
        return "Can you clarify if this is about salary, termination, overtime, or PF and ESI?"

    return "Can you share one more detail about what happened so I can guide you better?"


def _build_ready_fallback(session_id: str, session: dict, city: str, confidence: float):
    response = (
        "The issue is still somewhat unclear, but you should keep your proof together, note the timeline clearly, "
        "and speak to the opposite party in writing before escalating further. "
        "If you have any further question, ask it now, or generate the legal report."
    )
    return {
        "ok": True,
        "follow_up": False,
        "session_id": session_id,
        "stage": session["stage"],
        "session_state": public_session_state(session),
        "category": session.get("category", "unknown"),
        "subcategory": session.get("subcategory", "unknown"),
        "confidence": round(confidence, 2),
        "summary": "The issue is still somewhat unclear, but the collected details suggest a legal problem that may need local help.",
        "response": response,
        "rights": [],
        "law": [],
        "steps": [
            "Write down the full timeline of what happened.",
            "Keep messages, receipts, notices, photos, or other proof ready.",
            f"Check the correct office in {city or 'the nearest major city'} before filing a complaint.",
        ],
        "documents": [],
        "locations": [],
        "report_ready": True,
        "report": None,
    }


def _build_combined_query(session: dict) -> str:
    parts = [session.get("initial_query", "").strip()]
    for item in session.get("details_collected", []):
        question = item.get("question", "").strip()
        answer = item.get("answer", "").strip()
        if answer:
            parts.append(f"{question} {answer}".strip())
    return " ".join(part for part in parts if part).strip()


def _build_report_payload(session: dict, analyzed: dict):
    return {
        "category": analyzed.get("category", session.get("category", "unknown")),
        "subcategory": analyzed.get("subcategory", session.get("subcategory", "unknown")),
        "summary": analyzed.get("summary", ""),
        "response": analyzed.get("response", ""),
        "rights": analyzed.get("rights", []),
        "law": analyzed.get("law", []),
        "steps": analyzed.get("steps", []),
        "documents": analyzed.get("documents", []),
        "locations": analyzed.get("locations", []),
        "details_collected": session.get("details_collected", []),
        "city": session.get("city", ""),
    }


def _analyze_ready_text(text: str, city: str, preferred_category: str = "unknown", preferred_subcategory: str = "unknown"):
    query_understanding = understand_query(text)
    detected_lang = detect_language(text)
    text_en = translate_to_english(text) if detected_lang != "en" else text

    classification = predict_category(text_en)
    classifier_confidence = classification.get("confidence", 0)

    category = classification.get("category", "unknown")
    subcategory = classification.get("subcategory", "unknown")

    if category == "unknown" and preferred_category != "unknown":
        category = preferred_category
        subcategory = preferred_subcategory or "general"
        classifier_confidence = max(classifier_confidence, LOW_CONFIDENCE_THRESHOLD)

    if category == "unknown":
        return None

    entities = extract_entities(text_en)
    legal_info = get_legal_info(category, subcategory, text_en)
    retrieval_similarity = legal_info.get("similarity", 0.0)
    confidence = _calculate_combined_confidence(classifier_confidence, retrieval_similarity)

    if confidence < LOW_CONFIDENCE_THRESHOLD:
        follow_up_question = _get_confidence_follow_up_question(category, entities, text_en)
        if detected_lang != "en":
            follow_up_question = translate_to_target(follow_up_question, detected_lang)
        return {
            "ok": False,
            "follow_up": True,
            "category": category,
            "subcategory": legal_info["subcategory"],
            "confidence": round(confidence, 2),
            "entities": entities,
            "summary": "",
            "response": follow_up_question,
            "question": follow_up_question,
            "rights": [],
            "law": [],
            "steps": [],
            "documents": [],
            "language": detected_lang,
            "locations": [],
            "location_note": "",
            "matched_city": city,
            "query_understanding": query_understanding,
            "report_ready": False,
            "report": None,
        }

    combined_data = {
        "category": category,
        "subcategory": legal_info["subcategory"],
        "confidence": confidence,
        "entities": entities,
        "rights": legal_info["rights"],
        "law": legal_info["law"],
        "steps": legal_info["steps"],
        "documents": legal_info["documents"],
    }

    generated = generate_response(combined_data)
    summary_text = generated["summary"]

    rights = legal_info["rights"]
    law = legal_info["law"]
    steps = legal_info["steps"]
    documents = legal_info["documents"]

    if is_llm_available():
        refined = refine_response(
            summary=summary_text,
            category=category,
            subcategory=legal_info["subcategory"],
            rights=rights,
            steps=steps,
            user_query=text_en,
            entities=entities,
        )
        response_text = refined.get("response") or _build_useful_fallback_response(summary_text, rights, steps)
        response_text = _enhance_personalization(response_text, entities)
    else:
        response_text = _build_useful_fallback_response(summary_text, rights, steps)
        response_text = _enhance_personalization(response_text, entities)

    location_result = resolve_locations(category, city)
    locations = location_result.get("locations", [])
    matched_city = location_result.get("matched_city", city)
    fallback_used = location_result.get("fallback_used", False)
    location_note = ""
    if fallback_used and matched_city:
        location_note = f"No exact office match was found for {city}. Showing nearest major city offices from {matched_city}."

    if detected_lang != "en":
        response_text = translate_to_target(response_text, detected_lang)
        summary_text = translate_to_target(summary_text, detected_lang)
        rights = _translate_list(rights, detected_lang)
        law = _translate_list(law, detected_lang)
        steps = _translate_list(steps, detected_lang)
        documents = _translate_list(documents, detected_lang)
        if location_note:
            location_note = translate_to_target(location_note, detected_lang)

    return {
        "ok": True,
        "follow_up": False,
        "category": category,
        "subcategory": legal_info["subcategory"],
        "confidence": round(confidence, 2),
        "entities": entities,
        "summary": summary_text,
        "response": f"{response_text}\n\nIf you have any further question, ask it now, or generate the legal report.",
        "rights": rights,
        "law": law,
        "steps": steps,
        "documents": documents,
        "language": detected_lang,
        "locations": locations,
        "location_note": location_note,
        "matched_city": matched_city,
        "query_understanding": query_understanding,
        "report_ready": True,
        "report": None,
    }


def get_next_question(session_id: str = None):
    resolved_session_id, session = get_or_create_session(session_id)
    detail_key, question = _get_missing_detail(session)

    if session.get("stage") == "ready" or not question:
        return {
            "ok": True,
            "follow_up": False,
            "session_id": resolved_session_id,
            "stage": session["stage"],
            "session_state": public_session_state(session),
            "question": "",
            "message": "I already have enough details to prepare the legal guidance.",
        }

    return _build_follow_up_response(
        resolved_session_id,
        session,
        question,
        question,
    )


def generate_session_report(session_id: str = None, city: str = ""):
    resolved_session_id, session = get_or_create_session(session_id)
    if session.get("stage") != "ready":
        detail_key, question = _get_missing_detail(session)
        return {
            "ok": False,
            "follow_up": bool(question),
            "session_id": resolved_session_id,
            "stage": session["stage"],
            "session_state": public_session_state(session),
            "question": question or "",
            "message": "The report is not ready yet. Please complete the missing details first.",
            "report": None,
        }

    effective_city = session.get("city") or city
    analyzed = _analyze_ready_text(
        _build_combined_query(session),
        effective_city,
        session.get("category", "unknown"),
        session.get("subcategory", "unknown"),
    )

    if not analyzed:
        fallback = _build_ready_fallback(resolved_session_id, session, effective_city, 0.0)
        fallback["report"] = {
            "summary": fallback["summary"],
            "response": fallback["response"],
            "steps": fallback["steps"],
            "details_collected": session.get("details_collected", []),
            "city": effective_city,
        }
        return fallback

    analyzed["session_id"] = resolved_session_id
    analyzed["stage"] = session["stage"]
    analyzed["session_state"] = public_session_state(session)
    analyzed["report"] = _build_report_payload(session, analyzed)
    return analyzed


def process_user_input(text: str, city: str = "", session_id: str = None):
    resolved_session_id, session = get_or_create_session(session_id)
    clean_text = (text or "").strip()

    if not clean_text:
        return {
            "ok": False,
            "follow_up": False,
            "session_id": resolved_session_id,
            "stage": session["stage"],
            "session_state": public_session_state(session),
            "error": "empty_input",
            "message": "Please describe your issue",
        }

    if not any(char.isalpha() for char in clean_text):
        return {
            "ok": False,
            "follow_up": False,
            "session_id": resolved_session_id,
            "stage": session["stage"],
            "session_state": public_session_state(session),
            "error": "invalid_text",
            "message": "Please describe your issue in words",
        }

    if session["stage"] == "initial":
        detected_lang = detect_language(clean_text)
        text_en = translate_to_english(clean_text) if detected_lang != "en" else clean_text
        classification = predict_category(text_en)

        session["initial_query"] = clean_text
        session["language"] = detected_lang
        session["category"] = classification.get("category", "unknown")
        session["subcategory"] = classification.get("subcategory", "unknown")
        session["details_collected"] = []
        session["city"] = city.strip()
        session["stage"] = "collecting"

        detail_key, first_question = _get_missing_detail(session)
        category_label = session["category"] if session["category"] != "unknown" else "legal"
        message = f"This looks like a {category_label} issue so far. {first_question}"
        return _build_follow_up_response(resolved_session_id, session, first_question, message)

    if session["stage"] == "collecting":
        detail_key, current_question = _get_missing_detail(session)
        if detail_key:
            session["details_collected"].append({
                "key": detail_key,
                "question": current_question,
                "answer": clean_text,
            })
            if detail_key == "city":
                session["city"] = clean_text.strip()

        next_key, next_question = _get_missing_detail(session)
        if next_question:
            return _build_follow_up_response(
                resolved_session_id,
                session,
                next_question,
                next_question,
            )

        session["stage"] = "ready"
        effective_city = session.get("city") or city
        final_result = _analyze_ready_text(
            _build_combined_query(session),
            effective_city,
            session.get("category", "unknown"),
            session.get("subcategory", "unknown"),
        )

        if not final_result:
            fallback = _build_ready_fallback(resolved_session_id, session, effective_city, 0.0)
            fallback["session_id"] = resolved_session_id
            fallback["session_state"] = public_session_state(session)
            fallback["stage"] = session["stage"]
            return fallback

        final_result["session_id"] = resolved_session_id
        final_result["session_state"] = public_session_state(session)
        final_result["stage"] = session["stage"]
        return final_result

    effective_city = session.get("city") or city
    final_result = _analyze_ready_text(
        _build_combined_query(session) or clean_text,
        effective_city,
        session.get("category", "unknown"),
        session.get("subcategory", "unknown"),
    )

    if not final_result:
        fallback = _build_ready_fallback(resolved_session_id, session, effective_city, 0.0)
        fallback["session_id"] = resolved_session_id
        fallback["session_state"] = public_session_state(session)
        fallback["stage"] = session["stage"]
        return fallback

    final_result["session_id"] = resolved_session_id
    final_result["session_state"] = public_session_state(session)
    final_result["stage"] = session["stage"]
    return final_result
