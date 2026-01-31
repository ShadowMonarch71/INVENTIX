"""
Inventix AI - Research API Routes
=================================
Research engine endpoints for literature search and synthesis.
Uses Gemini for AI-powered research analysis.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from app.services.slm_engine import slm_engine, SLMRequest
from app.core.schemas import CrashLog

router = APIRouter()


class ResearchQuery(BaseModel):
    """Research query input."""
    query: str = Field(..., min_length=10, description="Research topic or question")
    domain: Optional[str] = Field(None, description="Technology/scientific domain")
    research_type: str = Field("general", description="Type: general, literature_review, gap_analysis, trend_analysis")


class RelatedTopic(BaseModel):
    """Related research topic."""
    topic: str
    relevance: str
    description: str


class ResearchGap(BaseModel):
    """Identified research gap."""
    gap: str
    opportunity: str
    difficulty: str


class ResearchDirection(BaseModel):
    """Suggested research direction."""
    direction: str
    rationale: str
    potential_impact: str


class ResearchAnalysisResponse(BaseModel):
    """Research analysis response following ANTIGRAVITY format."""
    query_summary: str
    key_concepts: List[str]
    related_topics: List[RelatedTopic]
    research_gaps: List[ResearchGap]  
    suggested_directions: List[ResearchDirection]
    methodology_suggestions: List[str]
    potential_challenges: List[str]
    confidence: str
    scope_disclaimer: str
    unknowns: List[str]


@router.post("/analyze", response_model=ResearchAnalysisResponse | CrashLog)
async def analyze_research(query: ResearchQuery):
    """
    Analyze a research topic using AI.
    
    This endpoint:
    - Analyzes the research query
    - Identifies related topics and concepts
    - Suggests research gaps and opportunities
    - Provides methodology suggestions
    """
    try:
        # Validate input
        if not query.query or len(query.query.strip()) < 10:
            return CrashLog(
                status="CRASH",
                error_type="INSUFFICIENT_INPUT",
                error_message="Research query must be at least 10 characters",
                failed_stage="validation",
                recommended_action="provide_more_detail"
            )

        # Build the analysis prompt
        system_prompt = """You are ANTIGRAVITY, an evidence-locked research intelligence system.
Your task is to analyze research topics and provide structured insights.

RULES:
- Be specific and actionable in suggestions
- Acknowledge limitations and unknowns
- Do not make claims without basis
- Focus on practical research guidance
- Output valid JSON only"""

        analysis_prompt = f"""Analyze this research topic and provide structured research guidance.

RESEARCH QUERY: {query.query}
DOMAIN: {query.domain or 'General'}
ANALYSIS TYPE: {query.research_type}

Provide a JSON response with this EXACT structure:
{{
    "query_summary": "2-3 sentence summary of the research topic",
    "key_concepts": ["concept1", "concept2", "concept3", "concept4", "concept5"],
    "related_topics": [
        {{"topic": "Topic Name", "relevance": "HIGH|MEDIUM|LOW", "description": "Brief description"}},
        {{"topic": "Topic Name 2", "relevance": "HIGH|MEDIUM|LOW", "description": "Brief description"}}
    ],
    "research_gaps": [
        {{"gap": "Identified gap in research", "opportunity": "What could be explored", "difficulty": "HIGH|MEDIUM|LOW"}},
        {{"gap": "Another gap", "opportunity": "What could be explored", "difficulty": "HIGH|MEDIUM|LOW"}}
    ],
    "suggested_directions": [
        {{"direction": "Research direction", "rationale": "Why this is promising", "potential_impact": "HIGH|MEDIUM|LOW"}},
        {{"direction": "Another direction", "rationale": "Why this is promising", "potential_impact": "HIGH|MEDIUM|LOW"}}
    ],
    "methodology_suggestions": [
        "Suggested methodology or approach 1",
        "Suggested methodology or approach 2",
        "Suggested methodology or approach 3"
    ],
    "potential_challenges": [
        "Challenge or limitation 1",
        "Challenge or limitation 2"
    ]
}}

Respond with ONLY valid JSON, no markdown."""

        # Call SLM
        slm_response = await slm_engine.generate(SLMRequest(
            prompt=analysis_prompt,
            system_prompt=system_prompt,
            response_format="json"
        ))

        if not slm_response.success:
            return CrashLog(
                status="CRASH",
                error_type="UNKNOWN_FAILURE",
                error_message=f"SLM generation failed: {slm_response.error}",
                failed_stage="reasoning",
                recommended_action="retry_with_more_evidence"
            )

        # Parse and validate response
        parsed = slm_response.parsed_json
        if not parsed:
            return CrashLog(
                status="CRASH",
                error_type="PARSE_ERROR",
                error_message="Failed to parse SLM response as JSON",
                failed_stage="parsing",
                recommended_action="retry"
            )

        # Build response
        return ResearchAnalysisResponse(
            query_summary=parsed.get("query_summary", "Analysis completed"),
            key_concepts=parsed.get("key_concepts", [])[:8],
            related_topics=[
                RelatedTopic(
                    topic=t.get("topic", ""),
                    relevance=t.get("relevance", "MEDIUM"),
                    description=t.get("description", "")
                )
                for t in parsed.get("related_topics", [])[:5]
            ],
            research_gaps=[
                ResearchGap(
                    gap=g.get("gap", ""),
                    opportunity=g.get("opportunity", ""),
                    difficulty=g.get("difficulty", "MEDIUM")
                )
                for g in parsed.get("research_gaps", [])[:4]
            ],
            suggested_directions=[
                ResearchDirection(
                    direction=d.get("direction", ""),
                    rationale=d.get("rationale", ""),
                    potential_impact=d.get("potential_impact", "MEDIUM")
                )
                for d in parsed.get("suggested_directions", [])[:4]
            ],
            methodology_suggestions=parsed.get("methodology_suggestions", [])[:5],
            potential_challenges=parsed.get("potential_challenges", [])[:4],
            confidence="medium",
            scope_disclaimer="This analysis is AI-generated and provides research guidance only. It does not replace thorough literature review or expert consultation. All suggestions should be verified through actual academic sources.",
            unknowns=[
                "Specific paper citations not available without database integration",
                "Real-time publication data not included",
                "Citation counts and impact factors not available"
            ]
        )

    except Exception as e:
        return CrashLog(
            status="CRASH",
            error_type="UNKNOWN_FAILURE",
            error_message=str(e),
            failed_stage="processing",
            recommended_action="system_debug"
        )


@router.get("/status")
async def research_status():
    """Get research service status."""
    return {
        "service": "research",
        "status": "active",
        "capabilities": [
            "topic_analysis",
            "gap_detection",
            "direction_suggestions",
            "methodology_guidance"
        ],
        "model": "gemini-flash-latest"
    }
