"""
Inventix AI - Project Service
=============================
Project CRUD operations and analysis.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.config import settings
from app.core.project_schemas import (
    Project, ProjectCreate, ProjectUpdate, ProjectCard, ProjectList,
    ProjectAnalysis, ProjectType, NoveltyStatus, PipelineStage,
    Roadmap, RoadmapPhase, RoadmapMilestone, RoadmapCreate,
    PipelineStatus, PipelineNode
)
from app.services.slm_engine import SLMEngine

# Simple file-based storage for MVP
DATA_DIR = Path(__file__).parent.parent.parent / "data"
PROJECTS_FILE = DATA_DIR / "projects.json"
ROADMAPS_FILE = DATA_DIR / "roadmaps.json"


def _ensure_data_dir():
    """Ensure data directory exists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not PROJECTS_FILE.exists():
        PROJECTS_FILE.write_text("{}")
    if not ROADMAPS_FILE.exists():
        ROADMAPS_FILE.write_text("{}")


def _load_projects() -> dict:
    """Load projects from file."""
    _ensure_data_dir()
    try:
        return json.loads(PROJECTS_FILE.read_text())
    except Exception:
        return {}


def _save_projects(projects: dict):
    """Save projects to file."""
    _ensure_data_dir()
    PROJECTS_FILE.write_text(json.dumps(projects, indent=2, default=str))


def _load_roadmaps() -> dict:
    """Load roadmaps from file."""
    _ensure_data_dir()
    try:
        return json.loads(ROADMAPS_FILE.read_text())
    except Exception:
        return {}


def _save_roadmaps(roadmaps: dict):
    """Save roadmaps to file."""
    _ensure_data_dir()
    ROADMAPS_FILE.write_text(json.dumps(roadmaps, indent=2, default=str))


def _novelty_score_to_status(score: float) -> NoveltyStatus:
    """Convert novelty score to status color."""
    if score >= 0.7:
        return NoveltyStatus.GREEN
    elif score >= 0.4:
        return NoveltyStatus.YELLOW
    else:
        return NoveltyStatus.RED


def create_project(user_id: str, data: ProjectCreate) -> Project:
    """Create a new project."""
    projects = _load_projects()
    
    project_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    project = Project(
        id=project_id,
        user_id=user_id,
        title=data.title,
        description=data.description,
        project_type=data.project_type,
        document_text=data.document_text,
        created_at=now,
        updated_at=now,
        pipeline_stage=PipelineStage.IDLE,
        progress=0.0
    )
    
    projects[project_id] = project.model_dump()
    _save_projects(projects)
    
    # Auto-generate roadmap
    _create_default_roadmap(project_id, data.project_type)
    
    return project


def get_project(project_id: str, user_id: str) -> Optional[Project]:
    """Get a project by ID."""
    projects = _load_projects()
    project_data = projects.get(project_id)
    
    if project_data and project_data.get("user_id") == user_id:
        return Project(**project_data)
    return None


def get_user_projects(user_id: str) -> ProjectList:
    """Get all projects for a user."""
    projects = _load_projects()
    user_projects = []
    
    for project_data in projects.values():
        if project_data.get("user_id") == user_id:
            # Create ProjectCard
            analysis = project_data.get("analysis")
            novelty_status = NoveltyStatus.UNKNOWN
            if analysis:
                novelty_status = analysis.get("novelty_status", NoveltyStatus.UNKNOWN)
            
            card = ProjectCard(
                id=project_data["id"],
                title=project_data["title"],
                project_type=project_data["project_type"],
                novelty_status=novelty_status,
                progress=project_data.get("progress", 0.0),
                last_analyzed=project_data.get("last_analyzed"),
                created_at=project_data["created_at"]
            )
            user_projects.append(card)
    
    # Sort by created_at descending
    user_projects.sort(key=lambda x: x.created_at, reverse=True)
    
    return ProjectList(projects=user_projects, total=len(user_projects))


def update_project(project_id: str, user_id: str, data: ProjectUpdate) -> Optional[Project]:
    """Update a project."""
    projects = _load_projects()
    project_data = projects.get(project_id)
    
    if not project_data or project_data.get("user_id") != user_id:
        return None
    
    # Update fields
    if data.title is not None:
        project_data["title"] = data.title
    if data.description is not None:
        project_data["description"] = data.description
    if data.document_text is not None:
        project_data["document_text"] = data.document_text
    
    project_data["updated_at"] = datetime.utcnow().isoformat()
    
    projects[project_id] = project_data
    _save_projects(projects)
    
    return Project(**project_data)


