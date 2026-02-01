"""
Inventix AI - Document Processor
================================
Handles document ingestion for PDF, DOCX, and text input.
Evidence-locked processing with structured error handling.
"""

import io
import re
from typing import Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class DocumentType(str, Enum):
    """Supported document types."""
    PDF = "pdf"
    DOCX = "docx"
    TEXT = "text"
    UNKNOWN = "unknown"


@dataclass
class DocumentResult:
    """Result of document processing."""
    success: bool
    text: Optional[str] = None
    word_count: int = 0
    paragraph_count: int = 0
    sections: list = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    metadata: dict = None

    def __post_init__(self):
        if self.sections is None:
            self.sections = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class CrashLog:
    """Structured crash log for failure handling."""
    operation: str
    error_code: str
    error_message: str
    recommendation: str
    recoverable: bool = False


class DocumentProcessor:
    """
    ANTIGRAVITY Document Processor
    
    Handles document ingestion with evidence-locked processing:
    - Extracts raw text reliably
    - Normalizes formatting
    - Preserves technical terminology
    - Maintains paragraph and section boundaries
    """

    SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt'}
    MAX_DOCUMENT_SIZE = 10 * 1024 * 1024  # 10MB limit

    def __init__(self):
        self._pdf_available = self._check_pdf_support()
        self._docx_available = self._check_docx_support()

    def _check_pdf_support(self) -> bool:
        """Check if PDF extraction is available."""
        try:
            import pypdf
            return True
        except ImportError:
            return False

    def _check_docx_support(self) -> bool:
        """Check if DOCX extraction is available."""
        try:
            import docx
            return True
        except ImportError:
            return False

    def detect_document_type(self, filename: str, content_type: Optional[str] = None) -> DocumentType:
        """Detect document type from filename or content type."""
        if filename:
            ext = Path(filename).suffix.lower()
            if ext == '.pdf':
                return DocumentType.PDF
            elif ext in ['.docx', '.doc']:
                return DocumentType.DOCX
            elif ext == '.txt':
                return DocumentType.TEXT
        
        if content_type:
            if 'pdf' in content_type:
                return DocumentType.PDF
            elif 'word' in content_type or 'document' in content_type:
                return DocumentType.DOCX
            elif 'text' in content_type:
                return DocumentType.TEXT
        
        return DocumentType.UNKNOWN

    def process_document(
        self, 
        content: bytes, 
        filename: str,
        content_type: Optional[str] = None
    ) -> DocumentResult:
        """
        Process a document and extract text.
        
        Returns structured result with extracted text or error details.
        """
        # Validate size
        if len(content) > self.MAX_DOCUMENT_SIZE:
            return DocumentResult(
                success=False,
                error_code="DOCUMENT_TOO_LARGE",
                error_message=f"Document exceeds maximum size of {self.MAX_DOCUMENT_SIZE // (1024*1024)}MB"
            )

        doc_type = self.detect_document_type(filename, content_type)

        try:
            if doc_type == DocumentType.PDF:
                return self._process_pdf(content)
            elif doc_type == DocumentType.DOCX:
                return self._process_docx(content)
            elif doc_type == DocumentType.TEXT:
                return self._process_text(content)
            else:
                return DocumentResult(
                    success=False,
                    error_code="UNSUPPORTED_FORMAT",
                    error_message=f"Document type '{doc_type}' is not supported. Supported formats: PDF, DOCX, TXT"
                )
        except Exception as e:
            return DocumentResult(
                success=False,
                error_code="PROCESSING_ERROR",
                error_message=f"Failed to process document: {str(e)}"
            )

    def _process_pdf(self, content: bytes) -> DocumentResult:
        """Extract text from PDF."""
        if not self._pdf_available:
            return DocumentResult(
                success=False,
                error_code="PDF_LIBRARY_MISSING",
                error_message="PDF processing library (pypdf) is not installed"
            )

        try:
            import pypdf
            
            reader = pypdf.PdfReader(io.BytesIO(content))
            
            if len(reader.pages) == 0:
                return DocumentResult(
                    success=False,
                    error_code="EMPTY_PDF",
                    error_message="PDF contains no readable pages"
                )

            text_parts = []
            sections = []
            
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
                    sections.append({
                        "type": "page",
                        "index": page_num + 1,
                        "content": page_text[:500] + "..." if len(page_text) > 500 else page_text
                    })

            if not text_parts:
                return DocumentResult(
                    success=False,
                    error_code="NO_TEXT_CONTENT",
                    error_message="PDF does not contain extractable text. Image-based PDFs require OCR which is not supported."
                )

            full_text = self._normalize_text("\n\n".join(text_parts))
            
            return DocumentResult(
                success=True,
                text=full_text,
                word_count=len(full_text.split()),
                paragraph_count=len([p for p in full_text.split('\n\n') if p.strip()]),
                sections=sections,
                metadata={
                    "page_count": len(reader.pages),
                    "document_type": "pdf"
                }
            )

        except Exception as e:
            return DocumentResult(
                success=False,
                error_code="PDF_EXTRACTION_FAILED",
                error_message=f"Failed to extract text from PDF: {str(e)}"
            )

    def _process_docx(self, content: bytes) -> DocumentResult:
        """Extract text from DOCX."""
        if not self._docx_available:
            return DocumentResult(
                success=False,
                error_code="DOCX_LIBRARY_MISSING",
                error_message="DOCX processing library (python-docx) is not installed"
            )

        try:
            import docx
            
            doc = docx.Document(io.BytesIO(content))
            
            paragraphs = []
            sections = []
            
            for para in doc.paragraphs:
                if para.text.strip():
                    paragraphs.append(para.text)
                    
                    # Detect section headers
                    if para.style and 'Heading' in para.style.name:
                        sections.append({
                            "type": "heading",
                            "level": int(para.style.name[-1]) if para.style.name[-1].isdigit() else 1,
                            "content": para.text
                        })

            if not paragraphs:
                return DocumentResult(
                    success=False,
                    error_code="EMPTY_DOCUMENT",
                    error_message="Document contains no readable text"
                )

            full_text = self._normalize_text("\n\n".join(paragraphs))
            
            return DocumentResult(
                success=True,
                text=full_text,
                word_count=len(full_text.split()),
                paragraph_count=len(paragraphs),
                sections=sections,
                metadata={
                    "paragraph_count": len(paragraphs),
                    "document_type": "docx"
                }
            )

        except Exception as e:
            return DocumentResult(
                success=False,
                error_code="DOCX_EXTRACTION_FAILED",
                error_message=f"Failed to extract text from DOCX: {str(e)}"
            )

    def _process_text(self, content: bytes) -> DocumentResult:
        """Process plain text content."""
        try:
            # Try UTF-8 first, then fallback to latin-1
            try:
                text = content.decode('utf-8')
            except UnicodeDecodeError:
                text = content.decode('latin-1')

            if not text.strip():
                return DocumentResult(
                    success=False,
                    error_code="EMPTY_TEXT",
                    error_message="Text content is empty"
                )

            normalized = self._normalize_text(text)
            paragraphs = [p for p in normalized.split('\n\n') if p.strip()]
            
            return DocumentResult(
                success=True,
                text=normalized,
                word_count=len(normalized.split()),
                paragraph_count=len(paragraphs),
                metadata={"document_type": "text"}
            )

        except Exception as e:
            return DocumentResult(
                success=False,
                error_code="TEXT_PROCESSING_FAILED",
                error_message=f"Failed to process text: {str(e)}"
            )

    def process_pasted_text(self, text: str) -> DocumentResult:
        """Process directly pasted text input."""
        if not text or not text.strip():
            return DocumentResult(
                success=False,
                error_code="EMPTY_INPUT",
                error_message="No text provided"
            )

        normalized = self._normalize_text(text)
        paragraphs = [p for p in normalized.split('\n\n') if p.strip()]
        
        return DocumentResult(
            success=True,
            text=normalized,
            word_count=len(normalized.split()),
            paragraph_count=len(paragraphs),
            metadata={"document_type": "pasted_text"}
        )

    def _normalize_text(self, text: str) -> str:
        """
        Normalize text while preserving technical terminology.
        
        - Removes excessive whitespace
        - Preserves paragraph boundaries
        - Maintains technical terms and formatting
        """
        # Replace multiple spaces with single space
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Replace multiple newlines with double newline (paragraph boundary)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Clean up leading/trailing whitespace per line while preserving structure
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        # Remove leading/trailing whitespace from full text
        text = text.strip()
        
        return text

    def emit_crash_log(self, operation: str, result: DocumentResult) -> CrashLog:
        """Generate a structured crash log from a failed operation."""
        recommendations = {
            "DOCUMENT_TOO_LARGE": "Please reduce the document size or split into smaller parts",
            "UNSUPPORTED_FORMAT": "Please convert your document to PDF, DOCX, or TXT format",
            "NO_TEXT_CONTENT": "Please ensure your PDF contains selectable text, not scanned images",
            "PDF_LIBRARY_MISSING": "Contact system administrator to install PDF support",
            "DOCX_LIBRARY_MISSING": "Contact system administrator to install DOCX support",
            "EMPTY_DOCUMENT": "Please provide a document with content",
            "EMPTY_INPUT": "Please provide text input",
        }

        return CrashLog(
            operation=operation,
            error_code=result.error_code or "UNKNOWN_ERROR",
            error_message=result.error_message or "An unknown error occurred",
            recommendation=recommendations.get(result.error_code, "Please review the input and try again"),
            recoverable=result.error_code in ["EMPTY_INPUT", "EMPTY_DOCUMENT", "UNSUPPORTED_FORMAT"]
        )
