import json

# Load location data
with open("db/locations.json", "r") as file:
    location_data = json.load(file)


def get_locations(category: str, city: str = "Bengaluru"):
    # Get locations for category
    if category not in location_data:
        return []

    category_locations = location_data[category]

    # Filter by city (case insensitive)
    filtered = [
        loc for loc in category_locations
        if loc["city"].lower() == city.lower()
    ]

    # If no match, return all for that category
    if not filtered:
        return category_locations

    return filtered