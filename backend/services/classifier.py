import csv
import os
import re
from collections import Counter

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAINING_PATH = os.path.join(BASE_DIR, "models", "training_data.csv")

CATEGORY_KEYWORDS = {
    "labour": [
        "salary", "wages", "employer", "company", "job", "fired", "terminated",
        "overtime", "hr", "pf", "esi", "boss", "work", "employee"
    ],
    "tenant": [
        "landlord", "tenant", "rent", "deposit", "evict", "vacate", "house",
        "flat", "room", "owner", "lease", "water", "electricity"
    ],
    "consumer": [
        "product", "refund", "defective", "broken", "order", "seller", "warranty",
        "service", "delivery", "website", "amazon", "flipkart", "repair"
    ],
}

SUBCATEGORY_RULES = {
    "labour": {
        "unpaid_salary": ["salary", "wages", "unpaid", "not paid", "payment delayed"],
        "wrongful_termination": ["fired", "terminated", "removed", "dismissed", "without notice"],
        "overtime_nonpayment": ["overtime", "extra hours", "12 hours", "late night"],
        "pf_esi_issue": ["pf", "provident fund", "esi", "uan", "epfo"],
    },
    "tenant": {
        "illegal_eviction": ["evict", "vacate", "force", "throw out", "leave house"],
        "deposit_not_returned": ["deposit", "security", "advance", "not returning"],
        "landlord_harassment": ["harass", "threat", "abuse", "entering", "water", "electricity", "lock"],
        "rent_increase_dispute": ["rent increase", "increase rent", "hike", "higher rent"],
    },
    "consumer": {
        "defective_product": ["defective", "broken", "damaged", "not working", "faulty"],
        "refund_not_given": ["refund", "money back", "cancelled", "return rejected"],
        "service_deficiency": ["bad service", "service deficiency", "not provided", "delay"],
        "warranty_denied": ["warranty", "guarantee", "service center", "repair denied"],
    },
}


def _load_training_data():
    with open(TRAINING_PATH, newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    return pd.DataFrame(rows)


data = _load_training_data()
x = data["text"]
y = data["category"]

vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
x_vectorized = vectorizer.fit_transform(x)

model = LogisticRegression(max_iter=1000, class_weight="balanced")
model.fit(x_vectorized, y)


def _contains(text_lower, keywords):
    return any(keyword in text_lower for keyword in keywords)


def _keyword_category(text_lower):
    scores = {
        category: sum(1 for keyword in keywords if keyword in text_lower)
        for category, keywords in CATEGORY_KEYWORDS.items()
    }
    category, score = Counter(scores).most_common(1)[0]
    if score == 0:
        return None, 0.0
    return category, min(0.95, 0.68 + (score * 0.08))


def _keyword_subcategory(category, text_lower):
    rules = SUBCATEGORY_RULES.get(category, {})
    best_subcategory = None
    best_score = 0

    for subcategory, keywords in rules.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        if score > best_score:
            best_subcategory = subcategory
            best_score = score

    return best_subcategory


def _ml_prediction(text):
    text_vectorized = vectorizer.transform([text])
    prediction = model.predict(text_vectorized)[0]
    probabilities = model.predict_proba(text_vectorized)[0]
    confidence = float(max(probabilities))
    return prediction, confidence


def predict_category(text: str):
    normalized = re.sub(r"\s+", " ", text or "").strip().lower()
    if not normalized or len(normalized) < 5:
        return {
            "category": "unknown",
            "subcategory": "unknown",
            "confidence": 0.0,
            "message": "Please provide more details about your issue",
        }

    keyword_category, keyword_confidence = _keyword_category(normalized)
    ml_category, ml_confidence = _ml_prediction(normalized)

    if keyword_category:
        category = keyword_category
        confidence = max(keyword_confidence, ml_confidence if ml_category == keyword_category else 0)
    else:
        category = ml_category
        confidence = ml_confidence

    subcategory = _keyword_subcategory(category, normalized)

    if confidence < 0.3:
        return {
            "category": "unknown",
            "subcategory": "unknown",
            "confidence": round(confidence, 2),
            "message": "Please provide more details about your issue",
        }

    return {
        "category": category,
        "subcategory": subcategory or "general",
        "confidence": round(confidence, 2),
    }
