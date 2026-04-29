from copy import deepcopy
from uuid import uuid4


_sessions = {}


def _default_session():
    return {
        "category": "unknown",
        "subcategory": "unknown",
        "details_collected": [],
        "stage": "initial",
        "initial_query": "",
        "language": "en",
        "city": "",
    }


def get_or_create_session(session_id=None):
    resolved_session_id = session_id or str(uuid4())
    if resolved_session_id not in _sessions:
        _sessions[resolved_session_id] = _default_session()
    return resolved_session_id, _sessions[resolved_session_id]


def reset_session(session_id=None):
    resolved_session_id = session_id or str(uuid4())
    _sessions[resolved_session_id] = _default_session()
    return resolved_session_id, _sessions[resolved_session_id]


def public_session_state(session):
    return {
        "category": session.get("category", "unknown"),
        "subcategory": session.get("subcategory", "unknown"),
        "details_collected": deepcopy(session.get("details_collected", [])),
        "stage": session.get("stage", "initial"),
    }
