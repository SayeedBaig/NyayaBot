import json
import os
from difflib import get_close_matches


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "db", "locations.json")

with open(DATA_PATH, "r", encoding="utf-8") as file:
    location_data = json.load(file)


def _normalize_city(city: str) -> str:
    return (city or "").strip().lower()


def resolve_locations(category: str, city: str = ""):
    if category not in location_data:
        return {
            "locations": [],
            "matched_city": "",
            "needs_city": False,
            "fallback_used": False,
        }

    if not city or not city.strip():
        return {
            "locations": [],
            "matched_city": "",
            "needs_city": True,
            "fallback_used": False,
        }

    category_locations = location_data[category]
    normalized_city = _normalize_city(city)

    filtered = [
        loc for loc in category_locations
        if _normalize_city(loc.get("city", "")) == normalized_city
    ]
    if filtered:
        return {
            "locations": filtered,
            "matched_city": filtered[0].get("city", city),
            "needs_city": False,
            "fallback_used": False,
        }

    available_cities = sorted({
        loc.get("city", "")
        for loc in category_locations
        if loc.get("city")
    })
    normalized_lookup = {
        _normalize_city(available_city): available_city
        for available_city in available_cities
    }
    closest_match = get_close_matches(normalized_city, list(normalized_lookup.keys()), n=1, cutoff=0.0)
    fallback_city = normalized_lookup.get(closest_match[0], "") if closest_match else (available_cities[0] if available_cities else "")
    fallback_locations = [
        loc for loc in category_locations
        if _normalize_city(loc.get("city", "")) == _normalize_city(fallback_city)
    ]

    return {
        "locations": fallback_locations,
        "matched_city": fallback_city,
        "needs_city": False,
        "fallback_used": True,
    }


def get_locations(category: str, city: str = ""):
    return resolve_locations(category, city).get("locations", [])
