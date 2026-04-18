import json
# Load JSON data
with open("db/seed_data.json", "r") as file:
    knowledge_data = json.load(file)


# def get_legal_info(category: str):
#     # Check if category exists
#     if category in knowledge_data:
#         category_data = knowledge_data[category]

#         # Pick first subcase (for now)
#         first_subcase = next(iter(category_data.values()))

#         return {
#             "rights": first_subcase.get("rights", []),
#             "law": first_subcase.get("law", []),
#             "steps": first_subcase.get("steps", []),
#             "documents": first_subcase.get("documents", [])
#         }

#     # If category not found
#     return {
#         "rights": [],
#         "law": [],
#         "steps": [],
#         "documents": []
#     }


def get_legal_info(category: str, text: str = ""):
    if category not in knowledge_data:
        return {
            "subcategory": "unknown",
            "rights": [],
            "law": [],
            "steps": [],
            "documents": []
        }

    category_data = knowledge_data[category]
    text_lower = text.lower()

    # 🔹 Subcategory keyword mapping
    subcategory = None

    if category == "labour":
        if any(word in text_lower for word in ["salary", "wages"]):
            subcategory = "unpaid_salary"
        elif "termination" in text_lower:
            subcategory = "wrongful_termination"

    elif category == "tenant":
        if any(word in text_lower for word in ["evict", "vacate"]):
            subcategory = "eviction"
        elif "deposit" in text_lower:
            subcategory = "deposit_issue"

    elif category == "consumer":
        if any(word in text_lower for word in ["refund", "defect"]):
            subcategory = "product_defect"

    # 🔹 Fallback to first subcase
    if subcategory and subcategory in category_data:
        selected = category_data[subcategory]
    else:
        subcategory = next(iter(category_data.keys()))
        selected = category_data[subcategory]

    return {
        "subcategory": subcategory,
        "rights": selected.get("rights", []),
        "law": selected.get("law", []),
        "steps": selected.get("steps", []),
        "documents": selected.get("documents", [])
    }