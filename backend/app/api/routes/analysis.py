"""
Inventix AI - Analysis API Routes
=================================
Core analysis endpoints for idea processing and novelty detection.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from app.services.slm_engine import SLMEngine, SLMRequest
from app.core.schemas import (
    AntigravityResponse,
    CrashLog,
    ConfidenceLevel,
    EvidenceReference
)

router = APIRouter()
slm_engine = SLMEngine()


class IdeaInput(BaseModel):
    """Input schema for idea analysis."""
    idea_text: str = Field(..., min_length=10, description="The idea to analyze")
    domain: Optional[str] = Field(None, description="Technology domain")
    context: Optional[str] = Field(None, description="Additional context")


class NoveltyScore(BaseModel):
    """Novelty scoring output."""
    overall_score: float = Field(..., ge=0.0, le=1.0)
    semantic_uniqueness: float = Field(..., ge=0.0, le=1.0)
    domain_coverage: float = Field(..., ge=0.0, le=1.0)
    prior_art_risk: float = Field(..., ge=0.0, le=1.0)


class IdeaAnalysisResponse(AntigravityResponse):
    """Response schema for idea analysis."""
    idea_summary: str
    key_concepts: List[str]
    novelty_indicators: NoveltyScore
    potential_overlaps: List[str]
    recommended_searches: List[str]


@router.post("/idea", response_model=IdeaAnalysisResponse | CrashLog)
async def analyze_idea(input_data: IdeaInput):
    """
    Analyze an idea for novelty indicators.
    
    This endpoint performs:
    1. Input validation
    2. Concept extraction
    3. Initial novelty scoring
    4. Overlap detection (placeholder without prior art DB)
    
    Returns structured analysis with evidence references.
    """
    try:
        # Step 1: Validate input integrity
        if not input_data.idea_text.strip():
            return CrashLog(
                status="CRASH",
                error_type="INPUT_ERROR",
                error_message="Idea text is empty or whitespace only",
                failed_stage="input_validation",
                evidence_state={"provided": False, "retrieved_count": 0, "usable": False},
                confidence_score=0.0,
                recommended_action="adjust_input",
                debug_trace=["Received input", "Validated idea_text", "Found empty content"]
            )
        
        # Step 2: Process through SLM
        prompt = f"""Analyze this innovation idea and extract structured information.

IDEA: {input_data.idea_text}
DOMAIN: {input_data.domain or 'Not specified'}
CONTEXT: {input_data.context or 'None provided'}

You must respond in valid JSON with this exact structure:
{{
    "idea_summary": "A concise 2-3 sentence summary of the core innovation",
    "key_concepts": ["concept1", "concept2", "concept3"],
    "novelty_indicators": {{
        "overall_score": 0.0 to 1.0,
        "semantic_uniqueness": 0.0 to 1.0,
        "domain_coverage": 0.0 to 1.0,
        "prior_art_risk": 0.0 to 1.0
    }},
    "potential_overlaps": ["area1", "area2"],
    "recommended_searches": ["search query 1", "search query 2"]
}}

IMPORTANT: 
- Scores are PROBABILISTIC ESTIMATES, not definitive assessments
- If uncertain, bias scores toward 0.5 (unknown)
- Do not claim patentability or legal conclusions
"""
        
        result = await slm_engine.generate(SLMRequest(
            prompt=prompt,
            system_prompt="You are ANTIGRAVITY, an evidence-locked analysis system. Output only valid JSON. Never invent facts.",
            response_format="json"
        ))
        
        if not result.success:
            return CrashLog(
                status="CRASH",
                error_type="UNKNOWN_FAILURE",
                error_message=f"SLM generation failed: {result.error}",
                failed_stage="reasoning",
                evidence_state={"provided": True, "retrieved_count": 0, "usable": True},
                confidence_score=0.0,
                recommended_action="retry_with_more_evidence",
                debug_trace=["Received input", "Validated input", "Sent to SLM", "SLM failed"]
            )
        
        # Step 3: Parse and validate output
        parsed = result.parsed_json
        
        # Step 4: Construct response with evidence
        evidence_id = f"EVD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-INPUT"
        
        return IdeaAnalysisResponse(
            idea_summary=parsed.get("idea_summary", "Unable to summarize"),
            key_concepts=parsed.get("key_concepts", []),
            novelty_indicators=NoveltyScore(**parsed.get("novelty_indicators", {
                "overall_score": 0.5,
                "semantic_uniqueness": 0.5,
                "domain_coverage": 0.5,
                "prior_art_risk": 0.5
            })),
            potential_overlaps=parsed.get("potential_overlaps", []),
            recommended_searches=parsed.get("recommended_searches", []),
            evidence_references=[EvidenceReference(
                evidence_id=evidence_id,
                source="user_input",
                content_hash=str(hash(input_data.idea_text)),
                timestamp=datetime.utcnow().isoformat()
            )],
            confidence=ConfidenceLevel.MEDIUM,
            scope_disclaimer="This analysis provides probabilistic indicators only. It does not determine patentability, legal status, or commercial viability.",
            observed_overlap="Initial semantic analysis without prior art database comparison",
            inferred_risk="Novelty scores are estimates based on textual analysis only",
            unknowns=["Actual prior art overlap", "Patent claim conflicts", "Market existing solutions"]
        )
        
    except Exception as e:
        return CrashLog(
            status="CRASH",
            error_type="UNKNOWN_FAILURE",
            error_message=str(e),
            failed_stage="output_generation",
            evidence_state={"provided": True, "retrieved_count": 0, "usable": True},
            confidence_score=0.0,
            recommended_action="system_debug",
            debug_trace=["Received input", "Processing failed", str(e)]
        )


@router.get("/status")
async def analysis_status():
    """Get analysis service status."""
    return {
        "service": "analysis",
        "status": "operational",
        "engine": "ANTIGRAVITY",
        "capabilities": [
            "idea_analysis",
            "concept_extraction",
            "novelty_scoring"
        ]
    }
