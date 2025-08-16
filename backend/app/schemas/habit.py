from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


class HabitCreate(BaseModel):
    name: str
    habit_type: str
    weight: float = 1.0
    target_days_per_week: int = 5
    nonzero_threshold: float = 0
    goal_threshold: float
    stretch_threshold: float
    zero_threshold: Optional[float] = None
    compound_rate: float = 1.15
    decay_rate: float = 0.9
    forgiveness_days: int = 2
    is_inverted: bool = False


class HabitUpdate(BaseModel):
    name: Optional[str] = None
    weight: Optional[float] = None
    target_days_per_week: Optional[int] = None
    nonzero_threshold: Optional[float] = None
    goal_threshold: Optional[float] = None
    stretch_threshold: Optional[float] = None
    zero_threshold: Optional[float] = None
    compound_rate: Optional[float] = None
    decay_rate: Optional[float] = None
    forgiveness_days: Optional[int] = None
    is_inverted: Optional[bool] = None
    is_active: Optional[bool] = None


class HabitResponse(BaseModel):
    id: int
    name: str
    habit_type: str
    weight: float
    target_days_per_week: int
    nonzero_threshold: float
    goal_threshold: float
    stretch_threshold: float
    zero_threshold: Optional[float] = None
    compound_rate: float
    decay_rate: float
    forgiveness_days: int
    is_inverted: bool
    is_active: bool
    created_at: datetime


class HabitEntryCreate(BaseModel):
    habit_id: int
    date: date
    value: float


class HabitEntryResponse(BaseModel):
    id: int
    habit_id: int
    date: date
    value: float
    created_at: datetime