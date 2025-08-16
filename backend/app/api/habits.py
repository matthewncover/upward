from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import date
from typing import List, Optional
from ..database import get_session
from ..models import Habit, HabitEntry
from ..schemas import HabitCreate, HabitUpdate, HabitResponse, HabitEntryCreate, HabitEntryResponse
from ..core.scoring import calculate_daily_scores

router = APIRouter(prefix="/api/habits", tags=["habits"])


@router.get("/", response_model=List[HabitResponse])
async def list_habits(session: Session = Depends(get_session)):
    """List all active habits with current configuration."""
    statement = select(Habit).where(Habit.is_active == True)
    habits = session.exec(statement).all()
    return habits


@router.post("/", response_model=HabitResponse)
async def create_habit(habit: HabitCreate, session: Session = Depends(get_session)):
    """Create a new habit."""
    db_habit = Habit(**habit.dict())
    session.add(db_habit)
    session.commit()
    session.refresh(db_habit)
    return db_habit


@router.put("/{habit_id}", response_model=HabitResponse)
async def update_habit(habit_id: int, habit_update: HabitUpdate, session: Session = Depends(get_session)):
    """Update habit configuration."""
    statement = select(Habit).where(Habit.id == habit_id)
    db_habit = session.exec(statement).first()
    
    if not db_habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    
    # Update only provided fields
    update_data = habit_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_habit, key, value)
    
    session.add(db_habit)
    session.commit()
    session.refresh(db_habit)
    return db_habit


@router.delete("/{habit_id}")
async def deactivate_habit(habit_id: int, session: Session = Depends(get_session)):
    """Deactivate a habit (soft delete)."""
    statement = select(Habit).where(Habit.id == habit_id)
    db_habit = session.exec(statement).first()
    
    if not db_habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    
    db_habit.is_active = False
    session.add(db_habit)
    session.commit()
    
    return {"message": "Habit deactivated successfully"}


@router.post("/entries", response_model=HabitEntryResponse)
async def create_habit_entry(entry: HabitEntryCreate, session: Session = Depends(get_session)):
    """Submit daily habit data."""
    # Check if habit exists and is active
    habit_statement = select(Habit).where(Habit.id == entry.habit_id, Habit.is_active == True)
    habit = session.exec(habit_statement).first()
    
    if not habit:
        raise HTTPException(status_code=404, detail="Active habit not found")
    
    # Check if entry already exists for this date
    existing_statement = select(HabitEntry).where(
        HabitEntry.habit_id == entry.habit_id,
        HabitEntry.date == entry.date
    )
    existing_entry = session.exec(existing_statement).first()
    
    if existing_entry:
        # Update existing entry
        existing_entry.value = entry.value
        session.add(existing_entry)
        db_entry = existing_entry
    else:
        # Create new entry
        db_entry = HabitEntry(**entry.dict())
        session.add(db_entry)
    
    session.commit()
    session.refresh(db_entry)
    
    # Recalculate scores for this date
    calculate_daily_scores(session, entry.date)
    
    return db_entry


@router.get("/entries", response_model=List[HabitEntryResponse])
async def get_habit_entries(entry_date: Optional[date] = None, session: Session = Depends(get_session)):
    """Get habit entries for a specific date or all entries."""
    statement = select(HabitEntry)
    
    if entry_date:
        statement = statement.where(HabitEntry.date == entry_date)
    
    entries = session.exec(statement).all()
    return entries


@router.post("/entries/batch")
async def create_habit_entries_batch(entries: List[HabitEntryCreate], session: Session = Depends(get_session)):
    """Submit multiple habit entries at once."""
    created_entries = []
    dates_to_recalculate = set()
    
    for entry_data in entries:
        # Check if habit exists and is active
        habit_statement = select(Habit).where(Habit.id == entry_data.habit_id, Habit.is_active == True)
        habit = session.exec(habit_statement).first()
        
        if not habit:
            raise HTTPException(status_code=404, detail=f"Active habit not found for ID {entry_data.habit_id}")
        
        # Check if entry already exists
        existing_statement = select(HabitEntry).where(
            HabitEntry.habit_id == entry_data.habit_id,
            HabitEntry.date == entry_data.date
        )
        existing_entry = session.exec(existing_statement).first()
        
        if existing_entry:
            existing_entry.value = entry_data.value
            session.add(existing_entry)
            created_entries.append(existing_entry)
        else:
            db_entry = HabitEntry(**entry_data.dict())
            session.add(db_entry)
            created_entries.append(db_entry)
        
        dates_to_recalculate.add(entry_data.date)
    
    session.commit()
    
    # Recalculate scores for all affected dates
    for calc_date in dates_to_recalculate:
        calculate_daily_scores(session, calc_date)
    
    return {"message": f"Successfully created/updated {len(created_entries)} entries"}


@router.get("/entries/{habit_id}", response_model=List[HabitEntryResponse])
async def get_habit_entries_by_id(habit_id: int, days: int = 30, session: Session = Depends(get_session)):
    """Get entries for a specific habit over the last N days."""
    from datetime import datetime, timedelta
    
    start_date = date.today() - timedelta(days=days)
    
    statement = select(HabitEntry).where(
        HabitEntry.habit_id == habit_id,
        HabitEntry.date >= start_date
    ).order_by(HabitEntry.date.desc())
    
    entries = session.exec(statement).all()
    return entries