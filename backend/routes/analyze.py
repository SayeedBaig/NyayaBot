from fastapi import APIRouter
from services.placeholder_service import process_user_input 

router = APIRouter()

@router.post("/analyze")
def analyze(data:dict):
    text = data.get("text")

    result = process_user_input(text)   

    return result    