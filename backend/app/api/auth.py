from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlmodel import Session
from datetime import date, timedelta
from ..database import get_session
from ..utils.whoop_client import WhoopAuth
from ..config import settings

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Simple in-memory storage for tokens (in production, use database)
whoop_tokens = {}


@router.get("/whoop")
async def initiate_whoop_oauth():
    """Initiate WHOOP OAuth flow."""
    if not settings.whoop_client_id:
        raise HTTPException(status_code=500, detail="WHOOP client ID not configured")
    
    auth_url = WhoopAuth.get_authorization_url()
    return {"auth_url": auth_url}


@router.get("/whoop/callback")
async def whoop_oauth_callback(code: str = None, state: str = None, error: str = None, session: Session = Depends(get_session)):
    """Handle WHOOP OAuth callback."""
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
    
    if not code:
        return {
            "error": "No authorization code provided",
            "message": "Please complete the OAuth flow by visiting the authorization URL first",
            "auth_url": f"http://localhost:8000/api/auth/whoop"
        }
    
    # Exchange code for token
    token_data = await WhoopAuth.exchange_code_for_token(code)
    
    if not token_data:
        raise HTTPException(status_code=400, detail="Failed to exchange code for token")
    
    # Store tokens (in production, store in database with user association)
    whoop_tokens["access_token"] = token_data.get("access_token")
    whoop_tokens["refresh_token"] = token_data.get("refresh_token")
    whoop_tokens["expires_in"] = token_data.get("expires_in")
    
    # Redirect to frontend success page
    return RedirectResponse(url="/?whoop_connected=true")


@router.post("/whoop/refresh")
async def refresh_whoop_token():
    """Refresh WHOOP access token."""
    if not whoop_tokens.get("refresh_token"):
        raise HTTPException(status_code=400, detail="No refresh token available")
    
    token_data = await WhoopAuth.refresh_token(whoop_tokens["refresh_token"])
    
    if not token_data:
        raise HTTPException(status_code=400, detail="Failed to refresh token")
    
    # Update stored tokens
    whoop_tokens.update(token_data)
    
    return {"message": "Token refreshed successfully"}


@router.get("/whoop/status")
async def get_whoop_connection_status():
    """Check WHOOP connection status."""
    is_connected = bool(whoop_tokens.get("access_token"))
    
    return {
        "connected": is_connected,
        "has_refresh_token": bool(whoop_tokens.get("refresh_token"))
    }


@router.post("/whoop/test-tokens")
async def set_test_tokens():
    """Set test tokens for testing refresh functionality. Remove in production."""
    whoop_tokens["access_token"] = "test_access_token_123"
    whoop_tokens["refresh_token"] = "test_refresh_token_456" 
    whoop_tokens["expires_in"] = 3600
    
    return {"message": "Test tokens set successfully"}