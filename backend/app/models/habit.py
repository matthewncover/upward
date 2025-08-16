from sqlmodel import SQLModel, Field
from datetime import date, datetime
from typing import Optional


class Habit(SQLModel, table=True):
    __tablename__ = "habits"
    
    id: Optional[int] = Field(primary_key=True)
    name: str = Field(max_length=50)
    habit_type: str = Field(max_length=10)  # 'duration', 'pages', 'binary'
    weight: float = Field(default=1.0)
    target_days_per_week: int = Field(default=5)
    
    nonzero_threshold: float = Field(default=0)
    goal_threshold: float
    stretch_threshold: float
    zero_threshold: Optional[float] = Field(default=None)
    
    compound_rate: float = Field(default=1.15)
    decay_rate: float = Field(default=0.9)
    forgiveness_days: int = Field(default=2)
    
    is_inverted: bool = Field(default=False)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class HabitEntry(SQLModel, table=True):
    __tablename__ = "habit_entries"
    
    id: Optional[int] = Field(primary_key=True)
    habit_id: int = Field(foreign_key="habits.id")
    date: date
    value: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        unique_together = [["habit_id", "date"]]


class HabitScore(SQLModel, table=True):
    __tablename__ = "habit_scores"
    
    id: Optional[int] = Field(primary_key=True)
    habit_id: int = Field(foreign_key="habits.id")
    date: date
    raw_score: float
    momentum_multiplier: float
    final_score: float
    weekly_completion_rate: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        unique_together = [["habit_id", "date"]]