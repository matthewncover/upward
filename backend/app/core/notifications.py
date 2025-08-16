import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date, timedelta
from typing import Optional
import asyncio
from sqlmodel import Session, select
from ..config import settings
from ..models import DailyScore, Habit, WhoopData
from ..database import get_session


def create_daily_reminder_email(yesterday_score: Optional[float], weekly_progress: dict) -> str:
    """
    Create HTML content for daily reminder email.
    """
    html_content = f"""
    <html>
    <body>
        <h2>Daily Habit Check-in</h2>
        <p>Good morning! Time for your daily habit tracking.</p>
        
        <h3>Yesterday's Performance</h3>
        <p>Final Score: {yesterday_score:.2f if yesterday_score else 'No data'}</p>
        
        <h3>This Week's Progress</h3>
        <ul>
    """
    
    for habit_name, progress in weekly_progress.items():
        completion = progress.get('completed_days', 0)
        target = progress.get('target_days', 5)
        html_content += f"<li>{habit_name}: {completion}/{target} days</li>"
    
    html_content += """
        </ul>
        
        <p><a href="http://localhost:8000">Enter Today's Data</a></p>
        
        <p>Keep building those upward habits!</p>
    </body>
    </html>
    """
    
    return html_content


def get_weekly_progress(session: Session, current_date: date) -> dict:
    """
    Get weekly progress for all habits.
    """
    week_start = current_date - timedelta(days=6)
    
    statement = select(Habit).where(Habit.is_active == True)
    habits = session.exec(statement).all()
    
    progress = {}
    
    for habit in habits:
        # Count completed days this week
        from ..models import HabitEntry
        entry_statement = select(HabitEntry).where(
            HabitEntry.habit_id == habit.id,
            HabitEntry.date >= week_start,
            HabitEntry.date <= current_date,
            HabitEntry.value > 0
        )
        completed_entries = session.exec(entry_statement).all()
        
        progress[habit.name] = {
            'completed_days': len(completed_entries),
            'target_days': habit.target_days_per_week
        }
    
    return progress


async def send_daily_reminder():
    """
    Send daily reminder email with yesterday's score and weekly progress.
    """
    if not all([settings.smtp_server, settings.smtp_username, settings.smtp_password, settings.notification_email]):
        print("Email settings not configured, skipping notification")
        return
    
    try:
        # Get data for email
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        with next(get_session()) as session:
            # Get yesterday's score
            score_statement = select(DailyScore).where(DailyScore.date == yesterday)
            yesterday_score_record = session.exec(score_statement).first()
            yesterday_score = yesterday_score_record.final_score if yesterday_score_record else None
            
            # Get weekly progress
            weekly_progress = get_weekly_progress(session, today)
        
        # Create email content
        html_content = create_daily_reminder_email(yesterday_score, weekly_progress)
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Daily Habit Reminder - {today.strftime('%Y-%m-%d')}"
        msg['From'] = settings.smtp_username
        msg['To'] = settings.notification_email
        
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(msg)
        
        print(f"Daily reminder sent successfully to {settings.notification_email}")
        
    except Exception as e:
        print(f"Failed to send daily reminder: {str(e)}")


async def sync_whoop_data():
    """
    Sync the latest WHOOP data from API to database.
    """
    try:
        # Import here to avoid circular imports
        from ..api.auth import whoop_tokens
        from ..utils.whoop_client import WhoopClient
        from ..api.whoop import calculate_whoop_multiplier_from_scores
        
        if not whoop_tokens.get("access_token"):
            print("WHOOP not connected, skipping sync")
            return
        
        client = WhoopClient(whoop_tokens["access_token"])
        
        # Sync last 7 days to catch any updates
        end_date = date.today()
        start_date = end_date - timedelta(days=6)
        
        print(f"Syncing WHOOP data from {start_date} to {end_date}")
        
        # Fetch data from WHOOP API
        recovery_data = await client.get_recovery_data(start_date, end_date)
        sleep_data = await client.get_sleep_data(start_date, end_date)
        
        synced_count = 0
        
        with next(get_session()) as session:
            # Process recovery data
            if recovery_data and "records" in recovery_data:
                for record in recovery_data["records"]:
                    if "created_at" not in record:
                        continue
                    
                    record_date = date.fromisoformat(record["created_at"].split("T")[0])
                    
                    # Extract scores
                    recovery_score = record.get("score", {}).get("recovery_score")
                    hrv_score = record.get("score", {}).get("hrv_rmssd_milli")
                    
                    # Get matching sleep data
                    sleep_score = None
                    if sleep_data and "records" in sleep_data:
                        for sleep_record in sleep_data["records"]:
                            if "start" in sleep_record and sleep_record["start"]:
                                sleep_date = date.fromisoformat(sleep_record["start"].split("T")[0])
                                if sleep_date == record_date:
                                    sleep_score = sleep_record.get("score", {}).get("sleep_performance_percentage")
                                    break
                    
                    # Calculate multiplier
                    whoop_multiplier = calculate_whoop_multiplier_from_scores(
                        sleep_score, hrv_score, recovery_score
                    )
                    
                    # Check if record exists
                    existing_statement = select(WhoopData).where(WhoopData.date == record_date)
                    existing = session.exec(existing_statement).first()
                    
                    if existing:
                        # Update existing record
                        existing.sleep_score = sleep_score
                        existing.hrv_score = hrv_score
                        existing.recovery_score = recovery_score
                        existing.whoop_multiplier = whoop_multiplier
                        print(f"Updated WHOOP data for {record_date}")
                    else:
                        # Create new record
                        whoop_record = WhoopData(
                            date=record_date,
                            sleep_score=sleep_score,
                            hrv_score=hrv_score,
                            recovery_score=recovery_score,
                            whoop_multiplier=whoop_multiplier
                        )
                        session.add(whoop_record)
                        print(f"Added new WHOOP data for {record_date}")
                    
                    synced_count += 1
            
            session.commit()
        
        print(f"WHOOP sync completed: {synced_count} records processed")
        
    except Exception as e:
        print(f"Failed to sync WHOOP data: {str(e)}")


def schedule_daily_reminder():
    """
    Schedule daily reminder to be sent at 8:45 AM MST.
    This would typically be called by a task scheduler or cron job.
    """
    asyncio.run(send_daily_reminder())


def schedule_daily_tasks():
    """
    Run all daily scheduled tasks: WHOOP sync and habit reminder.
    This would typically be called by a task scheduler or cron job.
    """
    asyncio.run(run_daily_tasks())


async def run_daily_tasks():
    """
    Run both WHOOP sync and daily reminder.
    """
    print("Starting daily scheduled tasks...")
    
    # Sync WHOOP data first
    await sync_whoop_data()
    
    # Then send daily reminder
    await send_daily_reminder()
    
    print("Daily scheduled tasks completed")