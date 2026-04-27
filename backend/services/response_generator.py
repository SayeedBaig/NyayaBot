def _label(value):
    return (value or "").replace("_", " ")


def generate_response(data: dict):
    category = data.get("category", "")
    subcategory = data.get("subcategory", "")
    entities = data.get("entities", {})
    rights = data.get("rights", [])
    law = data.get("law", [])
    steps = data.get("steps", [])
    documents = data.get("documents", [])

    issue = entities.get("issue") or _label(subcategory) or _label(category) or "legal issue"
    party = entities.get("opposite_party") or entities.get("employer")
    duration = entities.get("duration")

    context_parts = []
    if party:
        context_parts.append(f"with {party}")
    if duration:
        context_parts.append(f"for {duration}")

    context = f" {' '.join(context_parts)}" if context_parts else ""
    summary = f"Based on your {issue}{context}, this appears to be a {category} matter."

    if steps:
        first_step = steps[0].strip().rstrip(".")
        first_step = first_step[0].lower() + first_step[1:] if first_step else "collect proof"
        summary += f" A practical first step is to {first_step}."

    response_parts = [summary]
    if rights:
        response_parts.append(f"Your key right: {rights[0]}")
    if law:
        response_parts.append(f"Relevant law: {law[0]}")
    if documents:
        response_parts.append(f"Keep proof ready, especially {documents[0]}.")

    return {
        "summary": summary,
        "response": " ".join(response_parts).strip(),
    }