def delete_project(project_id: str, user_id: str) -> bool:
    """Delete a project."""
    projects = _load_projects()
    project_data = projects.get(project_id)
    
    if not project_data or project_data.get("user_id") != user_id:
        return False
    
    del projects[project_id]
    _save_projects(projects)
    
    # Also delete roadmap
    roadmaps = _load_roadmaps()
    if project_id in roadmaps:
        del roadmaps[project_id]
        _save_roadmaps(roadmaps)
    
    return True


async def analyze_project(project_id: str, user_id: str) -> Optional[Project]:
    """Analyze a project and update its novelty indicators."""
    projects = _load_projects()
    project_data = projects.get(project_id)
    
    if not project_data or project_data.get("user_id") != user_id:
        return None
    
    # Update pipeline status
    project_data["pipeline_stage"] = PipelineStage.ANALYZING.value
    project_data["progress"] = 50.0
    projects[project_id] = project_data
    _save_projects(projects)
    
    # Prepare analysis input
    analysis_text = project_data.get("document_text") or project_data.get("description", "")
    project_type = project_data.get("project_type", "research")
    title = project_data.get("title", "")
    
    # Use SLM Engine for comprehensive analysis
    engine = SLMEngine()
    
    # Build comprehensive analysis prompt
    prompt = f"""Analyze this {'patent claim' if project_type == 'patent' else 'research idea'} comprehensively.

TITLE: {title}

{'CLAIM' if project_type == 'patent' else 'IDEA'}: {analysis_text}

You must respond in valid JSON with this exact structure:
{{
    "novelty_score": 0.0 to 1.0,
    "confidence_score": 0 to 100,
    "risk_level": "low" | "medium" | "high",
    "risk_factors": ["risk1", "risk2"],
    "risk_summary": "Brief summary of patent/research risks",
    "key_concepts": ["concept1", "concept2", "concept3"],
    "potential_overlaps": ["overlap area 1", "overlap area 2"],
    "novel_claims": [
        {{"claim": "Description of novel claim 1", "evidence": "Supporting evidence"}},
        {{"claim": "Description of novel claim 2", "evidence": "Supporting evidence"}}
    ],
    "prior_art_matches": [
        {{"title": "Related work title", "similarity": 0 to 100, "summary": "Brief description", "overlap_areas": ["area1"]}},
        {{"title": "Another related work", "similarity": 0 to 100, "summary": "Brief description", "overlap_areas": ["area2"]}}
    ],
    "recommendations": [
        {{"title": "Recommendation title", "description": "Detailed recommendation", "priority": "high" | "medium" | "low"}}
    ],
    "summary": "Comprehensive analysis summary paragraph"
}}

Guidelines:
- novelty_score: Higher means more novel (0.7+ is highly novel, 0.4-0.7 is moderate, below 0.4 has significant overlap)
- novel_claims: Identify 2-4 potentially patentable/publishable unique aspects
- prior_art_matches: List 2-4 related existing works with similarity scores
- recommendations: Provide 2-3 actionable next steps
- IMPORTANT: All scores are PROBABILISTIC ESTIMATES, not legal conclusions"""

    from app.services.slm_engine import SLMRequest
    result = await engine.generate(SLMRequest(
        prompt=prompt,
        system_prompt="You are ANTIGRAVITY, an evidence-locked analysis system. Provide comprehensive, balanced analysis. Output only valid JSON.",
        response_format="json"
    ))
    
    # Parse analysis results
    if not result.success or not result.parsed_json:
        # Default fallback analysis
        analysis_data = {
            "novelty_score": 0.5,
            "novelty_status": NoveltyStatus.YELLOW.value,
            "confidence_score": 50,
            "confidence": "low",
            "risk_level": "medium",
            "risk_factors": ["Unable to complete full analysis"],
            "risk_summary": "Analysis could not be completed fully. Please try again.",
            "key_concepts": [],
            "potential_overlaps": [],
            "novel_claims": [],
            "prior_art_matches": [],
            "recommendations": [
                {"title": "Retry Analysis", "description": "Please try running the analysis again", "priority": "high"}
            ],
            "summary": "The analysis could not be completed. Please ensure your description is detailed enough and try again."
        }
    else:
        parsed = result.parsed_json
        novelty_score = parsed.get("novelty_score", 0.5)
        
        analysis_data = {
            "novelty_score": novelty_score,
            "novelty_status": _novelty_score_to_status(novelty_score).value,
            "confidence_score": parsed.get("confidence_score", 70),
            "confidence": "high" if parsed.get("confidence_score", 70) >= 80 else ("medium" if parsed.get("confidence_score", 70) >= 50 else "low"),
            "risk_level": parsed.get("risk_level", "medium"),
            "risk_factors": parsed.get("risk_factors", []),
            "risk_summary": parsed.get("risk_summary", ""),
            "key_concepts": parsed.get("key_concepts", []),
            "potential_overlaps": parsed.get("potential_overlaps", []),
            "novel_claims": parsed.get("novel_claims", []),
            "prior_art_matches": parsed.get("prior_art_matches", []),
            "recommendations": parsed.get("recommendations", []),
            "summary": parsed.get("summary", "Analysis complete.")
        }
    
    # Update project with analysis
    project_data["analysis"] = analysis_data
    project_data["last_analyzed"] = datetime.utcnow().isoformat()
    project_data["pipeline_stage"] = PipelineStage.COMPLETE.value
    project_data["progress"] = 100.0
    project_data["updated_at"] = datetime.utcnow().isoformat()
    
    projects[project_id] = project_data
    _save_projects(projects)
    
    return Project(**project_data)


