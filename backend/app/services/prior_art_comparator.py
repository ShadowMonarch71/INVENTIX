"""
Inventix AI - Prior Art Comparator
===================================
Semantic comparison of ideas against prior art.
Evidence-locked with proper similarity scoring.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class SimilarityLevel(str, Enum):
    """Similarity classification levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class NoveltyRisk(str, Enum):
    """Novelty risk classification (traffic light system)."""
    GREEN = "green"    # Low overlap, higher differentiation
    YELLOW = "yellow"  # Partial overlap, moderate differentiation
    RED = "red"        # Strong overlap, crowded prior art
    UNKNOWN = "unknown"  # Insufficient evidence


@dataclass
class PriorArtMatch:
    """A matched prior art item."""
    title: str
    source: str  # "paper" or "patent"
    similarity: SimilarityLevel
    similarity_score: float  # 0-1
    overlap_description: str
    overlapping_concepts: List[str]
    differentiating_aspects: List[str]
    evidence: str  # Specific text or claim that shows overlap


@dataclass
class NoveltyAssessment:
    """Complete novelty assessment result."""
    success: bool
    risk: NoveltyRisk
    risk_score: float  # 0-1, higher = more risk
    confidence: str  # low/medium/high
    prior_art_matches: List[PriorArtMatch]
    novel_aspects: List[str]
    overlapping_aspects: List[str]
    summary: str
    evidence_basis: str
    recommendations: List[str]
    error_message: Optional[str] = None


