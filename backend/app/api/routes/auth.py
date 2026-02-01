"""
Inventix AI - Authentication Routes
===================================
Google OAuth endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import timedelta

from app.config import settings
from app.core.project_schemas import Token, GoogleAuthRequest, User
from app.services.auth_service import (
    exchange_code_for_token,
    get_google_user_info,
    get_or_create_user,
    create_access_token,
    get_current_user,
    get_google_auth_url
)

router = APIRouter()


@router.get("/google/url")
async def get_google_oauth_url():
    """Get Google OAuth authorization URL."""
    return {
        "url": get_google_auth_url(),
        "client_id": settings.google_client_id
    }


@router.post("/google/callback", response_model=Token)
async def google_auth_callback(request: GoogleAuthRequest):
    """
    Exchange Google authorization code for JWT token.
    
    This endpoint receives the authorization code from the frontend
    after the user completes Google OAuth, exchanges it for an access token,
    fetches user info, creates/retrieves the user, and returns a JWT.
    """
    try:
        # Use provided redirect_uri or default
        redirect_uri = request.redirect_uri or settings.google_redirect_uri
        
        # Exchange code for Google access token
        google_access_token = await exchange_code_for_token(request.code, redirect_uri)
        
        # Get user info from Google
        google_user = await get_google_user_info(google_access_token)
        
        # Get or create user in our system
        user = get_or_create_user(google_user)
        
        # Create JWT token
        access_token = create_access_token(
            data={"sub": user.id, "email": user.email},
            expires_delta=timedelta(minutes=settings.jwt_expire_minutes)
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.jwt_expire_minutes * 60,
            user=user
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Authentication failed: {str(e)}"
        )


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user info."""
    return current_user


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout endpoint.
    
    Note: Since we use stateless JWT tokens, the actual token invalidation
    happens on the client side by removing the token.
    """
    return {"message": "Logged out successfully"}


@router.get("/verify")
async def verify_token_endpoint(current_user: User = Depends(get_current_user)):
    """Verify if the current token is valid."""
    return {
        "valid": True,
        "user_id": current_user.id,
        "email": current_user.email
    }