def get_pipeline_status(project_id: str, user_id: str) -> Optional[PipelineStatus]:
    """Get real-time pipeline status for a project."""
    projects = _load_projects()
    project_data = projects.get(project_id)
    
    if not project_data or project_data.get("user_id") != user_id:
        return None
    
    stage = PipelineStage(project_data.get("pipeline_stage", "idle"))
    progress = project_data.get("progress", 0.0)
    
    # Define pipeline nodes
    nodes = [
        PipelineNode(
            id="input",
            name="User Input",
            status="complete" if progress > 0 else "idle"
        ),
        PipelineNode(
            id="brain",
            name="AI Brain",
            status="complete" if progress >= 20 else ("active" if progress > 0 else "idle"),
            progress=min(100, progress * 5) if progress < 20 else 100
        ),
        PipelineNode(
            id="agents",
            name="Multi-Agent System",
            status="complete" if progress >= 40 else ("active" if progress >= 20 else "idle"),
            progress=max(0, min(100, (progress - 20) * 5)) if 20 <= progress < 40 else (100 if progress >= 40 else 0)
        ),
        PipelineNode(
            id="knowledge",
            name="Knowledge Graph",
            status="complete" if progress >= 60 else ("active" if progress >= 40 else "idle"),
            progress=max(0, min(100, (progress - 40) * 5)) if 40 <= progress < 60 else (100 if progress >= 60 else 0)
        ),
        PipelineNode(
            id="engine",
            name="Research Engine" if project_data.get("project_type") == "research" else "Patent Engine",
            status="complete" if progress >= 80 else ("active" if progress >= 60 else "idle"),
            progress=max(0, min(100, (progress - 60) * 5)) if 60 <= progress < 80 else (100 if progress >= 80 else 0)
        ),
        PipelineNode(
            id="output",
            name="Output Generator",
            status="complete" if progress >= 100 else ("active" if progress >= 80 else "idle"),
            progress=max(0, min(100, (progress - 80) * 5)) if 80 <= progress < 100 else (100 if progress >= 100 else 0)
        ),
    ]
    
    return PipelineStatus(
        project_id=project_id,
        current_stage=stage,
        overall_progress=progress,
        nodes=nodes
    )


# ==================== Roadmap Functions ====================

