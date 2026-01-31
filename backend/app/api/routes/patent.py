"""
Inventix AI - Patent Intelligence API Routes
============================================
Patent analysis, novelty scanning, and claim comparison.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from app.services.slm_engine import SLMEngine, SLMRequest
from app.core.schemas import CrashLog, AntigravityResponse, ConfidenceLevel, EvidenceReference

router = APIRouter()
slm_engine = SLMEngine()


class ClaimInput(BaseModel):
    """Patent claim input for analysis."""
    claim_text: str = Field(..., min_length=20)
    claim_type: str = Field("independent", pattern="^(independent|dependent)$")
    domain: Optional[str] = None


class ClaimAnalysisResult(BaseModel):
    """Claim analysis output."""
    claim_elements: List[str]
    scope_assessment: str
    potential_issues: List[str]
    clarity_score: float
    specificity_score: float


class PatentRiskIndicators(BaseModel):
    """Patent risk scoring."""
    novelty_risk: float = Field(..., ge=0.0, le=1.0)
    scope_risk: float = Field(..., ge=0.0, le=1.0)
    clarity_risk: float = Field(..., ge=0.0, le=1.0)
    prior_art_risk: float = Field(..., ge=0.0, le=1.0)
    overall_risk: float = Field(..., ge=0.0, le=1.0)


@router.post("/analyze-claim")
async def analyze_claim(claim: ClaimInput):
    """
    Analyze a patent claim for structure and potential issues.
    
    This does NOT assess patentability.
    This provides structural and clarity indicators only.
    """
    try:
        prompt = f"""Analyze this patent claim for structural elements and clarity.

CLAIM TEXT: {claim.claim_text}
CLAIM TYPE: {claim.claim_type}
DOMAIN: {claim.domain or 'Not specified'}

Respond in valid JSON:
{{
    "claim_elements": ["element1", "element2"],
    "scope_assessment": "broad/narrow/moderate assessment with reasoning",
    "potential_issues": ["issue1", "issue2"],
    "clarity_score": 0.0 to 1.0,
    "specificity_score": 0.0 to 1.0
}}

RULES:
- Do NOT assess patentability
- Do NOT provide legal advice
- Focus on structural analysis only
- If uncertain, use 0.5 for scores
"""
        
        result = await slm_engine.generate(SLMRequest(
            prompt=prompt,
            system_prompt="You are ANTIGRAVITY. Analyze patent claim structure only. Never assess patentability. Output JSON only.",
            response_format="json"
        ))
        
        if not result.success:
            return CrashLog(
                status="CRASH",
                error_type="UNKNOWN_FAILURE",
                error_message=f"Claim analysis failed: {result.error}",
                failed_stage="reasoning",
                evidence_state={"provided": True, "retrieved_count": 0, "usable": True},
                confidence_score=0.0,
                recommended_action="retry_with_more_evidence",
                debug_trace=["Received claim", "Sent to SLM", "Failed"]
            )
        
        parsed = result.parsed_json
        evidence_id = f"EVD-CLAIM-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        return {
            "analysis": ClaimAnalysisResult(**parsed),
            "evidence_references": [{
                "evidence_id": evidence_id,
                "source": "user_input",
                "timestamp": datetime.utcnow().isoformat()
            }],
            "confidence": "medium",
            "scope_disclaimer": "This analysis examines claim structure only. It does NOT determine patentability, validity, or enforceability. Consult a patent attorney for legal assessment."
        }
        
    except Exception as e:
        return CrashLog(
            status="CRASH",
            error_type="UNKNOWN_FAILURE",
            error_message=str(e),
            failed_stage="output_generation",
            evidence_state={"provided": True, "retrieved_count": 0, "usable": True},
            confidence_score=0.0,
            recommended_action="system_debug",
            debug_trace=["Processing error", str(e)]
        )


@router.post("/risk-scan")
async def scan_patent_risk(claim: ClaimInput):
    """
    Generate risk indicators for a patent claim.
    
    All scores are PROBABILISTIC ESTIMATES.
    This is NOT a patentability assessment.
    """
    try:
        prompt = f"""Generate risk indicators for this patent claim.

CLAIM: {claim.claim_text}

Respond in valid JSON:
{{
    "novelty_risk": 0.0 to 1.0 (higher = more likely to overlap with prior art),
    "scope_risk": 0.0 to 1.0 (higher = scope may be too broad or too narrow),
    "clarity_risk": 0.0 to 1.0 (higher = claim may be unclear),
    "prior_art_risk": 0.0 to 1.0 (higher = estimated overlap with existing patents),
    "overall_risk": 0.0 to 1.0 (weighted average)
}}

IMPORTANT:
- These are ESTIMATES, not legal conclusions
- Without actual prior art search, default prior_art_risk to 0.5
- Bias toward uncertainty (0.5) when unsure
"""
        
        result = await slm_engine.generate(SLMRequest(
            prompt=prompt,
            system_prompt="You are ANTIGRAVITY. Generate probabilistic risk scores. Never claim certainty. Output JSON only.",
            response_format="json"
        ))
        
        if not result.success:
            return CrashLog(
                status="CRASH",
                error_type="UNKNOWN_FAILURE",
                error_message=f"Risk scan failed: {result.error}",
                failed_stage="reasoning",
                evidence_state={"provided": True, "retrieved_count": 0, "usable": True},
                confidence_score=0.0,
                recommended_action="retry_with_more_evidence",
                debug_trace=["Received claim", "Sent to SLM", "Failed"]
            )
        
        parsed = result.parsed_json
        
        return {
            "risk_indicators": PatentRiskIndicators(**parsed),
            "confidence": "low",
            "scope_disclaimer": "Risk scores are probabilistic estimates based on textual analysis only. No actual prior art search was performed. These do NOT constitute legal advice or patentability assessment.",
            "unknowns": [
                "Actual prior art database not queried",
                "Patent examiner interpretation unknown",
                "Claim construction may vary"
            ]
        }
        
    except Exception as e:
        return CrashLog(
            status="CRASH",
            error_type="UNKNOWN_FAILURE",
            error_message=str(e),
            failed_stage="output_generation",
            evidence_state={"provided": True, "retrieved_count": 0, "usable": True},
            confidence_score=0.0,
            recommended_action="system_debug",
            debug_trace=["Processing error", str(e)]
        )


@router.get("/status")
async def patent_status():
    """Get patent intelligence service status."""
    return {
        "service": "patent_intelligence",
        "status": "operational",
        "capabilities": [
            "claim_analysis",
            "risk_scanning",
            "structure_assessment"
        ],
        "limitations": [
            "No prior art database integration",
            "No USPTO/EPO API connection",
            "Probabilistic estimates only"
        ]
    }
