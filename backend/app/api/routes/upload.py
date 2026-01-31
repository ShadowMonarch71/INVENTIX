"""
Inventix AI - Upload API Routes
===============================
Handle file uploads including PDF extraction.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.pdf_extractor import extract_text_from_pdf

router = APIRouter()


class PDFUploadResponse(BaseModel):
    """Response from PDF upload."""
    success: bool
    text: str
    page_count: int
    char_count: int
    filename: str
    error: Optional[str] = None


@router.post("/pdf", response_model=PDFUploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF file and extract its text content.
    
    Returns:
        Extracted text that can be used in other analysis endpoints.
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are accepted"
        )
    
    # Check file size (max 10MB)
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File size exceeds 10MB limit"
        )
    
    # Extract text
    result = extract_text_from_pdf(contents)
    
    if not result.success:
        return PDFUploadResponse(
            success=False,
            text="",
            page_count=0,
            char_count=0,
            filename=file.filename,
            error=result.error
        )
    
    return PDFUploadResponse(
        success=True,
        text=result.text,
        page_count=result.page_count,
        char_count=result.char_count,
        filename=file.filename
    )


@router.get("/status")
async def upload_status():
    """Get upload service status."""
    return {
        "service": "upload",
        "status": "active",
        "supported_formats": ["pdf"],
        "max_file_size_mb": 10,
        "max_pages": 50
    }
