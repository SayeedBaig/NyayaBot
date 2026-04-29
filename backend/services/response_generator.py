def _label(value):
    return (value or "").replace("_", " ")


def _compose_case_intro(issue, party, duration):
    issue_text = _label(issue) or "legal issue"

    if party and duration:
        return f"Based on your issue with {party} about {issue_text} for {duration}, this appears to be a"
    if party:
        return f"Based on your issue with {party} about {issue_text}, this appears to be a"
    if duration:
        return f"Based on your {issue_text} issue for {duration}, this appears to be a"
    return f"Based on your {issue_text} issue, this appears to be a"


def generate_response(data: dict):
    category = data.get("category", "")
    subcategory = data.get("subcategory", "")
    entities = data.get("entities", {})
    rights = data.get("rights", [])
    law = data.get("law", [])
    steps = data.get("steps", [])
    documents = data.get("documents", [])

    issue = entities.get("issue") or _label(subcategory) or _label(category) or "legal issue"
    party = entities.get("organization") or entities.get("opposite_party") or entities.get("employer")
    duration = entities.get("duration")
    intro = _compose_case_intro(issue, party, duration)

    issue_text = issue.replace("_", " ")
    if steps:
        first_step = steps[0].strip().rstrip(".")
        first_step = first_step[0].lower() + first_step[1:] if first_step else "collect proof"
    else:
        first_step = "keep your proof together and make a written record"

    next_step = ""
    if len(steps) > 1:
        next_step = steps[1].strip().rstrip(".")
    elif documents:
        next_step = f"keep {documents[0]} ready before you escalate the matter"
    else:
        next_step = "escalate it to the correct legal office if there is no response"

    debug_detail = first_step if steps else (rights[0] if rights else "none")
    print(
        f"[response_generator] subcategory={subcategory or 'unknown'} "
        f"detail={debug_detail}"
    )

    summary = f"{intro} {category} matter. You can start by {first_step.lower().replace('send ', 'sending ', 1)}. Next, {next_step.lower()}."

    response_parts = [summary]
    if rights:
        response_parts.append(f"Your key right is: {rights[0]}")

    return {
        "summary": summary,
        "response": " ".join(response_parts).strip(),
    }