def _create_default_roadmap(project_id: str, project_type: ProjectType) -> Roadmap:
    """Create default roadmap based on project type."""
    roadmaps = _load_roadmaps()
    
    if project_type == ProjectType.PATENT:
        phases = [
            RoadmapPhase(
                id=str(uuid.uuid4()),
                name="Discovery",
                description="Initial research and prior art analysis",
                color="#6366f1",
                milestones=[
                    RoadmapMilestone(id=str(uuid.uuid4()), title="Define core invention", description="Clearly articulate the novel aspects", order=0),
                    RoadmapMilestone(id=str(uuid.uuid4()), title="Prior art search", description="Conduct comprehensive prior art analysis", order=1),
                    RoadmapMilestone(id=str(uuid.uuid4()), title="Novelty assessment", description="Evaluate novelty indicators", order=2),
                ]
            ),
            RoadmapPhase(
                id=str(uuid.uuid4()),
                name="Documentation",
                description="Prepare patent application materials",
                color="#8b5cf6",
                milestones=[
                    RoadmapMilestone(id=str(uuid.uuid4()), title="Draft claims", description="Write patent claims", order=0),
                    RoadmapMilestone(id=str(uuid.uuid4()), title="Technical drawings", description="Prepare technical illustrations", order=1),
                    RoadmapMilestone(id=str(uuid.uuid4()), title="Description write-up", description="Complete detailed description", order=2),
                ]
            ),
            RoadmapPhase(
                id=str(uuid.uuid4()),
                name="Filing",
                description="Submit and track application",
                color="#a855f7",
                milestones=[
                    RoadmapMilestone(id=str(uuid.uuid4()), title="Legal review", description="Attorney review and feedback", order=0),
                    RoadmapMilestone(id=str(uuid.uuid4()), title="File application", description="Submit to patent office", order=1),
                    RoadmapMilestone(id=str(uuid.uuid4()), title="Track prosecution", description="Monitor and respond to office actions", order=2),
                ]
            ),
        ]
    else:
        phases = [
            RoadmapPhase(
                id=str(uuid.uuid4()),
                name="Literature Review",
                description="Comprehensive research landscape analysis",
                color="#06b6d4",
                milestones=[
                    RoadmapMilestone(id=str(uuid.uuid4()), title="Define research questions", description="Establish clear research objectives", order=0),
                    RoadmapMilestone(id=str(uuid.uuid4()), title="Literature search", description="Systematic literature review", order=1),
                    RoadmapMilestone(id=str(uuid.uuid4()), title="Gap analysis", description="Identify research gaps", order=2),
                ]
            ),
            RoadmapPhase(
                id=str(uuid.uuid4()),
                name="Methodology",
                description="Design and validate research approach",
                color="#14b8a6",
                milestones=[
                    RoadmapMilestone(id=str(uuid.uuid4()), title="Design methodology", description="Create research methodology", order=0),
                    RoadmapMilestone(id=str(uuid.uuid4()), title="Data collection plan", description="Define data sources and methods", order=1),
                    RoadmapMilestone(id=str(uuid.uuid4()), title="Validation strategy", description="Plan validation approach", order=2),
                ]
            ),
            RoadmapPhase(
                id=str(uuid.uuid4()),
                name="Publication",
                description="Prepare and submit for publication",
                color="#10b981",
                milestones=[
                    RoadmapMilestone(id=str(uuid.uuid4()), title="Draft paper", description="Write research paper", order=0),
                    RoadmapMilestone(id=str(uuid.uuid4()), title="Peer review prep", description="Internal review and refinement", order=1),
                    RoadmapMilestone(id=str(uuid.uuid4()), title="Submit to venue", description="Submit to conference or journal", order=2),
                ]
            ),
        ]
    
    roadmap = Roadmap(
        project_id=project_id,
        phases=phases,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    roadmaps[project_id] = roadmap.model_dump()
    _save_roadmaps(roadmaps)
    
    return roadmap


def get_roadmap(project_id: str, user_id: str) -> Optional[Roadmap]:
    """Get roadmap for a project."""
    # First verify user owns the project
    projects = _load_projects()
    project_data = projects.get(project_id)
    
    if not project_data or project_data.get("user_id") != user_id:
        return None
    
    roadmaps = _load_roadmaps()
    roadmap_data = roadmaps.get(project_id)
    
    if roadmap_data:
        return Roadmap(**roadmap_data)
    
    # Create default if doesn't exist
    return _create_default_roadmap(project_id, ProjectType(project_data["project_type"]))


def update_milestone(
    project_id: str, 
    user_id: str, 
    phase_id: str, 
    milestone_id: str, 
    completed: bool
) -> Optional[Roadmap]:
    """Update a milestone's completion status."""
    # Verify ownership
    projects = _load_projects()
    project_data = projects.get(project_id)
    
    if not project_data or project_data.get("user_id") != user_id:
        return None
    
    roadmaps = _load_roadmaps()
    roadmap_data = roadmaps.get(project_id)
    
    if not roadmap_data:
        return None
    
    # Find and update milestone
    for phase in roadmap_data.get("phases", []):
        if phase["id"] == phase_id:
            for milestone in phase.get("milestones", []):
                if milestone["id"] == milestone_id:
                    milestone["completed"] = completed
                    if completed:
                        milestone["completed_at"] = datetime.utcnow().isoformat()
                    else:
                        milestone["completed_at"] = None
                    break
    
    roadmap_data["updated_at"] = datetime.utcnow().isoformat()
    roadmaps[project_id] = roadmap_data
    _save_roadmaps(roadmaps)
    
    return Roadmap(**roadmap_data)
