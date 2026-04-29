from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from services.doc_generator import generate_document

router = APIRouter()


@router.post("/generate-document")
def create_document(data: dict):
    report = data.get("report") or {}

    if not report:
        raise HTTPException(status_code=400, detail="Report data is required")

    file_path = generate_document(report)

    return FileResponse(
        path=file_path,
        filename="legalease-ai-report.pdf",
        media_type="application/pdf",
    )
