from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import date, timedelta
from typing import List, Optional
from ..database import get_session
from ..models import DailyScore, HabitScore, Habit
from ..schemas import DailyScoreResponse, HabitScoreResponse
from ..core.scoring import calculate_daily_scores
from ..core.momentum import get_all_momentum_status

router = APIRouter(prefix="/api/scores", tags=["scores"])


@router.get("/daily", response_model=List[DailyScoreResponse])
async def get_daily_scores(
    start_date: Optional[date] = None, 
    end_date: Optional[date] = None, 
    days: Optional[int] = None,
    session: Session = Depends(get_session)
):
    """Get daily scores time series."""
    if not start_date and not end_date and not days:
        days = 30  # Default to last 30 days
    
    if days:
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
    elif not start_date:
        start_date = end_date - timedelta(days=30)
    elif not end_date:
        end_date = start_date + timedelta(days=30)
    
    statement = select(DailyScore).where(
        DailyScore.date >= start_date,
        DailyScore.date <= end_date
    ).order_by(DailyScore.date)
    
    scores = session.exec(statement).all()
    return scores


@router.get("/habits/{habit_id}", response_model=List[HabitScoreResponse])
async def get_habit_performance(
    habit_id: int, 
    days: int = 30, 
    session: Session = Depends(get_session)
):
    """Get individual habit performance over time."""
    # Verify habit exists
    habit_statement = select(Habit).where(Habit.id == habit_id)
    habit = session.exec(habit_statement).first()
    
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    
    start_date = date.today() - timedelta(days=days-1)
    
    statement = select(HabitScore).where(
        HabitScore.habit_id == habit_id,
        HabitScore.date >= start_date
    ).order_by(HabitScore.date)
    
    scores = session.exec(statement).all()
    return scores


@router.post("/recalculate")
async def recalculate_scores(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    session: Session = Depends(get_session)
):
    """Trigger score recalculation for a date range."""
    if not start_date:
        start_date = date.today() - timedelta(days=30)
    if not end_date:
        end_date = date.today()
    
    recalculated_dates = []
    current_date = start_date
    
    while current_date <= end_date:
        try:
            calculate_daily_scores(session, current_date)
            recalculated_dates.append(current_date)
        except Exception as e:
            print(f"Failed to recalculate scores for {current_date}: {str(e)}")
        
        current_date += timedelta(days=1)
    
    return {
        "message": f"Recalculated scores for {len(recalculated_dates)} dates",
        "dates": recalculated_dates
    }


@router.get("/summary")
async def get_scores_summary(session: Session = Depends(get_session)):
    """Get current momentum, streaks, and weekly progress summary."""
    today = date.today()
    
    # Get today's score if available
    today_statement = select(DailyScore).where(DailyScore.date == today)
    today_score = session.exec(today_statement).first()
    
    # Get yesterday's score
    yesterday = today - timedelta(days=1)
    yesterday_statement = select(DailyScore).where(DailyScore.date == yesterday)
    yesterday_score = session.exec(yesterday_statement).first()
    
    # Get momentum status for all habits
    momentum_status = get_all_momentum_status(session, today)
    
    # Calculate week-over-week progress
    week_start = today - timedelta(days=6)
    prev_week_start = week_start - timedelta(days=7)
    prev_week_end = week_start - timedelta(days=1)
    
    # Current week average
    current_week_statement = select(DailyScore).where(
        DailyScore.date >= week_start,
        DailyScore.date <= today
    )
    current_week_scores = session.exec(current_week_statement).all()
    current_week_avg = sum(s.final_score for s in current_week_scores) / len(current_week_scores) if current_week_scores else 0
    
    # Previous week average
    prev_week_statement = select(DailyScore).where(
        DailyScore.date >= prev_week_start,
        DailyScore.date <= prev_week_end
    )
    prev_week_scores = session.exec(prev_week_statement).all()
    prev_week_avg = sum(s.final_score for s in prev_week_scores) / len(prev_week_scores) if prev_week_scores else 0
    
    # Calculate longest streak
    statement = select(DailyScore).where(DailyScore.date <= today).order_by(DailyScore.date.desc())
    all_scores = session.exec(statement).all()
    
    longest_streak = 0
    current_streak = 0
    
    for score in all_scores:
        if score.final_score > 0:
            current_streak += 1
            longest_streak = max(longest_streak, current_streak)
        else:
            current_streak = 0
    
    return {
        "today_score": today_score.final_score if today_score else None,
        "yesterday_score": yesterday_score.final_score if yesterday_score else None,
        "cumulative_score": today_score.cumulative_score if today_score else (yesterday_score.cumulative_score if yesterday_score else 0),
        "current_week_average": current_week_avg,
        "previous_week_average": prev_week_avg,
        "week_over_week_change": ((current_week_avg - prev_week_avg) / prev_week_avg * 100) if prev_week_avg > 0 else 0,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "momentum_status": momentum_status
    }


@router.get("/habits", response_model=List[HabitScoreResponse])
async def get_all_habit_scores(target_date: Optional[date] = None, session: Session = Depends(get_session)):
    """Get scores for all habits on a specific date."""
    if not target_date:
        target_date = date.today()
    
    statement = select(HabitScore).where(HabitScore.date == target_date)
    scores = session.exec(statement).all()
    return scores


@router.get("/trends")
async def get_score_trends(days: int = 30, session: Session = Depends(get_session)):
    """Get scoring trends and analytics."""
    start_date = date.today() - timedelta(days=days-1)
    
    statement = select(DailyScore).where(
        DailyScore.date >= start_date
    ).order_by(DailyScore.date)
    
    daily_scores = session.exec(statement).all()
    
    if not daily_scores:
        return {"message": "No data available for trend analysis"}
    
    # Calculate trend metrics
    scores = [s.final_score for s in daily_scores]
    avg_score = sum(scores) / len(scores)
    max_score = max(scores)
    min_score = min(scores)
    
    # Calculate 7-day moving average
    moving_averages = []
    for i in range(6, len(scores)):
        ma = sum(scores[i-6:i+1]) / 7
        moving_averages.append({
            "date": daily_scores[i].date,
            "moving_average": ma
        })
    
    # Identify best and worst performing days
    best_day = max(daily_scores, key=lambda x: x.final_score)
    worst_day = min(daily_scores, key=lambda x: x.final_score)
    
    return {
        "period": {
            "start_date": start_date,
            "end_date": date.today(),
            "days": days
        },
        "statistics": {
            "average_score": avg_score,
            "max_score": max_score,
            "min_score": min_score,
            "total_cumulative": daily_scores[-1].cumulative_score if daily_scores else 0
        },
        "best_day": {
            "date": best_day.date,
            "score": best_day.final_score
        },
        "worst_day": {
            "date": worst_day.date,
            "score": worst_day.final_score
        },
        "moving_averages": moving_averages
    }