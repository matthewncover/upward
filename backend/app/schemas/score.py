from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


class DailyScoreResponse(BaseModel):
    id: int
    date: date
    base_score: float
    whoop_multiplier: float
    final_score: float
    cumulative_score: float
    created_at: datetime


class HabitScoreResponse(BaseModel):
    id: int
    habit_id: int
    date: date
    raw_score: float
    momentum_multiplier: float
    final_score: float
    weekly_completion_rate: Optional[float]
    created_at: datetime