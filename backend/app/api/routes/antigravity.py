"""
Inventix AI - ANTIGRAVITY Core API Routes
==========================================
Unified API endpoints for ANTIGRAVITY core features.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from typing import Optional, List
from pydantic import BaseModel
from dataclasses import asdict

from app.services.document_processor import DocumentProcessor, DocumentType
from app.services.concept_extractor import ConceptExtractor, ConceptCategory
from app.services.prior_art_comparator import PriorArtComparator, NoveltyRisk
from app.services.research_summarizer import ResearchSummarizer
from app.services.draft_refiner import DraftRefiner, RefinementType
from app.services.auth_service import get_current_user, get_optional_user
from app.core.project_schemas import User


router = APIRouter()


# ==================== Request/Response Models ====================

class TextInput(BaseModel):
    """Text input for processing."""
    text: str
    title: Optional[str] = None
    project_type: Optional[str] = "research"  # "patent" or "research"


class ConceptExtractionResponse(BaseModel):
    """Response for concept extraction."""
    success: bool
    concepts: list
    differentiating_terms: list
    common_terms: list
    summary: dict
    error: Optional[str] = None


class NoveltyAssessmentResponse(BaseModel):
    """Response for novelty assessment."""
    success: bool
    risk: str
    risk_score: float
    confidence: str
    prior_art_matches: list
    novel_aspects: list
    overlapping_aspects: list
    summary: str
    recommendations: list
    error: Optional[str] = None


class SummaryResponse(BaseModel):
    """Response for structured summary."""
    success: bool
    existing_work: str
    user_contribution: str
    differentiation: str
    uncertainty: str
    key_innovations: list
    confidence_level: str
    error: Optional[str] = None


class RefinementRequest(BaseModel):
    """Request for draft refinement."""
    text: str
    focus_areas: Optional[List[str]] = None
    change_level: Optional[str] = "moderate"


class RefinementResponse(BaseModel):
    """Response for draft refinement."""
    success: bool
    original_text: str
    refined_text: str
    changes: list
    change_summary: dict
    preserved_claims: list
    confidence: str
    warnings: list
    error: Optional[str] = None


# ==================== Document Processing ====================

@router.post("/document/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_optional_user)
):
    """
    Upload and process a document (PDF, DOCX, or TXT).
    
    Extracts text while preserving structure and technical terminology.
    """
    processor = DocumentProcessor()
    
    # Read file content
    content = await file.read()
    
    # Process document
    result = processor.process_document(
        content=content,
        filename=file.filename,
        content_type=file.content_type
    )
    
    if not result.success:
        # Emit crash log
        crash_log = processor.emit_crash_log("document_upload", result)
        return {
            "success": False,
            "error_code": result.error_code,
            "error_message": result.error_message,
            "recommendation": crash_log.recommendation,
            "recoverable": crash_log.recoverable
        }
    
    return {
        "success": True,
        "text": result.text,
        "word_count": result.word_count,
        "paragraph_count": result.paragraph_count,
        "sections": result.sections,
        "metadata": result.metadata
    }


@router.post("/document/process-text")
async def process_text(
    input_data: TextInput,
    current_user: User = Depends(get_optional_user)
):
    """
    Process pasted text input.
    """
    processor = DocumentProcessor()
    result = processor.process_pasted_text(input_data.text)
    
    if not result.success:
        return {
            "success": False,
            "error_code": result.error_code,
            "error_message": result.error_message
        }
    
    return {
        "success": True,
        "text": result.text,
        "word_count": result.word_count,
        "paragraph_count": result.paragraph_count,
        "metadata": result.metadata
    }


# ==================== Concept Extraction ====================

@router.post("/concepts/extract", response_model=ConceptExtractionResponse)
async def extract_concepts(
    input_data: TextInput,
    current_user: User = Depends(get_optional_user)
):
    """
    Extract keywords and concepts from text.
    
    Uses deterministic + SLM-assisted extraction.
    Distinguishes common domain terms from differentiating terms.
    """
    extractor = ConceptExtractor()
    
    result = await extractor.extract_concepts(
        text=input_data.text,
        use_slm=True,
        domain_context=input_data.project_type
    )
    
    if not result.success:
        return ConceptExtractionResponse(
            success=False,
            concepts=[],
            differentiating_terms=[],
            common_terms=[],
            summary={},
            error=result.error_message
        )
    
    # Convert concepts to serializable format
    concepts = [
        {
            "term": c.term,
            "category": c.category.value,
            "frequency": c.frequency,
            "weight": c.weight,
            "context": c.context
        }
        for c in result.concepts
    ]
    
    return ConceptExtractionResponse(
        success=True,
        concepts=concepts,
        differentiating_terms=result.differentiating_terms,
        common_terms=result.common_terms,
        summary=result.summary
    )


# ==================== Prior Art Comparison ====================

@router.post("/prior-art/compare", response_model=NoveltyAssessmentResponse)
async def compare_prior_art(
    input_data: TextInput,
    current_user: User = Depends(get_optional_user)
):
    """
    Compare idea/document against prior art.
    
    Uses semantic similarity for comparison.
    Returns GREEN/YELLOW/RED risk classification with evidence.
    """
    comparator = PriorArtComparator()
    
    result = await comparator.compare_with_prior_art(
        user_text=input_data.text,
        user_title=input_data.title or "Untitled",
        project_type=input_data.project_type
    )
    
    if not result.success:
        return NoveltyAssessmentResponse(
            success=False,
            risk=NoveltyRisk.UNKNOWN.value,
            risk_score=0.5,
            confidence="low",
            prior_art_matches=[],
            novel_aspects=[],
            overlapping_aspects=[],
            summary="",
            recommendations=[],
            error=result.error_message
        )
    
    # Convert matches to serializable format
    matches = [
        {
            "title": m.title,
            "source": m.source,
            "similarity": m.similarity.value,
            "similarity_score": m.similarity_score,
            "overlap_description": m.overlap_description,
            "overlapping_concepts": m.overlapping_concepts,
            "differentiating_aspects": m.differentiating_aspects,
            "evidence": m.evidence
        }
        for m in result.prior_art_matches
    ]
    
    return NoveltyAssessmentResponse(
        success=True,
        risk=result.risk.value,
        risk_score=result.risk_score,
        confidence=result.confidence,
        prior_art_matches=matches,
        novel_aspects=result.novel_aspects,
        overlapping_aspects=result.overlapping_aspects,
        summary=result.summary,
        recommendations=result.recommendations
    )


@router.post("/prior-art/compare-claims")
async def compare_claims(
    claims: List[str],
    title: Optional[str] = None,
    current_user: User = Depends(get_optional_user)
):
    """
    Clause-level comparison for patent claims.
    """
    comparator = PriorArtComparator()
    
    result = await comparator.compare_claims(
        user_claims=claims,
        project_title=title or "Untitled"
    )
    
    return result


# ==================== Summary Generation ====================

@router.post("/summary/generate", response_model=SummaryResponse)
async def generate_summary(
    input_data: TextInput,
    current_user: User = Depends(get_optional_user)
):
    """
    Generate a structured summary of the idea/document.
    
    Separates: existing work, user contribution, differentiation, uncertainty.
    Evidence-grounded only - no fabricated claims.
    """
    summarizer = ResearchSummarizer()
    
    result = await summarizer.generate_summary(
        user_text=input_data.text,
        user_title=input_data.title or "Untitled",
        project_type=input_data.project_type
    )
    
    if not result.success:
        return SummaryResponse(
            success=False,
            existing_work="",
            user_contribution="",
            differentiation="",
            uncertainty="",
            key_innovations=[],
            confidence_level="low",
            error=result.error_message
        )
    
    return SummaryResponse(
        success=True,
        existing_work=result.existing_work,
        user_contribution=result.user_contribution,
        differentiation=result.differentiation,
        uncertainty=result.uncertainty,
        key_innovations=result.key_innovations,
        confidence_level=result.confidence_level
    )


@router.post("/summary/comparative")
async def generate_comparative_summary(
    text: str,
    title: str,
    compared_works: List[dict],
    current_user: User = Depends(get_optional_user)
):
    """
    Generate a comparative summary against specific prior works.
    """
    summarizer = ResearchSummarizer()
    
    result = await summarizer.generate_comparative_summary(
        user_text=text,
        user_title=title,
        compared_works=compared_works
    )
    
    return result


# ==================== Draft Refinement ====================

@router.post("/refine/draft", response_model=RefinementResponse)
async def refine_draft(
    request: RefinementRequest,
    current_user: User = Depends(get_optional_user)
):
    """
    Refine a user's draft while preserving original intent.
    
    Improves clarity, structure, precision, grammar without:
    - Adding new technical claims
    - Inventing results, data, or citations
    - Exaggerating novelty
    
    Output is non-detectable as AI-generated.
    """
    refiner = DraftRefiner()
    
    # Convert focus areas
    focus_areas = None
    if request.focus_areas:
        try:
            focus_areas = [RefinementType(f) for f in request.focus_areas]
        except ValueError:
            pass
    
    result = await refiner.refine_draft(
        original_text=request.text,
        focus_areas=focus_areas,
        max_change_level=request.change_level
    )
    
    if not result.success:
        return RefinementResponse(
            success=False,
            original_text=request.text,
            refined_text="",
            changes=[],
            change_summary={},
            preserved_claims=[],
            confidence="low",
            warnings=[],
            error=result.error_message
        )
    
    # Convert changes to serializable format
    changes = [
        {
            "type": c.type.value,
            "original": c.original,
            "refined": c.refined,
            "reason": c.reason,
            "location": c.location
        }
        for c in result.changes
    ]
    
    return RefinementResponse(
        success=True,
        original_text=result.original_text,
        refined_text=result.refined_text,
        changes=changes,
        change_summary=result.change_summary,
        preserved_claims=result.preserved_claims,
        confidence=result.confidence,
        warnings=result.warnings
    )


@router.post("/refine/section")
async def refine_section(
    text: str,
    section_type: str,
    improvements: Optional[List[str]] = None,
    current_user: User = Depends(get_optional_user)
):
    """
    Refine a specific section of a document.
    """
    refiner = DraftRefiner()
    
    result = await refiner.refine_section(
        section_text=text,
        section_type=section_type,
        target_improvements=improvements
    )
    
    return result


# ==================== Full Pipeline ====================

@router.post("/analyze/full")
async def full_analysis(
    input_data: TextInput,
    include_refinement: bool = False,
    current_user: User = Depends(get_optional_user)
):
    """
    Run full ANTIGRAVITY analysis pipeline:
    1. Concept extraction
    2. Prior art comparison
    3. Novelty assessment
    4. Summary generation
    5. Optional draft refinement
    """
    results = {
        "success": True,
        "title": input_data.title or "Untitled",
        "project_type": input_data.project_type
    }
    
    # 1. Concept Extraction
    extractor = ConceptExtractor()
    concepts_result = await extractor.extract_concepts(
        text=input_data.text,
        use_slm=True,
        domain_context=input_data.project_type
    )
    results["concepts"] = {
        "success": concepts_result.success,
        "differentiating_terms": concepts_result.differentiating_terms,
        "common_terms": concepts_result.common_terms,
        "summary": concepts_result.summary
    }
    
    # 2. Prior Art Comparison
    comparator = PriorArtComparator()
    prior_art_result = await comparator.compare_with_prior_art(
        user_text=input_data.text,
        user_title=input_data.title or "Untitled",
        project_type=input_data.project_type,
        extracted_concepts=concepts_result.differentiating_terms
    )
    results["novelty"] = {
        "success": prior_art_result.success,
        "risk": prior_art_result.risk.value,
        "risk_score": prior_art_result.risk_score,
        "confidence": prior_art_result.confidence,
        "novel_aspects": prior_art_result.novel_aspects,
        "overlapping_aspects": prior_art_result.overlapping_aspects,
        "recommendations": prior_art_result.recommendations
    }
    
    # 3. Summary Generation
    summarizer = ResearchSummarizer()
    summary_result = await summarizer.generate_summary(
        user_text=input_data.text,
        user_title=input_data.title or "Untitled",
        project_type=input_data.project_type,
        key_concepts=concepts_result.differentiating_terms
    )
    results["summary"] = {
        "success": summary_result.success,
        "existing_work": summary_result.existing_work,
        "user_contribution": summary_result.user_contribution,
        "differentiation": summary_result.differentiation,
        "key_innovations": summary_result.key_innovations
    }
    
    # 4. Optional Refinement
    if include_refinement:
        refiner = DraftRefiner()
        refine_result = await refiner.refine_draft(
            original_text=input_data.text,
            max_change_level="moderate"
        )
        results["refinement"] = {
            "success": refine_result.success,
            "refined_text": refine_result.refined_text if refine_result.success else None,
            "change_count": len(refine_result.changes),
            "warnings": refine_result.warnings
        }
    
    return results
