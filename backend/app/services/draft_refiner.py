"""
Inventix AI - Draft Refiner
============================
Refines user drafts while preserving original intent.
Non-detectable, non-fabricated improvements.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class RefinementType(str, Enum):
    """Types of refinement applied."""
    CLARITY = "clarity"
    STRUCTURE = "structure"
    PRECISION = "precision"
    GRAMMAR = "grammar"
    FLOW = "flow"


@dataclass
class RefinementChange:
    """A single refinement change."""
    type: RefinementType
    original: str
    refined: str
    reason: str
    location: Optional[str] = None  # e.g., "paragraph 2"


@dataclass
class RefinementResult:
    """Result of draft refinement."""
    success: bool
    original_text: str
    refined_text: str
    changes: List[RefinementChange]
    change_summary: Dict[str, int]  # Count by type
    preserved_claims: List[str]  # Original claims that were preserved
    word_count_original: int
    word_count_refined: int
    confidence: str  # low/medium/high
    warnings: List[str]  # Any concerns about the refinement
    error_message: Optional[str] = None


class DraftRefiner:
    """
    ANTIGRAVITY Draft Refiner
    
    Refines user-provided drafts by:
    - Improving clarity
    - Improving structure
    - Improving technical precision
    - Correcting grammar and flow
    
    CRITICAL RULES:
    - Do NOT add new technical claims
    - Do NOT invent results, data, or citations
    - Do NOT exaggerate novelty
    - Preserve the user's original intent
    
    Output must:
    - Remain faithful to source document
    - Be suitable for human review
    - Avoid detectable AI stylistic artifacts
    - Be indistinguishable from careful human editing
    """

    # Patterns that might indicate AI-generated text (to avoid)
    AI_ARTIFACTS = [
        "it is important to note that",
        "it should be noted that",
        "in conclusion",
        "furthermore",
        "moreover",
        "significantly",
        "it is worth mentioning",
        "as previously mentioned",
        "in this context",
        "with respect to",
        "leveraging",
        "paradigm shift",
        "groundbreaking",
        "revolutionary",
        "cutting-edge",
    ]

    def __init__(self):
        self.slm_engine = None

    async def refine_draft(
        self,
        original_text: str,
        focus_areas: Optional[List[RefinementType]] = None,
        preserve_sections: Optional[List[str]] = None,
        max_change_level: str = "moderate"  # "light", "moderate", "thorough"
    ) -> RefinementResult:
        """
        Refine a draft while preserving original intent.
        
        Args:
            original_text: The user's draft text
            focus_areas: Specific areas to focus refinement on
            preserve_sections: Sections that should not be modified
            max_change_level: How aggressive the refinement should be
        
        Returns:
            RefinementResult with refined text and change tracking
        """
        if not original_text or not original_text.strip():
            return self._create_error_result("No text provided for refinement")

        try:
            from app.services.slm_engine import SLMEngine, SLMRequest
            
            engine = SLMEngine()
            
            # Extract original claims to ensure preservation
            original_claims = self._extract_claims(original_text)
            
            focus_hint = ""
            if focus_areas:
                focus_hint = f"\n\nFocus on: {', '.join([f.value for f in focus_areas])}"
            
            preserve_hint = ""
            if preserve_sections:
                preserve_hint = f"\n\nDo NOT modify these sections: {', '.join(preserve_sections)}"

            # Determine change level guidance
            change_guidance = {
                "light": "Make minimal changes. Only fix clear errors and minor awkwardness.",
                "moderate": "Make balanced improvements. Fix errors, improve clarity, but maintain original voice.",
                "thorough": "Comprehensive refinement. Restructure as needed while preserving all claims."
            }.get(max_change_level, "Make balanced improvements.")

            prompt = f"""Refine this academic/technical draft while preserving the original intent.

ORIGINAL DRAFT:
{original_text[:5000]}

CHANGE LEVEL: {change_guidance}
{focus_hint}
{preserve_hint}

Respond in JSON with this exact structure:
{{
    "refined_text": "The complete refined version of the text",
    
    "changes": [
        {{
            "type": "clarity" | "structure" | "precision" | "grammar" | "flow",
            "original": "Original phrase or sentence",
            "refined": "Refined version",
            "reason": "Why this change was made",
            "location": "paragraph 1" or similar
        }}
    ],
    
    "preserved_claims": ["List of key technical/scientific claims that were preserved exactly"],
    
    "confidence": "low" | "medium" | "high",
    
    "warnings": ["Any concerns about the refinement"]
}}

