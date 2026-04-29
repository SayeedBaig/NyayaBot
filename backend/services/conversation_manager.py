from copy import deepcopy


_session_store = {}
_FOLLOW_UP_FLOW = {
    "labour": [
        ("duration", "How long has this issue been happening?"),
        ("employer_name", "What is your employer's name?"),
        ("proof_available", "Do you have any proof such as salary slips?"),
    ],
    "tenant": [
        ("issue_type", "What type of tenant issue is this?"),
        ("duration", "How long has this issue been happening?"),
        ("rent_agreement", "Do you have a rent agreement?"),
    ],
    "consumer": [
        ("product/service", "Is this about a product or a service?"),
        ("date_of_issue", "When did the issue happen?"),
        ("proof", "Do you have any proof such as bills, chats, or screenshots?"),
    ],
}
_CITY_QUESTION = "Which city are you located in?"

_FIELD_ALIASES = {
    "employer_name": ("employer_name", "organization"),
}


def _default_session():
    return {
        "category": None,
        "subcategory": None,
        "city": None,
        "collected_info": {},
        "stage": "initial",
        "questions_asked": [],
        "awaiting_field": None,
    }


def init_session(session_id):
    """Initialize a new empty session for the provided session ID."""
    _session_store[session_id] = _default_session()
    return _session_store[session_id]


def get_session(session_id):
    """Return the session data for the provided session ID."""
    return _session_store.get(session_id)


def update_session(session_id, key, value):
    """Update a top-level session field."""
    session = _session_store.get(session_id)
    if session is None:
        session = init_session(session_id)

    session[key] = value
    return session


def add_collected_info(session_id, field, value):
    """Store a collected answer inside the session's collected_info map."""
    session = _session_store.get(session_id)
    if session is None:
        session = init_session(session_id)

    session["collected_info"][field] = value
    return session["collected_info"]


def has_collected_value(collected_info, field):
    """Check whether a field or one of its aliases already has a value."""
    candidate_fields = _FIELD_ALIASES.get(field, (field,))
    return any(collected_info.get(candidate_field) for candidate_field in candidate_fields)


def get_next_question(session):
    """Return the next category-based question for a missing field."""
    category = session.get("category")
    collected_info = session.get("collected_info", {})
    questions_asked = set(session.get("questions_asked", []))
    awaiting_field = session.get("awaiting_field")
    city = session.get("city")

    flow = _FOLLOW_UP_FLOW.get(category, [])

    if awaiting_field == "city" and not city:
        return {
            "field": "city",
            "question": _CITY_QUESTION,
        }

    for field, question in flow:
        if field == awaiting_field and not has_collected_value(collected_info, field):
            return {
                "field": field,
                "question": question,
            }

    for field, question in flow:
        if has_collected_value(collected_info, field):
            continue
        if question in questions_asked:
            continue
        return {
            "field": field,
            "question": question,
        }

    if not city and _CITY_QUESTION not in questions_asked:
        return {
            "field": "city",
            "question": _CITY_QUESTION,
        }

    return None


def get_all_sessions():
    """Return a copy of the in-memory session store."""
    return deepcopy(_session_store)


def reset_session(session_id):
    """Reset an existing session back to its default state."""
    _session_store[session_id] = _default_session()
    return _session_store[session_id]
