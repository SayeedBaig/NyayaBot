import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "db", "seed_data.json")

with open(DATA_PATH, "r", encoding="utf-8") as file:
    knowledge_data = json.load(file)

# Try to initialize semantic retriever
_retriever_available = False
try:
    from services.retriever import initialize as init_retriever, retrieve_best_match
    init_retriever()
    _retriever_available = True
except Exception:
    pass  # Will fallback to keyword matching


def _match_subcategory(category_data, text):
    text_lower = (text or "").lower()
    best_subcategory = None
    best_score = 0

    for subcategory, info in category_data.items():
        keywords = info.get("keywords", [])
        score = sum(1 for keyword in keywords if keyword.lower() in text_lower)
        if score > best_score:
            best_subcategory = subcategory
            best_score = score

    return best_subcategory


def get_legal_info(category: str, subcategory: str = None, text: str = ""):
    """
    Get legal information with semantic retrieval + keyword fallback.
    """
    if category not in knowledge_data:
        return {
            "subcategory": "unknown",
            "rights": [],
            "law": [],
            "steps": [],
            "documents": [],
            "similarity": 0.0,
        }

    category_data = knowledge_data[category]
    similarity = 0.0
    selected_subcategory = None

    # Try semantic retrieval first
    if text and _retriever_available:
        try:
            semantic_result = retrieve_best_match(text, category, top_k=1)
            if semantic_result:
                selected_subcategory = semantic_result.get("subcategory")
                similarity = semantic_result.get("similarity", 0.0)
        except Exception:
            pass

    # Fallback to keyword matching if semantic failed
    if not selected_subcategory:
        selected_subcategory = subcategory if subcategory in category_data else None
        selected_subcategory = selected_subcategory or _match_subcategory(category_data, text)

    # Final fallback: use first subcategory
    selected_subcategory = selected_subcategory or next(iter(category_data.keys()))
    selected = category_data[selected_subcategory]

    return {
        "subcategory": selected_subcategory,
        "rights": selected.get("rights", []),
        "law": selected.get("law", []),
        "steps": selected.get("steps", []),
        "documents": selected.get("documents", []),
        "similarity": similarity,
    }