import httpx
from datetime import date, timedelta
from typing import Optional, Dict, Any
from ..config import settings


class WhoopClient:
    """WHOOP API client for fetching biometric data."""
    
    BASE_URL = "https://api.prod.whoop.com/developer"
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    async def get_user_profile(self) -> Optional[Dict[str, Any]]:
        """Get user profile information. Note: requires read:profile scope which we don't have."""
        print("User profile endpoint requires read:profile scope which is not configured")
        return {"message": "Profile data unavailable - requires read:profile scope"}
    
    async def get_recovery_data(self, start_date: date, end_date: date) -> Optional[Dict[str, Any]]:
        """Get recovery data for a date range."""
        try:
            # v2 API expects datetime format with timezone
            params = {
                "start": f"{start_date.isoformat()}T00:00:00.000Z",
                "end": f"{end_date.isoformat()}T23:59:59.999Z"
            }
            
            async with httpx.AsyncClient() as client:
                # Use v2 recovery endpoint from OpenAPI spec
                response = await client.get(
                    f"{self.BASE_URL}/v2/recovery",
                    headers=self.headers,
                    params=params
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error fetching recovery data: {str(e)}")
            # Try to get more detailed error info
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"Response body: {e.response.text}")
            return None
    
    async def get_sleep_data(self, start_date: date, end_date: date) -> Optional[Dict[str, Any]]:
        """Get sleep data for a date range."""
        try:
            # v2 API expects datetime format with timezone
            params = {
                "start": f"{start_date.isoformat()}T00:00:00.000Z",
                "end": f"{end_date.isoformat()}T23:59:59.999Z"
            }
            
            async with httpx.AsyncClient() as client:
                # Use v2 sleep endpoint from OpenAPI spec
                response = await client.get(
                    f"{self.BASE_URL}/v2/activity/sleep",
                    headers=self.headers,
                    params=params
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error fetching sleep data: {str(e)}")
            return None
    
    async def get_hrv_data(self, start_date: date, end_date: date) -> Optional[Dict[str, Any]]:
        """Get HRV data for a date range. In v2 API, HRV is part of recovery data."""
        # HRV data is now included in the recovery endpoint as hrv_rmssd_milli
        return await self.get_recovery_data(start_date, end_date)


class WhoopAuth:
    """WHOOP OAuth authentication handler."""
    
    AUTH_URL = "https://api.prod.whoop.com/oauth"
    
    @staticmethod
    def get_authorization_url() -> str:
        """Get WHOOP OAuth authorization URL."""
        from urllib.parse import urlencode
        import secrets
        
        # Generate a random state for CSRF protection
        state = secrets.token_urlsafe(32)
        
        params = {
            "client_id": settings.whoop_client_id,
            "redirect_uri": settings.whoop_redirect_uri,
            "response_type": "code",
            "scope": "read:recovery read:cycles read:sleep read:workout",
            "state": state
        }
        
        param_string = urlencode(params)
        return f"{WhoopAuth.AUTH_URL}/oauth2/auth?{param_string}"
    
    @staticmethod
    async def exchange_code_for_token(code: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for access token."""
        try:
            data = {
                "client_id": settings.whoop_client_id,
                "client_secret": settings.whoop_client_secret,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.whoop_redirect_uri
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{WhoopAuth.AUTH_URL}/oauth2/token",
                    data=data
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error exchanging code for token: {str(e)}")
            return None
    
    @staticmethod
    async def refresh_token(refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh access token using refresh token."""
        try:
            data = {
                "client_id": settings.whoop_client_id,
                "client_secret": settings.whoop_client_secret,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{WhoopAuth.AUTH_URL}/oauth2/token",
                    data=data
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error refreshing token: {str(e)}")
            return None