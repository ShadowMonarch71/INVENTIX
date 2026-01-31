"""
Inventix AI - Core Schemas
==========================
ANTIGRAVITY-compliant response schemas.
All outputs must conform to these structures.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from enum import Enum
from datetime import datetime


class ConfidenceLevel(str, Enum):
    """Confidence levels for ANTIGRAVITY outputs."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ErrorType(str, Enum):
    """Error types for crash logs."""
    INPUT_ERROR = "INPUT_ERROR"
    EVIDENCE_MISSING = "EVIDENCE_MISSING"
    SCHEMA_VIOLATION = "SCHEMA_VIOLATION"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    INTERNAL_INCONSISTENCY = "INTERNAL_INCONSISTENCY"
    UNKNOWN_FAILURE = "UNKNOWN_FAILURE"


class FailedStage(str, Enum):
    """Processing stages that can fail."""
    INPUT_VALIDATION = "input_validation"
    RETRIEVAL = "retrieval"
    SIMILARITY = "similarity"
    REASONING = "reasoning"
    VERIFICATION = "verification"
    OUTPUT_GENERATION = "output_generation"


class RecommendedAction(str, Enum):
    """Recommended actions on failure."""
    RETRY_WITH_MORE_EVIDENCE = "retry_with_more_evidence"
    ADJUST_INPUT = "adjust_input"
    HUMAN_REVIEW = "human_review"
    SYSTEM_DEBUG = "system_debug"


class EvidenceState(BaseModel):
    """State of evidence in a request."""
    provided: bool
    retrieved_count: int
    usable: bool


class EvidenceReference(BaseModel):
    """Reference to a piece of evidence."""
    evidence_id: str
    source: str
    content_hash: Optional[str] = None
    timestamp: str


class CrashLog(BaseModel):
    """
    ANTIGRAVITY Crash Log Format.
    
    Emitted when the system cannot proceed safely.
    Crash logs are FIRST-CLASS OUTPUTS, not errors.
    """
    status: Literal["CRASH"] = "CRASH"
    error_type: ErrorType
    error_message: str
    failed_stage: FailedStage
    evidence_state: EvidenceState
    confidence_score: float = Field(0.0, ge=0.0, le=1.0)
    recommended_action: RecommendedAction
    debug_trace: List[str]


class AntigravityResponse(BaseModel):
    """
    Base response schema for all ANTIGRAVITY outputs.
    
    Every successful output MUST include:
    - evidence_references: Array of evidence IDs
    - confidence: low/medium/high
    - scope_disclaimer: What this output does NOT determine
    - observed_overlap: What was directly detected
    - inferred_risk: What was probabilistically derived
    - unknowns: What could not be determined
    """
    evidence_references: List[EvidenceReference]
    confidence: ConfidenceLevel
    scope_disclaimer: str
    observed_overlap: str
    inferred_risk: str
    unknowns: List[str]
    
    class Config:
        use_enum_values = True


class AnalysisRequest(BaseModel):
    """Base analysis request."""
    content: str = Field(..., min_length=1)
    context: Optional[str] = None
    metadata: Optional[dict] = None


class AnalysisResult(AntigravityResponse):
    """Base analysis result."""
    summary: str
    key_points: List[str]
    risk_level: ConfidenceLevel


# Audit log schema
class AuditEntry(BaseModel):
    """Immutable audit log entry."""
    entry_id: str
    timestamp: datetime
    action: str
    input_hash: str
    output_hash: str
    confidence: ConfidenceLevel
    evidence_ids: List[str]
    user_id: Optional[str] = None
    session_id: Optional[str] = None
