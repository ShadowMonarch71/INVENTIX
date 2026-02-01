"""
Inventix AI - Project Routes
============================
Project CRUD and analysis endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from app.core.project_schemas import (
    Project, ProjectCreate, ProjectUpdate, ProjectList,
    Roadmap, PipelineStatus, User
)
from app.services.auth_service import get_current_user
from app.services import project_service

router = APIRouter()


@router.get("", response_model=ProjectList)
async def list_projects(current_user: User = Depends(get_current_user)):
    """Get all projects for the current user."""
    return project_service.get_user_projects(current_user.id)


@router.post("", response_model=Project)
async def create_project(
    data: ProjectCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new project."""
    return project_service.create_project(current_user.id, data)


@router.get("/{project_id}", response_model=Project)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a project by ID."""
    project = project_service.get_project(project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=Project)
async def update_project(
    project_id: str,
    data: ProjectUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a project."""
    project = project_service.update_project(project_id, current_user.id, data)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a project."""
    success = project_service.delete_project(project_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project deleted successfully"}


@router.post("/{project_id}/analyze", response_model=Project)
async def analyze_project(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Analyze a project for novelty indicators."""
    project = await project_service.analyze_project(project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("/{project_id}/pipeline", response_model=PipelineStatus)
async def get_pipeline_status(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get real-time pipeline status for a project."""
    status = project_service.get_pipeline_status(project_id, current_user.id)
    if not status:
        raise HTTPException(status_code=404, detail="Project not found")
    return status


@router.get("/{project_id}/roadmap", response_model=Roadmap)
async def get_roadmap(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get roadmap for a project."""
    roadmap = project_service.get_roadmap(project_id, current_user.id)
    if not roadmap:
        raise HTTPException(status_code=404, detail="Project or roadmap not found")
    return roadmap


@router.patch("/{project_id}/roadmap/{phase_id}/milestones/{milestone_id}")
async def update_milestone(
    project_id: str,
    phase_id: str,
    milestone_id: str,
    completed: bool,
    current_user: User = Depends(get_current_user)
):
    """Update a milestone's completion status."""
    roadmap = project_service.update_milestone(
        project_id, current_user.id, phase_id, milestone_id, completed
    )
    if not roadmap:
        raise HTTPException(status_code=404, detail="Project, phase, or milestone not found")
    return roadmap
