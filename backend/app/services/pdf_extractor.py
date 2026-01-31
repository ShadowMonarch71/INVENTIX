"""
Inventix AI - PDF Extraction Service
=====================================
Extract text content from uploaded PDF files.
"""

import fitz  # PyMuPDF
from typing import Optional
from dataclasses import dataclass
import io


@dataclass
class PDFExtractionResult:
    """Result of PDF text extraction."""
    success: bool
    text: str
    page_count: int
    error: Optional[str] = None
    char_count: int = 0


def extract_text_from_pdf(pdf_bytes: bytes, max_pages: int = 50) -> PDFExtractionResult:
    """
    Extract text content from a PDF file.
    
    Args:
        pdf_bytes: Raw bytes of the PDF file
        max_pages: Maximum number of pages to process
        
    Returns:
        PDFExtractionResult with extracted text or error
    """
    try:
        # Open PDF from bytes
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        # Limit pages
        page_count = min(len(doc), max_pages)
        
        # Extract text from each page
        text_parts = []
        for page_num in range(page_count):
            page = doc.load_page(page_num)
            page_text = page.get_text()
            if page_text.strip():
                text_parts.append(f"--- Page {page_num + 1} ---\n{page_text}")
        
        doc.close()
        
        # Combine all text
        full_text = "\n\n".join(text_parts)
        
        # Truncate if too long (keep first 50000 chars)
        if len(full_text) > 50000:
            full_text = full_text[:50000] + "\n\n[... Text truncated due to length ...]"
        
        return PDFExtractionResult(
            success=True,
            text=full_text,
            page_count=page_count,
            char_count=len(full_text)
        )
        
    except Exception as e:
        return PDFExtractionResult(
            success=False,
            text="",
            page_count=0,
            error=str(e)
        )


def extract_text_from_pdf_file(file_path: str, max_pages: int = 50) -> PDFExtractionResult:
    """
    Extract text from a PDF file path.
    
    Args:
        file_path: Path to the PDF file
        max_pages: Maximum number of pages to process
        
    Returns:
        PDFExtractionResult with extracted text or error
    """
    try:
        with open(file_path, 'rb') as f:
            pdf_bytes = f.read()
        return extract_text_from_pdf(pdf_bytes, max_pages)
    except Exception as e:
        return PDFExtractionResult(
            success=False,
            text="",
            page_count=0,
            error=str(e)
        )
