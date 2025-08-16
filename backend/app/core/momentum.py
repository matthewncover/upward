from datetime import date, timedelta
from typing import Dict, List
from sqlmodel import Session, select
from ..models import Habit, HabitScore


def get_momentum_status(session: Session, habit_id: int, current_date: date) -> Dict:
    """
    Get current momentum status for a habit including trend analysis.
    """
    # Get last 14 days of scores to analyze trend
    start_date = current_date - timedelta(days=13)
    
    statement = select(HabitScore).where(
        HabitScore.habit_id == habit_id,
        HabitScore.date >= start_date,
        HabitScore.date <= current_date
    ).order_by(HabitScore.date)
    
    scores = session.exec(statement).all()
    
    if not scores:
        return {
            "status": "no_data",
            "current_multiplier": 1.0,
            "trend": "stable",
            "streak_days": 0
        }
    
    current_score = scores[-1] if scores else None
    current_multiplier = current_score.momentum_multiplier if current_score else 1.0
    
    # Analyze trend over last 7 days
    recent_multipliers = [score.momentum_multiplier for score in scores[-7:]]
    
    if len(recent_multipliers) >= 2:
        if recent_multipliers[-1] > recent_multipliers[0] * 1.05:
            trend = "growing"
        elif recent_multipliers[-1] < recent_multipliers[0] * 0.95:
            trend = "decaying"
        else:
            trend = "stable"
    else:
        trend = "stable"
    
    # Calculate streak (consecutive days with positive momentum)
    streak_days = 0
    for score in reversed(scores):
        if score.raw_score > 0:
            streak_days += 1
        else:
            break
    
    # Determine status based on current multiplier
    if current_multiplier >= 1.5:
        status = "excellent"
    elif current_multiplier >= 1.2:
        status = "good"
    elif current_multiplier >= 0.9:
        status = "stable"
    elif current_multiplier >= 0.6:
        status = "declining"
    else:
        status = "poor"
    
    return {
        "status": status,
        "current_multiplier": current_multiplier,
        "trend": trend,
        "streak_days": streak_days
    }


def get_all_momentum_status(session: Session, current_date: date) -> Dict:
    """
    Get momentum status for all active habits.
    """
    statement = select(Habit).where(Habit.is_active == True)
    habits = session.exec(statement).all()
    
    momentum_data = {}
    
    for habit in habits:
        momentum_data[habit.name] = get_momentum_status(session, habit.id, current_date)
    
    return momentum_data