CRITICAL RULES - VIOLATIONS ARE STRICTLY PROHIBITED:
1. NEVER add new technical claims, results, data, or citations
2. NEVER invent or fabricate any information
3. NEVER exaggerate novelty or importance
4. PRESERVE all original technical assertions exactly
5. MAINTAIN the author's original argumentation
6. AVOID these AI-stylistic patterns: {', '.join(self.AI_ARTIFACTS[:5])}
7. The refined text should read like careful human editing
8. When in doubt, make fewer changes rather than more"""

            result = await engine.generate(SLMRequest(
                prompt=prompt,
                system_prompt="You are a careful academic editor. Your role is to improve clarity and fix errors, NOT to change content. Preserve all original claims. Write naturally, avoiding AI patterns.",
                response_format="json"
            ))

            if not result.success or not result.parsed_json:
                return self._create_error_result("Refinement could not be completed")

            parsed = result.parsed_json
            refined_text = parsed.get("refined_text", original_text)
            
            # Validate that claims were preserved
            validation_warnings = self._validate_claim_preservation(
                original_claims, 
                refined_text
            )
            
            # Check for AI artifacts in output
            artifact_warnings = self._check_for_artifacts(refined_text)
            
            # Build changes list
            changes = []
            for change_data in parsed.get("changes", []):
                try:
                    changes.append(RefinementChange(
                        type=RefinementType(change_data.get("type", "clarity")),
                        original=change_data.get("original", ""),
                        refined=change_data.get("refined", ""),
                        reason=change_data.get("reason", ""),
                        location=change_data.get("location")
                    ))
                except ValueError:
                    continue  # Skip invalid refinement types
            
            # Count changes by type
            change_summary = {}
            for change in changes:
                key = change.type.value
                change_summary[key] = change_summary.get(key, 0) + 1
            
            all_warnings = (
                parsed.get("warnings", []) + 
                validation_warnings + 
                artifact_warnings
            )

            return RefinementResult(
                success=True,
                original_text=original_text,
                refined_text=refined_text,
                changes=changes,
                change_summary=change_summary,
                preserved_claims=parsed.get("preserved_claims", []),
                word_count_original=len(original_text.split()),
                word_count_refined=len(refined_text.split()),
                confidence=parsed.get("confidence", "medium"),
                warnings=all_warnings
            )

        except Exception as e:
            return self._create_error_result(f"Refinement failed: {str(e)}")

    def _extract_claims(self, text: str) -> List[str]:
        """Extract key claims/assertions from text."""
        import re
        
        claims = []
        
        # Look for sentences with claim indicators
        claim_patterns = [
            r'we (?:propose|present|introduce|demonstrate|show)\s+[^.]+\.',
            r'(?:our|this)\s+(?:method|approach|system|technique|algorithm)\s+[^.]+\.',
            r'the results (?:show|indicate|demonstrate|suggest)\s+[^.]+\.',
            r'(?:achieved|obtained|measured|observed)\s+[^.]+(?:\d+%?|\d+\.\d+)[^.]*\.',
        ]
        
        for pattern in claim_patterns:
            matches = re.findall(pattern, text.lower())
            claims.extend(matches[:3])  # Limit per pattern
        
        return claims[:10]  # Return top 10 claims

    def _validate_claim_preservation(
        self, 
        original_claims: List[str], 
        refined_text: str
    ) -> List[str]:
        """Check if original claims are preserved in refined text."""
        warnings = []
        refined_lower = refined_text.lower()
        
        for claim in original_claims:
            # Check if key parts of the claim are preserved
            claim_words = set(claim.split())
            significant_words = [w for w in claim_words if len(w) > 4]
            
            present_count = sum(1 for w in significant_words if w in refined_lower)
            
            if len(significant_words) > 0:
                preservation_ratio = present_count / len(significant_words)
                if preservation_ratio < 0.5:
                    warnings.append(
                        f"Possible claim modification detected. Please verify: '{claim[:50]}...'"
                    )
        
        return warnings

    def _check_for_artifacts(self, text: str) -> List[str]:
        """Check for AI-stylistic artifacts in refined text."""
        warnings = []
        text_lower = text.lower()
        
        found_artifacts = []
        for artifact in self.AI_ARTIFACTS:
            if artifact in text_lower:
                found_artifacts.append(artifact)
        
        if found_artifacts:
            warnings.append(
                f"Detected potential AI artifacts: {', '.join(found_artifacts[:3])}. Consider manual review."
            )
        
        return warnings

    def _create_error_result(self, error_msg: str) -> RefinementResult:
        """Create an error result."""
        return RefinementResult(
            success=False,
            original_text="",
            refined_text="",
            changes=[],
            change_summary={},
            preserved_claims=[],
            word_count_original=0,
            word_count_refined=0,
            confidence="low",
            warnings=[],
            error_message=error_msg
        )

    async def refine_section(
        self,
        section_text: str,
        section_type: str,  # "abstract", "introduction", "methodology", etc.
        target_improvements: Optional[List[str]] = None
    ) -> Dict:
        """
        Refine a specific section of a document.
        """
        from app.services.slm_engine import SLMEngine, SLMRequest
        
        engine = SLMEngine()
        
        improvements_hint = ""
        if target_improvements:
            improvements_hint = f"\n\nTarget improvements: {', '.join(target_improvements)}"

        prompt = f"""Refine this {section_type} section:

{section_text}
{improvements_hint}

Respond in JSON:
{{
    "refined": "The refined section text",
    "improvements_made": ["List of specific improvements"],
    "preserved_elements": ["Key elements that were kept unchanged"],
    "suggestions": ["Optional further improvements for human consideration"]
}}

RULES:
- Preserve all factual claims
- Do not add new information
- Improve clarity and flow only
- Write naturally, like a human editor"""

        result = await engine.generate(SLMRequest(
            prompt=prompt,
            system_prompt="You are a careful academic editor refining a specific section.",
            response_format="json"
        ))

        if result.success and result.parsed_json:
            return {
                "success": True,
                **result.parsed_json
            }
        
        return {
            "success": False,
            "error": "Section refinement could not be completed",
            "original": section_text
        }
