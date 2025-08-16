from sqlmodel import SQLModel, Field
from datetime import date as Date, datetime
from typing import Optional


class WhoopData(SQLModel, table=True):
    __tablename__ = "whoop_data"
    
    id: Optional[int] = Field(primary_key=True)
    date: Date = Field(unique=True)
    sleep_score: Optional[float] = None
    hrv_score: Optional[float] = None
    recovery_score: Optional[float] = None
    whoop_multiplier: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)