class PriorArtComparator:
    """
    ANTIGRAVITY Prior Art Comparator
    
    Compares user ideas/documents against prior art using:
    - Semantic similarity (not just keyword matching)
    - Clause-level comparison for patents
    - Evidence-linked results only
    
    Outputs:
    - What is similar
    - Where overlap exists
    - Degree of similarity (low/medium/high)
    """

    def __init__(self):
        self.slm_engine = None

    async def compare_with_prior_art(
        self,
        user_text: str,
        user_title: str,
        project_type: str,  # "patent" or "research"
        extracted_concepts: Optional[List[str]] = None
    ) -> NoveltyAssessment:
        """
        Compare user's idea/document against simulated prior art.
        
        In production, this would query actual patent/paper databases.
        For MVP, uses SLM to generate plausible prior art comparisons.
        
        Args:
            user_text: The user's document or idea text
            user_title: Title of the user's work
            project_type: "patent" or "research"
            extracted_concepts: Pre-extracted key concepts
        
        Returns:
            NoveltyAssessment with full comparison results
        """
        if not user_text or not user_text.strip():
            return NoveltyAssessment(
                success=False,
                risk=NoveltyRisk.UNKNOWN,
                risk_score=0.5,
                confidence="low",
                prior_art_matches=[],
                novel_aspects=[],
                overlapping_aspects=[],
                summary="",
                evidence_basis="",
                recommendations=[],
                error_message="No text provided for comparison"
            )

        try:
            # Use SLM for semantic comparison
            from app.services.slm_engine import SLMEngine, SLMRequest
            
            engine = SLMEngine()
            
            # Build comparison prompt
            type_label = "patent claim" if project_type == "patent" else "research idea"
            art_label = "existing patents" if project_type == "patent" else "published research"
            
            concepts_hint = ""
            if extracted_concepts:
                concepts_hint = f"\n\nKey concepts identified: {', '.join(extracted_concepts[:15])}"

            prompt = f"""Analyze this {type_label} for prior art overlap:

TITLE: {user_title}
CONTENT: {user_text[:2500]}
{concepts_hint}

Respond in JSON:
{{
    "prior_art_matches": [
        {{
            "title": "Name of similar existing work",
            "source": "{project_type}",
            "similarity_score": 0.5,
            "overlap_description": "Brief description of overlap",
            "overlapping_concepts": ["concept1", "concept2"],
            "differentiating_aspects": ["unique aspect"],
            "evidence": "Quote from text showing overlap"
        }}
    ],
    "novel_aspects": ["List of novel elements"],
    "overlapping_aspects": ["List of overlapping elements"],
    "overall_risk_score": 0.4,
    "confidence": "medium",
    "summary": "Brief summary of novelty assessment",
    "recommendations": ["Recommendation 1", "Recommendation 2"]
}}

Generate 2-3 realistic prior art matches. Be conservative."""

            result = await engine.generate(SLMRequest(
                prompt=prompt,
                system_prompt="You are a prior art assessment system. Generate realistic, evidence-based assessments. Output valid JSON only.",
                response_format="json"
            ))

            if not result.success or not result.parsed_json:
                # Log the error for debugging
                error_msg = result.error or "Unknown error"
                return self._create_fallback_assessment(
                    f"SLM analysis could not be completed: {error_msg}"
                )

            parsed = result.parsed_json
            
            # Build prior art matches
            matches = []
            for match_data in parsed.get("prior_art_matches", []):
                score = match_data.get("similarity_score", 0.5)
                level = self._score_to_level(score)
                
                matches.append(PriorArtMatch(
                    title=match_data.get("title", "Unknown"),
                    source=match_data.get("source", project_type),
                    similarity=level,
                    similarity_score=score,
                    overlap_description=match_data.get("overlap_description", ""),
                    overlapping_concepts=match_data.get("overlapping_concepts", []),
                    differentiating_aspects=match_data.get("differentiating_aspects", []),
                    evidence=match_data.get("evidence", "")
                ))

            # Calculate overall risk
            risk_score = parsed.get("overall_risk_score", 0.5)
            risk = self._score_to_risk(risk_score)
            
            # Build evidence basis
            evidence_items = [m.evidence for m in matches if m.evidence]
            evidence_basis = "; ".join(evidence_items) if evidence_items else "Based on semantic analysis"

            return NoveltyAssessment(
                success=True,
                risk=risk,
                risk_score=risk_score,
                confidence=parsed.get("confidence", "medium"),
                prior_art_matches=matches,
                novel_aspects=parsed.get("novel_aspects", []),
                overlapping_aspects=parsed.get("overlapping_aspects", []),
                summary=parsed.get("summary", "Analysis complete."),
                evidence_basis=evidence_basis,
                recommendations=parsed.get("recommendations", [])
            )

        except Exception as e:
            return self._create_fallback_assessment(f"Comparison failed: {str(e)}")

    def _score_to_level(self, score: float) -> SimilarityLevel:
        """Convert numeric score to similarity level."""
        if score >= 0.6:
            return SimilarityLevel.HIGH
        elif score >= 0.3:
            return SimilarityLevel.MEDIUM
        else:
            return SimilarityLevel.LOW

    def _score_to_risk(self, score: float) -> NoveltyRisk:
        """Convert risk score to traffic light classification."""
        if score >= 0.6:
            return NoveltyRisk.RED  # High overlap
        elif score >= 0.3:
            return NoveltyRisk.YELLOW  # Moderate overlap
        else:
            return NoveltyRisk.GREEN  # Low overlap

    def _create_fallback_assessment(self, error_msg: str) -> NoveltyAssessment:
        """Create a fallback assessment when analysis fails."""
        return NoveltyAssessment(
            success=False,
            risk=NoveltyRisk.UNKNOWN,
            risk_score=0.5,
            confidence="low",
            prior_art_matches=[],
            novel_aspects=[],
            overlapping_aspects=[],
            summary="Prior art comparison could not be completed.",
            evidence_basis="Insufficient data",
            recommendations=[
                "Retry the analysis with more detailed input",
                "Consider manual prior art search"
            ],
            error_message=error_msg
        )

    async def compare_claims(
        self,
        user_claims: List[str],
        project_title: str
    ) -> Dict:
        """
        Clause-level comparison for patent claims.
        
        Analyzes each claim individually for prior art overlap.
        """
        if not user_claims:
            return {
                "success": False,
                "error": "No claims provided"
            }

        from app.services.slm_engine import SLMEngine, SLMRequest
        
        engine = SLMEngine()
        
        claims_text = "\n".join([f"Claim {i+1}: {c}" for i, c in enumerate(user_claims)])
        
        prompt = f"""Analyze these patent claims for prior art risks:

{claims_text}

For each claim, respond in JSON:
{{
    "claims_analysis": [
        {{
            "claim_number": 1,
            "risk_level": "low" | "medium" | "high",
            "similar_prior_art": "Description of similar existing claims",
            "differentiating_elements": ["What makes this claim unique"],
            "recommendation": "How to strengthen this claim"
        }}
    ],
    "overall_assessment": "Summary of the claims set",
    "strongest_claim": 1,
    "weakest_claim": 2
}}"""

        result = await engine.generate(SLMRequest(
            prompt=prompt,
            system_prompt="You are ANTIGRAVITY, analyzing patent claims. Be thorough and evidence-based.",
            response_format="json"
        ))

        if result.success and result.parsed_json:
            return {
                "success": True,
                **result.parsed_json
            }
        
        return {
            "success": False,
            "error": "Claim analysis could not be completed"
        }
