from services.classifier import predict_category
from services.knowledge_base import get_legal_info

def process_user_input(text: str):
    # Step 1: classify input
    result = predict_category(text)
    category = result["category"]
    confidence = result["confidence"]

    # Step 2: fetch legal knowledge
    legal_info = get_legal_info(category,text)

    # Step 3: combine response
    return {
    "category": category,
    "subcategory": legal_info["subcategory"],
    "confidence": confidence,
    "rights": legal_info["rights"],
    "law": legal_info["law"],
    "steps": legal_info["steps"],
    "documents": legal_info["documents"]
}