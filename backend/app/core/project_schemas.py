"""
Inventix AI - Project Schemas
=============================
Pydantic models for Projects, Roadmaps, and Pipeline Status.
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from enum import Enum


class ProjectType(str, Enum):
    """Project type enumeration."""
    PATENT = "patent"
    RESEARCH = "research"


class NoveltyStatus(str, Enum):
    """Novelty status indicator."""
    RED = "red"      # High risk / Low novelty
    YELLOW = "yellow"  # Medium risk / Uncertain
    GREEN = "green"   # Low risk / High novelty
    UNKNOWN = "unknown"


class PipelineStage(str, Enum):
    """Pipeline processing stages."""
    IDLE = "idle"
    INGESTING = "ingesting"
    EXTRACTING = "extracting"
    ANALYZING = "analyzing"
    VALIDATING = "validating"
    COMPLETE = "complete"
    ERROR = "error"


# ==================== User Models ====================

class UserBase(BaseModel):
    """Base user model."""
    email: str
    name: str
    picture: Optional[str] = None


class UserCreate(UserBase):
    """User creation model."""
    google_id: str


class User(UserBase):
    """User model with ID."""
    id: str
    google_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True


class UserInDB(User):
    """User stored in database."""
    pass


# ==================== Project Models ====================

class ProjectBase(BaseModel):
    """Base project model."""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    project_type: ProjectType


class ProjectCreate(ProjectBase):
    """Project creation request."""
    document_text: Optional[str] = None


class ProjectUpdate(BaseModel):
    """Project update request."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1, max_length=2000)
    document_text: Optional[str] = None


class PriorArtMatch(BaseModel):
    """Prior art match result."""
    patent_id: Optional[str] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    similarity: Optional[float] = None
    relevance: Optional[float] = None
    overlap_areas: Optional[list[str]] = None


class NovelClaim(BaseModel):
    """A novel claim identified in the analysis."""
    claim: str
    evidence: Optional[str] = None
    confidence: Optional[float] = None


class Recommendation(BaseModel):
    """A recommendation for the project."""
    title: Optional[str] = None
    description: str
    priority: Optional[Literal["high", "medium", "low"]] = None


class ProjectAnalysis(BaseModel):
    """Project analysis results."""
    novelty_score: float = Field(0.5, ge=0.0, le=1.0)
    novelty_status: NoveltyStatus = NoveltyStatus.UNKNOWN
    confidence_score: Optional[int] = None
    confidence: str = "low"
    risk_level: Optional[Literal["low", "medium", "high"]] = None
    risk_factors: Optional[list[str]] = None
    risk_summary: Optional[str] = None
    key_concepts: list[str] = []
    potential_overlaps: list[str] = []
    novel_claims: Optional[list] = None  # Can be list of NovelClaim or strings
    prior_art_matches: Optional[list] = None  # Can be list of PriorArtMatch
    recommendations: Optional[list] = None  # Can be list of Recommendation or strings
    summary: Optional[str] = None


class Project(ProjectBase):
    """Full project model."""
    id: str
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_analyzed: Optional[datetime] = None
    document_text: Optional[str] = None
    analysis: Optional[ProjectAnalysis] = None
    pipeline_stage: PipelineStage = PipelineStage.IDLE
    progress: float = Field(0.0, ge=0.0, le=100.0)
    
    class Config:
        from_attributes = True


class ProjectCard(BaseModel):
    """Project card for dashboard display."""
    id: str
    title: str
    project_type: ProjectType
    novelty_status: NoveltyStatus
    progress: float
    last_analyzed: Optional[datetime] = None
    created_at: datetime


class ProjectList(BaseModel):
    """List of project cards."""
    projects: list[ProjectCard]
    total: int


# ==================== Roadmap Models ====================

class RoadmapMilestone(BaseModel):
    """A milestone in the project roadmap."""
    id: str
    title: str
    description: str
    target_date: Optional[datetime] = None
    completed: bool = False
    completed_at: Optional[datetime] = None
    order: int = 0


class RoadmapPhase(BaseModel):
    """A phase containing multiple milestones."""
    id: str
    name: str
    description: str
    milestones: list[RoadmapMilestone] = []
    color: str = "#6366f1"


class Roadmap(BaseModel):
    """Project roadmap."""
    project_id: str
    phases: list[RoadmapPhase] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class RoadmapCreate(BaseModel):
    """Roadmap creation request (auto-generated based on project type)."""
    project_id: str


class MilestoneUpdate(BaseModel):
    """Update a milestone."""
    title: Optional[str] = None
    description: Optional[str] = None
    target_date: Optional[datetime] = None
    completed: Optional[bool] = None


# ==================== Pipeline Status Models ====================

class PipelineNode(BaseModel):
    """A node in the pipeline visualization."""
    id: str
    name: str
    status: Literal["idle", "active", "complete", "error"] = "idle"
    progress: float = 0.0
    message: Optional[str] = None


class PipelineStatus(BaseModel):
    """Real-time pipeline status."""
    project_id: str
    current_stage: PipelineStage
    overall_progress: float = 0.0
    nodes: list[PipelineNode] = []
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


# ==================== Auth Models ====================

class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User


class TokenData(BaseModel):
    """Data extracted from JWT token."""
    user_id: Optional[str] = None
    email: Optional[str] = None


class GoogleAuthRequest(BaseModel):
    """Google OAuth callback request."""
    code: str
    redirect_uri: Optional[str] = None


class GoogleUserInfo(BaseModel):
    """Google user info from OAuth."""
    id: str
    email: str
    name: str
    picture: Optional[str] = None
    verified_email: bool = True
