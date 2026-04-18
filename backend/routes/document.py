from fastapi import APIRouter
from fastapi.responses import FileResponse
from services.doc_generator import generate_document

router = APIRouter()

@router.post("/generate-document")
def create_document(data: dict):
    category = data.get("category")
    user_name = data.get("user_name")
    details = data.get("details")
    opposite_party = data.get("opposite_party")
    issue = data.get("issue")

    file_path = generate_document(
        category,
        user_name,
        details,
        opposite_party,
        issue
    )

    return FileResponse(
        path=file_path,
        filename="complaint.docx",  # ✅ FIX HERE
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )