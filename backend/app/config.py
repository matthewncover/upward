from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
import os


# Load .env file explicitly
env_file_path = Path(__file__).parent.parent.parent / ".env"
if env_file_path.exists():
    load_dotenv(env_file_path)


class Settings(BaseSettings):
    database_url: str = "sqlite:///./upward_habits.db"
    
    whoop_client_id: Optional[str] = None
    whoop_client_secret: Optional[str] = None
    whoop_redirect_uri: str = "http://localhost:8000/api/auth/whoop/callback"
    
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    notification_email: Optional[str] = None
    
    secret_key: str = "your-secret-key-change-this-in-production"
    debug: bool = True
    timezone: str = "America/Phoenix"
    
    def __init__(self, **kwargs):
        # Override with environment variables if available
        kwargs.setdefault('whoop_client_id', os.getenv('WHOOP_CLIENT_ID'))
        kwargs.setdefault('whoop_client_secret', os.getenv('WHOOP_CLIENT_SECRET'))
        kwargs.setdefault('whoop_redirect_uri', os.getenv('WHOOP_REDIRECT_URI', 'http://localhost:8000/api/auth/whoop/callback'))
        
        # Remove None values
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        super().__init__(**kwargs)
    
    class Config:
        env_file = str(env_file_path)


settings = Settings()