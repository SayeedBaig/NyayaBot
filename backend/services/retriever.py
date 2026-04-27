"""
Semantic Retriever Module
Uses sentence-transformers for semantic search within legal knowledge.
"""

import json
import os
from typing import Optional

import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "db", "seed_data.json")

# Cache for embeddings
_embeddings_cache = {}
_model = None
_knowledge_data = None


def _load_knowledge():
    """Load legal knowledge from JSON file."""
    global _knowledge_data
    if _knowledge_data is None:
        with open(DATA_PATH, "r", encoding="utf-8") as file:
            _knowledge_data = json.load(file)
    return _knowledge_data


def _get_model():
    """Get or load the sentence transformer model."""
    global _model
    if _model is None:
        if SentenceTransformer is None:
            raise ImportError("sentence-transformers not installed")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _create_search_text(subcategory: str, data: dict) -> str:
    """Create combined text for embedding from subcategory data."""
    rights = " ".join(data.get("rights", []))
    steps = " ".join(data.get("steps", []))
    keywords = " ".join(data.get("keywords", []))
    return f"{subcategory} {rights} {steps} {keywords}".lower()


def _compute_embeddings():
    """Precompute embeddings for all subcategories on startup."""
    global _embeddings_cache

    knowledge = _load_knowledge()
    model = _get_model()

    for category, subcategories in knowledge.items():
        _embeddings_cache[category] = {}

        for subcategory, info in subcategories.items():
            search_text = _create_search_text(subcategory, info)
            embedding = model.encode(search_text, convert_to_numpy=True)
            _embeddings_cache[category][subcategory] = {
                "embedding": embedding,
                "info": info,
            }


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors."""
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot_product / (norm_a * norm_b))


def initialize():
    """Initialize the retriever by precomputing embeddings."""
    if not _embeddings_cache:
        _compute_embeddings()


def retrieve_best_match(query: str, category: str, top_k: int = 1) -> Optional[dict]:
    """
    Retrieve the best matching subcategory for a query within a category.

    Args:
        query: User query text
        category: Legal category (labour, tenant, consumer)
        top_k: Number of top results to return

    Returns:
        Dict with subcategory, info, similarity score
    """
    if not _embeddings_cache:
        initialize()

    if category not in _embeddings_cache:
        return None

    model = _get_model()
    query_embedding = model.encode(query.lower(), convert_to_numpy=True)

    similarities = []
    for subcategory, data in _embeddings_cache[category].items():
        sim = _cosine_similarity(query_embedding, data["embedding"])
        similarities.append((subcategory, sim, data["info"]))

    # Sort by similarity (descending)
    similarities.sort(key=lambda x: x[1], reverse=True)

    if top_k == 1:
        if similarities and similarities[0][1] > 0.2:
            return {
                "subcategory": similarities[0][0],
                "info": similarities[0][2],
                "similarity": similarities[0][1],
            }
        return None

    return [
        {"subcategory": s[0], "info": s[2], "similarity": s[1]}
        for s in similarities[:top_k]
        if s[1] > 0.2
    ]


def get_embedding_cache():
    """Return the embeddings cache (for debugging/inspection)."""
    return _embeddings_cache