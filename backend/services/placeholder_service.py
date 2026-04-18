from services.classifier import predict_category
from services.knowledge_base import get_legal_info
from services.response_generator import generate_response

def process_user_input(text: str):
    # Step 1: classify input
    result = predict_category(text)
    category = result["category"]
    confidence = result["confidence"]

    # Step 2: get legal data
    legal_info = get_legal_info(category, text)

    # Step 3: prepare data for response generator
    combined_data = {
        "category": category,
        "subcategory": legal_info["subcategory"],
        "rights": legal_info["rights"],
        "law": legal_info["law"],
        "steps": legal_info["steps"],
        "documents": legal_info["documents"]
    }

    # Step 4: generate human response
    final_response = generate_response(combined_data)

    # Step 5: return final output
    return {
        "category": category,
        "confidence": confidence,
        "response": final_response["response"]
    }