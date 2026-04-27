from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from services.doc_generator import generate_document

router = APIRouter()


@router.post("/generate-document")
def create_document(data: dict):
    category = data.get("category")
    user_name = (data.get("user_name") or "").strip()
    details = (data.get("details") or "").strip()
    opposite_party = (data.get("opposite_party") or "").strip()
    issue = (data.get("issue") or "").strip()

    if not all([category, user_name, details, opposite_party, issue]):
        raise HTTPException(status_code=400, detail="All document fields are required")

    file_path = generate_document(
        category,
        user_name,
        details,
        opposite_party,
        issue,
    )

    return FileResponse(
        path=file_path,
        filename="complaint.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
