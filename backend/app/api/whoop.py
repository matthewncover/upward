from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import date, timedelta
from typing import List, Optional
from ..database import get_session
from ..models import WhoopData
from ..utils.whoop_client import WhoopClient
from ..api.auth import whoop_tokens

router = APIRouter(prefix="/api/whoop", tags=["whoop"])


@router.get("/test-auth")
async def test_whoop_auth():
    """Test WHOOP authentication and API access."""
    if not whoop_tokens.get("access_token"):
        raise HTTPException(status_code=401, detail="WHOOP not connected")
    
    client = WhoopClient(whoop_tokens["access_token"])
    
    try:
        # Test basic profile access
        profile_data = await client.get_user_profile()
        
        if profile_data:
            return {"message": "Authentication successful", "profile": profile_data}
        else:
            return {"message": "Authentication failed or no profile data", "profile": None}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test auth: {str(e)}")


@router.post("/sync")
async def sync_whoop_data(days: int = 30, session: Session = Depends(get_session)):
    """Fetch latest WHOOP data and sync to database."""
    if not whoop_tokens.get("access_token"):
        raise HTTPException(status_code=401, detail="WHOOP not connected")
    
    client = WhoopClient(whoop_tokens["access_token"])
    
    # Calculate date range
    end_date = date.today()
    start_date = end_date - timedelta(days=days-1)
    
    try:
        # Fetch data from WHOOP API
        recovery_data = await client.get_recovery_data(start_date, end_date)
        sleep_data = await client.get_sleep_data(start_date, end_date)
        hrv_data = await client.get_hrv_data(start_date, end_date)
        
        synced_dates = []
        
        # Process recovery data (v2 API structure)
        if recovery_data and "records" in recovery_data:
            for record in recovery_data["records"]:
                # v2 API: use created_at as the date reference
                if "created_at" in record:
                    record_date = date.fromisoformat(record["created_at"].split("T")[0])
                else:
                    continue  # Skip records without date
                
                # Extract scores from v2 API structure
                recovery_score = record.get("score", {}).get("recovery_score")
                hrv_score = record.get("score", {}).get("hrv_rmssd_milli")
                
                # Get sleep score from sleep data for the same date
                sleep_score = None
                if sleep_data and "records" in sleep_data:
                    for sleep_record in sleep_data["records"]:
                        # v2 API: use start timestamp for sleep records
                        if "start" in sleep_record and sleep_record["start"]:
                            sleep_date = date.fromisoformat(sleep_record["start"].split("T")[0])
                            if sleep_date == record_date:
                                # Use sleep_performance_percentage as the sleep score (0-100%)
                                sleep_score = sleep_record.get("score", {}).get("sleep_performance_percentage")
                                break
                
                # Calculate WHOOP multiplier
                whoop_multiplier = calculate_whoop_multiplier_from_scores(
                    sleep_score, hrv_score, recovery_score
                )
                
                # Check if record already exists
                existing_statement = select(WhoopData).where(WhoopData.date == record_date)
                existing = session.exec(existing_statement).first()
                
                if existing:
                    # Update existing record
                    existing.sleep_score = sleep_score
                    existing.hrv_score = hrv_score
                    existing.recovery_score = recovery_score
                    existing.whoop_multiplier = whoop_multiplier
                else:
                    # Create new record
                    whoop_record = WhoopData(
                        date=record_date,
                        sleep_score=sleep_score,
                        hrv_score=hrv_score,
                        recovery_score=recovery_score,
                        whoop_multiplier=whoop_multiplier
                    )
                    session.add(whoop_record)
                
                synced_dates.append(record_date)
        
        session.commit()
        
        return {
            "message": f"Successfully synced WHOOP data for {len(synced_dates)} dates",
            "synced_dates": synced_dates,
            "date_range": {
                "start": start_date,
                "end": end_date
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync WHOOP data: {str(e)}")


@router.get("/data")
async def get_whoop_data(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    days: int = 30,
    session: Session = Depends(get_session)
):
    """Get stored WHOOP data for a date range."""
    if not start_date and not end_date:
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
    elif not start_date:
        start_date = end_date - timedelta(days=30)
    elif not end_date:
        end_date = start_date + timedelta(days=30)
    
    statement = select(WhoopData).where(
        WhoopData.date >= start_date,
        WhoopData.date <= end_date
    ).order_by(WhoopData.date)
    
    whoop_data = session.exec(statement).all()
    return whoop_data


@router.get("/debug/raw-data")
async def debug_raw_whoop_data(days: int = 3):
    """Debug endpoint to see raw WHOOP API responses."""
    if not whoop_tokens.get("access_token"):
        raise HTTPException(status_code=401, detail="WHOOP not connected")
    
    client = WhoopClient(whoop_tokens["access_token"])
    end_date = date.today()
    start_date = end_date - timedelta(days=days-1)
    
    recovery_data = await client.get_recovery_data(start_date, end_date)
    sleep_data = await client.get_sleep_data(start_date, end_date)
    
    return {
        "date_range": {"start": start_date, "end": end_date},
        "recovery_sample": recovery_data.get("records", [])[:1] if recovery_data else None,
        "sleep_sample": sleep_data.get("records", [])[:1] if sleep_data else None
    }


@router.get("/status")
async def get_whoop_sync_status(session: Session = Depends(get_session)):
    """Get WHOOP data sync status and coverage."""
    if not whoop_tokens.get("access_token"):
        return {
            "connected": False,
            "last_sync": None,
            "data_coverage": 0,
            "missing_dates": []
        }
    
    # Get latest WHOOP data entry
    latest_statement = select(WhoopData).order_by(WhoopData.date.desc())
    latest_data = session.exec(latest_statement).first()
    
    # Calculate data coverage for last 30 days
    end_date = date.today()
    start_date = end_date - timedelta(days=29)
    
    coverage_statement = select(WhoopData).where(
        WhoopData.date >= start_date,
        WhoopData.date <= end_date
    )
    coverage_data = session.exec(coverage_statement).all()
    
    # Find missing dates
    all_dates = {start_date + timedelta(days=i) for i in range(30)}
    covered_dates = {data.date for data in coverage_data}
    missing_dates = sorted(all_dates - covered_dates)
    
    return {
        "connected": True,
        "last_sync": latest_data.date if latest_data else None,
        "data_coverage": len(covered_dates) / 30 * 100,
        "missing_dates": missing_dates,
        "total_records": len(coverage_data)
    }


def calculate_whoop_multiplier_from_scores(sleep_score: Optional[float], hrv_score: Optional[float], recovery_score: Optional[float]) -> float:
    """
    Calculate WHOOP multiplier from individual scores.
    Sleep and recovery scores are percentages (0-100).
    HRV is in milliseconds and needs normalization.
    """
    valid_scores = []
    
    if sleep_score is not None:
        # Sleep performance percentage is already 0-100%
        valid_scores.append(sleep_score)
    
    if hrv_score is not None:
        # HRV score normalization (this is highly individual, using rough estimates)
        # Typical HRV ranges from 20-100ms, normalize to percentage
        hrv_percentage = min(hrv_score / 50 * 100, 100)  # Rough normalization
        valid_scores.append(hrv_percentage)
    
    if recovery_score is not None:
        # Recovery score is already a percentage (0-100)
        valid_scores.append(recovery_score)
    
    if not valid_scores:
        return 1.0
    
    average_score = sum(valid_scores) / len(valid_scores)
    
    # Linear scaling around 70%
    multiplier = average_score / 70.0
    
    # Cap the multiplier between 0.5 and 2.0
    return max(0.5, min(multiplier, 2.0))