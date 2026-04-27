from services.classifier import predict_category
from services.input_parser import extract_entities
from services.knowledge_base import get_legal_info
from services.llm_service import refine_response, is_llm_available
from services.location_service import get_locations
from services.query_understanding import understand_query, normalize_query
from services.response_generator import generate_response
from services.translator import (
    detect_language,
    translate_to_english,
    translate_to_target,
)


def _translate_list(items, target_lang):
    if target_lang == "en":
        return items
    return [translate_to_target(item, target_lang) for item in items]


def _calculate_combined_confidence(classifier_confidence: float, retrieval_similarity: float) -> float:
    """
    Calculate combined confidence from classifier and retriever.
    """
    if retrieval_similarity > 0:
        # Weight classifier more since it determines category
        combined = (classifier_confidence * 0.6) + (retrieval_similarity * 0.4)
        return min(0.99, combined)
    return classifier_confidence


def _enhance_personalization(response: str, entities: dict) -> str:
    """
    Enhance response with personalization based on extracted entities.
    """
    if not entities:
        return response

    employer = entities.get("employer")
    opposite_party = entities.get("opposite_party")
    duration = entities.get("duration")

    # Only add personalization once at the beginning
    if employer and "with " + employer.lower() not in response.lower():
        response = f"Based on your issue with {employer}, {response}"
    elif opposite_party and "with " + opposite_party.lower() not in response.lower():
        response = f"Based on your issue with {opposite_party}, {response}"

    return response


def process_user_input(text: str, city: str = "Bengaluru"):
    clean_text = (text or "").strip()
    if not clean_text:
        return {
            "ok": False,
            "error": "empty_input",
            "message": "Please describe your issue",
        }

    if len(clean_text) < 8 or not any(char.isalpha() for char in clean_text):
        return {
            "ok": False,
            "error": "invalid_text",
            "message": "Please provide more details about your issue",
        }

    # Apply query understanding
    query_understanding = understand_query(clean_text)
    normalized_text = query_understanding.get("normalized", clean_text)

    detected_lang = detect_language(clean_text)
    text_en = translate_to_english(clean_text) if detected_lang != "en" else clean_text

    # Get classification
    classification = predict_category(text_en)
    classifier_confidence = classification.get("confidence", 0)

    if classification.get("category") == "unknown" or classifier_confidence < 0.6:
        return {
            "ok": False,
            "category": "unknown",
            "subcategory": "unknown",
            "confidence": classifier_confidence,
            "message": "We need more details to assist you better.",
            "response": "We need more details to assist you better.",
            "rights": [],
            "law": [],
            "steps": [],
            "documents": [],
            "locations": [],
        }

    category = classification["category"]
    entities = extract_entities(text_en)

    # Get legal info with similarity score
    legal_info = get_legal_info(
        category,
        classification.get("subcategory"),
        text_en,
    )

    # Get similarity from retrieval
    retrieval_similarity = legal_info.get("similarity", 0.0)

    # Calculate combined confidence
    confidence = _calculate_combined_confidence(classifier_confidence, retrieval_similarity)

    # Check for low confidence scenario
    if confidence < 0.5:
        return {
            "ok": False,
            "category": category,
            "subcategory": legal_info.get("subcategory"),
            "confidence": round(confidence, 2),
            "message": "We may need more details to assist you accurately.",
            "response": "We may need more details to assist you accurately.",
            "rights": [],
            "law": [],
            "steps": [],
            "documents": [],
            "locations": [],
        }

    # Combine data for response generation
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

    # Generate initial response
    generated = generate_response(combined_data)
    summary_text = generated["summary"]

    rights = legal_info["rights"]
    law = legal_info["law"]
    steps = legal_info["steps"]
    documents = legal_info["documents"]

    # Try LLM refinement if available
    llm_available = is_llm_available()
    if llm_available:
        refined = refine_response(
            summary=summary_text,
            rights=rights,
            steps=steps,
            user_query=text_en,
            entities=entities,
        )
        response_text = refined.get("response", generated["response"])

        # Apply personalization
        response_text = _enhance_personalization(response_text, entities)
    else:
        response_text = generated["response"]
        # Apply basic personalization without LLM
        response_text = _enhance_personalization(response_text, entities)

    # Translate if needed
    if detected_lang != "en":
        response_text = translate_to_target(response_text, detected_lang)
        summary_text = translate_to_target(summary_text, detected_lang)
        rights = _translate_list(rights, detected_lang)
        law = _translate_list(law, detected_lang)
        steps = _translate_list(steps, detected_lang)
        documents = _translate_list(documents, detected_lang)

    return {
        "ok": True,
        "category": category,
        "subcategory": legal_info["subcategory"],
        "confidence": round(confidence, 2),
        "entities": entities,
        "summary": summary_text,
        "response": response_text,
        "rights": rights,
        "law": law,
        "steps": steps,
        "documents": documents,
        "language": detected_lang,
        "locations": get_locations(category, city),
        "query_understanding": query_understanding,
    }