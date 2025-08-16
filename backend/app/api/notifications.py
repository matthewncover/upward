from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from datetime import date, timedelta
from ..database import get_session
from ..core.notifications import send_daily_reminder, get_weekly_progress
from ..config import settings

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.post("/test-email")
async def test_email_notification():
    """Test endpoint to send a sample email notification."""
    if not all([settings.smtp_server, settings.smtp_username, settings.smtp_password, settings.notification_email]):
        raise HTTPException(
            status_code=400, 
            detail="Email settings not configured. Please set SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD, and NOTIFICATION_EMAIL environment variables."
        )
    
    try:
        await send_daily_reminder()
        return {"message": "Test email sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")


@router.get("/email-settings")
async def check_email_settings():
    """Check current email notification settings."""
    return {
        "configured": all([settings.smtp_server, settings.smtp_username, settings.smtp_password, settings.notification_email]),
        "smtp_server": settings.smtp_server,
        "smtp_port": settings.smtp_port,
        "smtp_username": settings.smtp_username if settings.smtp_username else None,
        "notification_email": settings.notification_email,
        "missing_settings": [
            setting for setting, value in [
                ("SMTP_SERVER", settings.smtp_server),
                ("SMTP_USERNAME", settings.smtp_username), 
                ("SMTP_PASSWORD", settings.smtp_password),
                ("NOTIFICATION_EMAIL", settings.notification_email)
            ] if not value
        ]
    }


@router.get("/weekly-progress")
async def get_current_weekly_progress(session: Session = Depends(get_session)):
    """Get the current weekly progress for all habits."""
    today = date.today()
    progress = get_weekly_progress(session, today)
    
    return {
        "date": today,
        "week_start": today - timedelta(days=6),
        "progress": progress
    }


@router.post("/schedule")
async def schedule_notifications():
    """Information about scheduling daily notifications."""
    return {
        "message": "To schedule daily notifications, set up a cron job or task scheduler",
        "recommended_time": "8:45 AM MST (15:45 UTC)",
        "cron_expression": "45 15 * * *",
        "example_commands": {
            "unix_cron": "45 15 * * * /usr/bin/python3 -c \"from app.core.notifications import schedule_daily_reminder; schedule_daily_reminder()\"",
            "windows_task": "Create a Windows Task to run the Python script daily at 8:45 AM MST"
        },
        "manual_trigger": "Use POST /api/notifications/test-email to manually trigger"
    }