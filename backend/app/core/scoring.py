from datetime import date, timedelta
from typing import List, Tuple, Optional
from sqlmodel import Session, select
from ..models import Habit, HabitEntry, HabitScore, DailyScore, WhoopData


def calculate_raw_score(habit: Habit, value: float) -> float:
    """
    Calculate raw score based on habit thresholds.
    Returns 0.3, 1.0, or 1.5 based on performance tier.
    """
    if habit.is_inverted:
        if value >= habit.nonzero_threshold:
            return 0.0
        elif value <= habit.stretch_threshold:
            return 1.5
        elif value <= habit.goal_threshold:
            return 1.0
        else:
            return 0.3
    else:
        if value == 0:
            return 0.0
        elif value >= habit.stretch_threshold:
            return 1.5
        elif value >= habit.goal_threshold:
            return 1.0
        elif value >= habit.nonzero_threshold:
            return 0.3
        else:
            return 0.0


def get_weekly_completion_rate(session: Session, habit_id: int, target_date: date) -> float:
    """
    Calculate completion rate for the 7 days leading up to target_date.
    """
    start_date = target_date - timedelta(days=6)
    
    statement = select(HabitEntry).where(
        HabitEntry.habit_id == habit_id,
        HabitEntry.date >= start_date,
        HabitEntry.date <= target_date
    )
    entries = session.exec(statement).all()
    
    completed_days = 0
    for entry in entries:
        if entry.value > 0:
            completed_days += 1
    
    return completed_days / 7.0


def calculate_weekly_performance_tier(completion_rate: float, target_rate: float, forgiveness_days: int) -> str:
    """
    Determine performance tier based on completion rate vs target.
    """
    target_completion_rate = target_rate / 7.0
    forgiveness_buffer = forgiveness_days / 7.0
    
    if completion_rate > target_completion_rate:
        return "exceed"
    elif completion_rate >= target_completion_rate:
        return "meet"
    elif completion_rate >= (target_completion_rate - forgiveness_buffer):
        return "close"
    elif completion_rate > 0.2:
        return "miss"
    else:
        return "fail"


def calculate_momentum(session: Session, habit: Habit, current_date: date) -> float:
    """
    Calculate momentum multiplier based on rolling 7-day performance.
    """
    completion_rate = get_weekly_completion_rate(session, habit.id, current_date)
    performance_tier = calculate_weekly_performance_tier(
        completion_rate, habit.target_days_per_week, habit.forgiveness_days
    )
    
    # Get previous momentum to apply compound/decay
    previous_date = current_date - timedelta(days=1)
    statement = select(HabitScore).where(
        HabitScore.habit_id == habit.id,
        HabitScore.date == previous_date
    )
    previous_score = session.exec(statement).first()
    previous_momentum = previous_score.momentum_multiplier if previous_score else 1.0
    
    # Apply momentum rules
    if performance_tier == "exceed":
        return min(previous_momentum * habit.compound_rate, 3.0)
    elif performance_tier == "meet":
        return previous_momentum
    elif performance_tier == "close":
        return max(previous_momentum * habit.decay_rate, 0.5)
    elif performance_tier == "miss":
        return max(previous_momentum * (habit.decay_rate ** 2), 0.3)
    else:  # fail
        return max(previous_momentum * (habit.decay_rate ** 3), 0.1)


def calculate_whoop_multiplier(session: Session, target_date: date) -> float:
    """
    Calculate WHOOP multiplier based on average of sleep, HRV, and recovery scores.
    Linear scaling: 70% = 1.0x, <70% = <1.0x, >70% = >1.0x
    """
    statement = select(WhoopData).where(WhoopData.date == target_date)
    whoop_data = session.exec(statement).first()
    
    if not whoop_data or not all([whoop_data.sleep_score, whoop_data.hrv_score, whoop_data.recovery_score]):
        return 1.0
    
    average_score = (whoop_data.sleep_score + whoop_data.hrv_score + whoop_data.recovery_score) / 3.0
    
    # Linear scaling around 70%
    multiplier = average_score / 70.0
    
    # Cap the multiplier between 0.5 and 2.0
    return max(0.5, min(multiplier, 2.0))


def calculate_daily_scores(session: Session, target_date: date) -> float:
    """
    Complete daily scoring pipeline for a specific date.
    Returns the final daily score.
    """
    # Get all active habits
    habits_statement = select(Habit).where(Habit.is_active == True)
    habits = session.exec(habits_statement).all()
    
    total_weighted_score = 0.0
    total_weight = 0.0
    
    # Process each habit
    for habit in habits:
        # Get habit entry for the date
        entry_statement = select(HabitEntry).where(
            HabitEntry.habit_id == habit.id,
            HabitEntry.date == target_date
        )
        entry = session.exec(entry_statement).first()
        
        if not entry:
            # No entry means 0 value
            raw_score = 0.0
        else:
            raw_score = calculate_raw_score(habit, entry.value)
        
        # Calculate momentum multiplier
        momentum_multiplier = calculate_momentum(session, habit, target_date)
        
        # Calculate final habit score
        final_habit_score = raw_score * momentum_multiplier
        
        # Store habit score
        habit_score = HabitScore(
            habit_id=habit.id,
            date=target_date,
            raw_score=raw_score,
            momentum_multiplier=momentum_multiplier,
            final_score=final_habit_score,
            weekly_completion_rate=get_weekly_completion_rate(session, habit.id, target_date)
        )
        
        # Check if habit score already exists
        existing_statement = select(HabitScore).where(
            HabitScore.habit_id == habit.id,
            HabitScore.date == target_date
        )
        existing = session.exec(existing_statement).first()
        
        if existing:
            existing.raw_score = raw_score
            existing.momentum_multiplier = momentum_multiplier
            existing.final_score = final_habit_score
            existing.weekly_completion_rate = habit_score.weekly_completion_rate
        else:
            session.add(habit_score)
        
        # Add to total score calculation
        total_weighted_score += final_habit_score * habit.weight
        total_weight += habit.weight
    
    # Calculate base daily score
    base_score = total_weighted_score / total_weight if total_weight > 0 else 0.0
    
    # Apply WHOOP multiplier
    whoop_multiplier = calculate_whoop_multiplier(session, target_date)
    final_score = base_score * whoop_multiplier
    
    # Calculate cumulative score
    previous_date = target_date - timedelta(days=1)
    previous_daily_statement = select(DailyScore).where(DailyScore.date == previous_date)
    previous_daily = session.exec(previous_daily_statement).first()
    previous_cumulative = previous_daily.cumulative_score if previous_daily else 0.0
    cumulative_score = previous_cumulative + final_score
    
    # Store daily score
    daily_score = DailyScore(
        date=target_date,
        base_score=base_score,
        whoop_multiplier=whoop_multiplier,
        final_score=final_score,
        cumulative_score=cumulative_score
    )
    
    # Check if daily score already exists
    existing_daily_statement = select(DailyScore).where(DailyScore.date == target_date)
    existing_daily = session.exec(existing_daily_statement).first()
    
    if existing_daily:
        existing_daily.base_score = base_score
        existing_daily.whoop_multiplier = whoop_multiplier
        existing_daily.final_score = final_score
        existing_daily.cumulative_score = cumulative_score
    else:
        session.add(daily_score)
    
    session.commit()
    return final_score