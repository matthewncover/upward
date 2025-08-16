from sqlmodel import SQLModel, Field
from datetime import date as Date, datetime
from typing import Optional


class DailyScore(SQLModel, table=True):
    __tablename__ = "daily_scores"
    
    id: Optional[int] = Field(primary_key=True)
    date: Date = Field(unique=True)
    base_score: float
    whoop_multiplier: float = Field(default=1.0)
    final_score: float
    cumulative_score: float
    created_at: datetime = Field(default_factory=datetime.utcnow)