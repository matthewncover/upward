#!/usr/bin/env python3
"""
Daily Scheduled Tasks Runner

This script runs daily maintenance tasks including:
- WHOOP data synchronization from API to database
- Morning habit reminder email notifications

Usage:
    python schedule_reminder.py

Recommended scheduling:
    - Unix/Linux cron: 45 15 * * * /path/to/python /path/to/schedule_reminder.py
    - Windows Task Scheduler: Run daily at 8:45 AM MST (15:45 UTC)
"""

import sys
import os
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from app.core.notifications import schedule_daily_tasks

if __name__ == "__main__":
    print("Starting daily scheduled tasks...")
    try:
        schedule_daily_tasks()
        print("Daily tasks completed successfully")
    except Exception as e:
        print(f"Failed to run daily tasks: {e}")
        sys.exit(1)