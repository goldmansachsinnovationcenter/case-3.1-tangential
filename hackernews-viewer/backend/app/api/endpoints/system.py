"""API endpoints for system operations."""
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlmodel import Session

from app.core.database import get_db
from app.db import crud
from app.services.hackernews import refresh_hackernews_data

router = APIRouter()


@router.get("/status")
async def get_system_status(
    db: Session = Depends(get_db)
):
    """Get system status information."""
    last_refresh = crud.get_last_refresh(db)
    
    result = {
        "status": "ok",
        "last_refresh": None
    }
    
    if last_refresh:
        result["last_refresh"] = {
            "refresh_id": last_refresh.refresh_id,
            "refresh_time": last_refresh.refresh_time.isoformat(),
            "stories_refreshed": last_refresh.stories_refreshed,
            "comments_refreshed": last_refresh.comments_refreshed,
            "status": last_refresh.status,
            "error_message": last_refresh.error_message
        }
    
    return result


@router.post("/refresh")
async def trigger_refresh(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Trigger a manual refresh of the data."""
    background_tasks.add_task(refresh_hackernews_data, db)
    
    return {"status": "refresh_started"}
