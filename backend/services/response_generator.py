import random

def generate_response(data: dict):
    category = data.get("category", "")
    rights = data.get("rights", [])
    law = data.get("law", [])
    steps = data.get("steps", [])
    documents = data.get("documents", [])

    # 🔹 Intro variations
    intros = {
        "labour": [
            "It looks like you're facing a workplace-related issue.",
            "This seems to be a labour-related concern.",
            "You appear to be dealing with an employment issue."
        ],
        "tenant": [
            "It seems you are facing a housing or rental issue.",
            "This appears to be related to a tenant or landlord problem.",
            "You may be dealing with a rental dispute."
        ],
        "consumer": [
            "This looks like a consumer-related issue.",
            "It seems you are facing a problem with a product or service.",
            "You appear to have a consumer complaint."
        ]
    }

    intro = random.choice(intros.get(category, ["This appears to be a legal issue."]))

    # 🔹 Build parts with variation
    parts = [intro]

    if rights:
        parts.append(f"You have legal rights, such as {rights[0]}.")

    if law:
        parts.append(f"This is supported by {law[0]}.")

    if steps:
        parts.append(f"You can take steps like {', '.join(steps[:2])}.")

    if documents:
        parts.append(f"Keep documents ready, including {', '.join(documents[:2])}.")

    # 🔹 Final response
    response = " ".join(parts)

    return {
        "response": response.strip()
    }