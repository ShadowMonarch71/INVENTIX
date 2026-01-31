"""
Inventix AI - Knowledge Graph API Routes
========================================
Knowledge graph construction using AI-powered concept extraction.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from app.services.slm_engine import slm_engine, SLMRequest
from app.core.schemas import CrashLog

router = APIRouter()


class ConceptNode(BaseModel):
    """Knowledge graph node."""
    id: str
    label: str
    type: str  # concept, technology, method, application, challenge
    importance: str  # HIGH, MEDIUM, LOW


class ConceptEdge(BaseModel):
    """Knowledge graph edge."""
    source: str
    target: str
    relationship: str
    strength: str  # STRONG, MODERATE, WEAK


class KnowledgeGraphInput(BaseModel):
    """Input for knowledge graph generation."""
    topic: str = Field(..., min_length=10, description="Topic to build graph for")
    domain: Optional[str] = Field(None, description="Technology domain")
    depth: str = Field("medium", description="Graph depth: shallow, medium, deep")


class KnowledgeGraphResponse(BaseModel):
    """Knowledge graph response."""
    topic_summary: str
    nodes: List[ConceptNode]
    edges: List[ConceptEdge]
    central_concept: str
    clusters: List[dict]
    confidence: str
    scope_disclaimer: str
    unknowns: List[str]


@router.post("/generate", response_model=KnowledgeGraphResponse | CrashLog)
async def generate_knowledge_graph(input_data: KnowledgeGraphInput):
    """
    Generate a knowledge graph from a topic using AI.
    
    This endpoint:
    - Extracts key concepts from the topic
    - Identifies relationships between concepts
    - Creates a structured graph representation
    """
    try:
        # Validate input
        if not input_data.topic or len(input_data.topic.strip()) < 10:
            return CrashLog(
                status="CRASH",
                error_type="INSUFFICIENT_INPUT",
                error_message="Topic must be at least 10 characters",
                failed_stage="validation",
                recommended_action="provide_more_detail"
            )

        # Determine node count based on depth
        node_counts = {"shallow": 6, "medium": 10, "deep": 15}
        max_nodes = node_counts.get(input_data.depth, 10)

        # Build the analysis prompt
        system_prompt = """You are ANTIGRAVITY, an evidence-locked knowledge extraction system.
Your task is to extract concepts and relationships to build a knowledge graph.

RULES:
- Extract meaningful, distinct concepts
- Identify clear relationships between concepts
- Use consistent node types and relationship names
- Output valid JSON only"""

        analysis_prompt = f"""Analyze this topic and extract concepts for a knowledge graph.

TOPIC: {input_data.topic}
DOMAIN: {input_data.domain or 'General'}
DEPTH: {input_data.depth} (generate approximately {max_nodes} nodes)

Provide a JSON response with this EXACT structure:
{{
    "topic_summary": "Brief summary of the topic (1-2 sentences)",
    "central_concept": "The main concept this graph is about",
    "nodes": [
        {{"id": "node1", "label": "Concept Name", "type": "concept|technology|method|application|challenge", "importance": "HIGH|MEDIUM|LOW"}},
        {{"id": "node2", "label": "Another Concept", "type": "technology", "importance": "HIGH|MEDIUM|LOW"}}
    ],
    "edges": [
        {{"source": "node1", "target": "node2", "relationship": "uses|enables|requires|improves|challenges|relates_to", "strength": "STRONG|MODERATE|WEAK"}},
        {{"source": "node2", "target": "node3", "relationship": "enables", "strength": "STRONG|MODERATE|WEAK"}}
    ],
    "clusters": [
        {{"name": "Cluster Name", "nodes": ["node1", "node2"], "description": "What this cluster represents"}}
    ]
}}

Important:
- Generate {max_nodes} distinct nodes
- Each node must have a unique id (use node1, node2, etc.)
- Create edges that connect related nodes
- The central_concept should be one of the node labels
- Group related nodes into 2-4 clusters

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

        # Parse response
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
        nodes = [
            ConceptNode(
                id=n.get("id", f"node{i}"),
                label=n.get("label", "Unknown"),
                type=n.get("type", "concept"),
                importance=n.get("importance", "MEDIUM")
            )
            for i, n in enumerate(parsed.get("nodes", []))
        ]

        edges = [
            ConceptEdge(
                source=e.get("source", ""),
                target=e.get("target", ""),
                relationship=e.get("relationship", "relates_to"),
                strength=e.get("strength", "MODERATE")
            )
            for e in parsed.get("edges", [])
            if e.get("source") and e.get("target")
        ]

        return KnowledgeGraphResponse(
            topic_summary=parsed.get("topic_summary", "Knowledge graph generated"),
            nodes=nodes,
            edges=edges,
            central_concept=parsed.get("central_concept", nodes[0].label if nodes else ""),
            clusters=parsed.get("clusters", []),
            confidence="medium",
            scope_disclaimer="This knowledge graph is AI-generated and represents a conceptual model. Relationships and importance levels are estimates based on general knowledge. Verify with domain experts for critical applications.",
            unknowns=[
                "Actual research paper connections not available",
                "Citation-based relationship strength not calculated",
                "Temporal evolution of concepts not shown"
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
async def knowledge_status():
    """Get knowledge graph service status."""
    return {
        "service": "knowledge_graph",
        "status": "active",
        "capabilities": [
            "concept_extraction",
            "relationship_mapping",
            "cluster_detection",
            "graph_visualization"
        ],
        "model": "gemini-flash-latest"
    }
