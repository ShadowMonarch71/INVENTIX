"""
Inventix AI - API Router
========================
Central router aggregating all API endpoints.
"""

from fastapi import APIRouter

from app.api.routes import analysis, research, patent, knowledge

router = APIRouter()

# Include sub-routers
router.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])
router.include_router(research.router, prefix="/research", tags=["Research"])
router.include_router(patent.router, prefix="/patent", tags=["Patent Intelligence"])
router.include_router(knowledge.router, prefix="/knowledge", tags=["Knowledge Graph"])
