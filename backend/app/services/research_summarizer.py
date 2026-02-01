"""
Inventix AI - Research/Patent Summarizer
=========================================
Auto-generates structured summaries with evidence-grounded analysis.
Separates existing work, user contribution, and uncertainty.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class SummarySection(str, Enum):
    """Sections of a structured summary."""
    EXISTING_WORK = "existing_work"
    USER_CONTRIBUTION = "user_contribution"
    DIFFERENTIATION = "differentiation"
    UNCERTAINTY = "uncertainty"


@dataclass
class StructuredSummary:
    """A structured, evidence-grounded summary."""
    success: bool
    title: str
    
    # Core sections
    existing_work: str  # What already exists in prior art
    user_contribution: str  # What the user's project does differently
    differentiation: str  # Where the contribution lies relative to similar work
    uncertainty: str  # Areas of uncertainty or insufficient evidence
    
    # Supporting elements
    key_innovations: List[str]
    prior_art_context: List[str]
    evidence_citations: List[str]
    confidence_level: str  # low/medium/high
    
    # Metadata
    word_count: int
    is_complete: bool
    error_message: Optional[str] = None


class ResearchSummarizer:
    """
    ANTIGRAVITY Research/Patent Summarizer
    
    Generates structured summaries explaining:
    - What already exists in prior art
    - What the user's project does differently
    - Where the contribution lies relative to similar work
    
    Rules:
    - Evidence-grounded only
    - No fabricated claims
    - Clear separation between existing work, contribution, and uncertainty
    """

    def __init__(self):
        self.slm_engine = None

    async def generate_summary(
        self,
        user_text: str,
        user_title: str,
        project_type: str,  # "patent" or "research"
        prior_art_context: Optional[List[str]] = None,
        key_concepts: Optional[List[str]] = None
    ) -> StructuredSummary:
        """
        Generate a structured summary of the user's work.
        
        Args:
            user_text: The user's document or idea
            user_title: Title of the work
            project_type: "patent" or "research"
            prior_art_context: Known similar works
            key_concepts: Extracted key concepts
        
        Returns:
            StructuredSummary with all sections
        """
        if not user_text or not user_text.strip():
            return self._create_error_summary("No text provided for summarization")

        try:
            from app.services.slm_engine import SLMEngine, SLMRequest
            
            engine = SLMEngine()
            
            type_label = "patent application" if project_type == "patent" else "research proposal"
            
            context_hint = ""
            if prior_art_context:
                context_hint = f"\n\nKnown similar works:\n" + "\n".join(f"- {w}" for w in prior_art_context[:5])
            
            concepts_hint = ""
            if key_concepts:
                concepts_hint = f"\n\nKey concepts: {', '.join(key_concepts[:15])}"

            prompt = f"""Generate a structured summary for this {type_label}.

TITLE: {user_title}

CONTENT:
{user_text[:4000]}
{context_hint}
{concepts_hint}

Respond in JSON with this exact structure:
{{
    "existing_work": "2-3 paragraphs summarizing what already exists in the field. Be specific about related prior art and current state of knowledge.",
    
    "user_contribution": "2-3 paragraphs explaining what this {type_label} contributes. Focus on the novel aspects and specific innovations.",
    
    "differentiation": "1-2 paragraphs explaining WHERE the contribution lies relative to similar work. What gap does it fill? What problem does it solve differently?",
    
    "uncertainty": "1 paragraph noting areas where evidence is insufficient or claims are uncertain. Be honest about limitations.",
    
    "key_innovations": ["Innovation 1", "Innovation 2", "Innovation 3"],
    
    "prior_art_context": ["Related work 1", "Related work 2"],
    
    "evidence_citations": ["Specific text or claim from the document that supports each innovation"],
    
    "confidence_level": "low" | "medium" | "high"
}}

CRITICAL RULES:
1. Do NOT fabricate claims or invent results
2. Only include assertions that can be traced to the provided text
3. Clearly separate facts from interpretations
4. If something is uncertain, say so explicitly
5. Use hedging language appropriately ("appears to", "suggests", "may")
6. This summary is ASSISTIVE, not authoritative"""

            result = await engine.generate(SLMRequest(
                prompt=prompt,
                system_prompt="You are ANTIGRAVITY, generating evidence-grounded research summaries. Never fabricate. Always hedge appropriately. Separate facts from interpretations.",
                response_format="json"
            ))

            if not result.success or not result.parsed_json:
                return self._create_error_summary("Summary generation could not be completed")

            parsed = result.parsed_json
            
            full_text = (
                parsed.get("existing_work", "") + 
                parsed.get("user_contribution", "") + 
                parsed.get("differentiation", "")
            )

            return StructuredSummary(
                success=True,
                title=user_title,
                existing_work=parsed.get("existing_work", "Unable to determine existing work context."),
                user_contribution=parsed.get("user_contribution", "Unable to identify specific contributions."),
                differentiation=parsed.get("differentiation", "Differentiation analysis incomplete."),
                uncertainty=parsed.get("uncertainty", "Uncertainty assessment not available."),
                key_innovations=parsed.get("key_innovations", []),
                prior_art_context=parsed.get("prior_art_context", []),
                evidence_citations=parsed.get("evidence_citations", []),
                confidence_level=parsed.get("confidence_level", "medium"),
                word_count=len(full_text.split()),
                is_complete=True
            )

        except Exception as e:
            return self._create_error_summary(f"Summarization failed: {str(e)}")

    async def generate_comparative_summary(
        self,
        user_text: str,
        user_title: str,
        compared_works: List[Dict]  # List of {"title": str, "summary": str}
    ) -> Dict:
        """
        Generate a summary comparing user's work to specific prior art.
        """
        if not compared_works:
            return {
                "success": False,
                "error": "No works provided for comparison"
            }

        from app.services.slm_engine import SLMEngine, SLMRequest
        
        engine = SLMEngine()
        
        works_text = "\n\n".join([
            f"PRIOR WORK: {w['title']}\n{w.get('summary', 'No summary available')}"
            for w in compared_works[:3]
        ])

        prompt = f"""Compare the user's work against these prior works:

USER'S WORK: {user_title}
{user_text[:2000]}

PRIOR WORKS:
{works_text}

Respond in JSON:
{{
    "comparison_matrix": [
        {{
            "aspect": "Aspect being compared",
            "user_approach": "How user handles this",
            "prior_approaches": ["How prior work 1 handles this", "How prior work 2 handles this"],
            "novelty_indicator": "novel" | "similar" | "unclear"
        }}
    ],
    "unique_to_user": ["What only the user's work has"],
    "unique_to_prior": ["What prior works have that user doesn't"],
    "overlap_areas": ["Where all works overlap"],
    "overall_novelty": "high" | "medium" | "low",
    "recommendation": "What the user should emphasize to differentiate"
}}"""

        result = await engine.generate(SLMRequest(
            prompt=prompt,
            system_prompt="You are ANTIGRAVITY, performing comparative analysis. Be evidence-based and specific.",
            response_format="json"
        ))

        if result.success and result.parsed_json:
            return {
                "success": True,
                **result.parsed_json
            }
        
        return {
            "success": False,
            "error": "Comparative analysis could not be completed"
        }

    def _create_error_summary(self, error_msg: str) -> StructuredSummary:
        """Create an error summary."""
        return StructuredSummary(
            success=False,
            title="",
            existing_work="",
            user_contribution="",
            differentiation="",
            uncertainty="Analysis could not be completed.",
            key_innovations=[],
            prior_art_context=[],
            evidence_citations=[],
            confidence_level="low",
            word_count=0,
            is_complete=False,
            error_message=error_msg
        )
