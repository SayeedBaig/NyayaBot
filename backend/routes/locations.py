from fastapi import APIRouter
from services.location_service import get_locations

router = APIRouter()

@router.get("/locations")
def fetch_locations(category: str, city: str = "Bengaluru"):
    locations = get_locations(category, city)

    return {
        "locations": locations
    }