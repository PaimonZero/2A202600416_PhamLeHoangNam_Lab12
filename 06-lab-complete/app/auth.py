"""
Authentication & Authorization Module

Handles API key verification and JWT token generation/verification.
"""

import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict

import jwt
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

# Configuration
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
BEARER_SCHEME = HTTPBearer(auto_error=False)

SECRET_KEY = os.getenv("JWT_SECRET", "dev-jwt-secret-change-in-production")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 60


# ─────────────────────────────────────────────────────────
# API Key Authentication
# ─────────────────────────────────────────────────────────

def verify_api_key(api_key: Optional[str] = Security(API_KEY_HEADER)) -> str:
    """
    Verify API key from X-API-Key header.
    
    Args:
        api_key: API key from header
    
    Returns:
        str: The API key if valid
    
    Raises:
        HTTPException: 401 if missing, 403 if invalid
    """
    expected_key = os.getenv("AGENT_API_KEY", "demo-key-change-in-production")
    
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Include header: X-API-Key: <your-key>"
        )
    
    if api_key != expected_key:
        logger.warning(f"Invalid API key attempt: {api_key[:10]}...")
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )
    
    logger.debug("API key verified successfully")
    return api_key


# ─────────────────────────────────────────────────────────
# JWT Token Management
# ─────────────────────────────────────────────────────────

def create_token(username: str, role: str = "user") -> Dict[str, str]:
    """
    Create JWT token.
    
    Args:
        username: User identifier
        role: User role (user, admin)
    
    Returns:
        dict: Token info with access_token, token_type, expires_in_minutes
    """
    payload = {
        "sub": username,
        "role": role,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES),
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in_minutes": TOKEN_EXPIRE_MINUTES
    }


def verify_token(credentials: Optional[HTTPAuthorizationCredentials] = Security(BEARER_SCHEME)) -> Dict[str, str]:
    """
    Verify JWT token from Authorization header.
    
    Args:
        credentials: Bearer token credentials
    
    Returns:
        dict: Decoded token payload with username and role
    
    Raises:
        HTTPException: 401 if missing or invalid, 403 if expired
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Include: Authorization: Bearer <token>"
        )
    
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role", "user")
        
        if not username:
            raise HTTPException(
                status_code=403,
                detail="Invalid token: missing username"
            )
        
        logger.debug(f"Token verified for user: {username}")
        return {"username": username, "role": role}
    
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )
    
    except jwt.InvalidTokenError as error:
        logger.warning(f"Invalid token: {error}")
        raise HTTPException(
            status_code=403,
            detail="Invalid token"
        )
