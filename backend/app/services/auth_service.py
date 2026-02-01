"""
Inventix AI - Authentication Service
====================================
Google OAuth and JWT token management.
"""

import httpx
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uuid
import json
from pathlib import Path

from app.config import settings
from app.core.project_schemas import User, UserCreate, TokenData, GoogleUserInfo

# Security scheme
security = HTTPBearer(auto_error=False)

# Simple file-based user storage for MVP
DATA_DIR = Path(__file__).parent.parent.parent / "data"
USERS_FILE = DATA_DIR / "users.json"


def _ensure_data_dir():
    """Ensure data directory exists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not USERS_FILE.exists():
        USERS_FILE.write_text("{}")


def _load_users() -> dict:
    """Load users from file."""
    _ensure_data_dir()
    try:
        return json.loads(USERS_FILE.read_text())
    except Exception:
        return {}


def _save_users(users: dict):
    """Save users to file."""
    _ensure_data_dir()
    USERS_FILE.write_text(json.dumps(users, indent=2, default=str))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.secret_key, 
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def verify_token(token: str) -> Optional[TokenData]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(
            token, 
            settings.secret_key, 
            algorithms=[settings.jwt_algorithm]
        )
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        if user_id is None:
            return None
        return TokenData(user_id=user_id, email=email)
    except JWTError:
        return None


async def get_google_user_info(access_token: str) -> GoogleUserInfo:
    """Fetch user info from Google using access token."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=401,
                detail="Failed to get user info from Google"
            )
        
        data = response.json()
        return GoogleUserInfo(
            id=data["id"],
            email=data["email"],
            name=data.get("name", data["email"].split("@")[0]),
            picture=data.get("picture"),
            verified_email=data.get("verified_email", True)
        )


async def exchange_code_for_token(code: str, redirect_uri: str) -> str:
    """Exchange authorization code for access token."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code"
            }
        )
        
        if response.status_code != 200:
            error_detail = response.json().get("error_description", "Token exchange failed")
            raise HTTPException(
                status_code=401,
                detail=f"Failed to exchange code: {error_detail}"
            )
        
        return response.json()["access_token"]


def get_or_create_user(google_info: GoogleUserInfo) -> User:
    """Get existing user or create new one."""
    users = _load_users()
    
    # Check if user exists by google_id
    for user_id, user_data in users.items():
        if user_data.get("google_id") == google_info.id:
            return User(**user_data)
    
    # Create new user
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        google_id=google_info.id,
        email=google_info.email,
        name=google_info.name,
        picture=google_info.picture,
        created_at=datetime.utcnow()
    )
    
    users[user_id] = user.model_dump()
    _save_users(users)
    
    return user


def get_user_by_id(user_id: str) -> Optional[User]:
    """Get user by ID."""
    users = _load_users()
    user_data = users.get(user_id)
    if user_data:
        return User(**user_data)
    return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> User:
    """Get current authenticated user from JWT token."""
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = credentials.credentials
    token_data = verify_token(token)
    
    if token_data is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user = get_user_by_id(token_data.user_id)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> Optional[User]:
    """Get current user if authenticated, None otherwise."""
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


def get_google_auth_url() -> str:
    """Generate Google OAuth authorization URL."""
    from urllib.parse import urlencode
    
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent"
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
