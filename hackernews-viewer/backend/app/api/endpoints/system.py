"""API endpoints for system operations."""
import os
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, Query
from sqlmodel import Session

from app.core.database import get_db
from app.db import crud
from app.services.hackernews import refresh_hackernews_data
from app.utils import backup

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
    
    try:
        backups = backup.list_backups()
        result["backups"] = {
            "count": len(backups),
            "latest": backups[0] if backups else None
        }
    except Exception as e:
        result["backups"] = {
            "count": 0,
            "error": str(e)
        }
    
    return result


@router.post("/refresh")
async def trigger_refresh(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Trigger a manual refresh of the data.
    
    Creates a backup of the current database before refreshing.
    """
    try:
        backup_info = backup.create_backup()
        
        background_tasks.add_task(refresh_hackernews_data, db)
        
        return {
            "status": "refresh_started",
            "backup": backup_info
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create backup before refresh: {str(e)}"
        )


@router.get("/backups")
async def list_database_backups():
    """List all available database backups."""
    try:
        backups = backup.list_backups()
        return {
            "count": len(backups),
            "backups": backups
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list backups: {str(e)}"
        )


@router.post("/restore")
async def restore_database(
    filename: str = Query(..., description="Backup filename to restore from")
):
    """Restore the database from a backup file."""
    try:
        result = backup.restore_from_backup(filename)
        return {
            "status": "success",
            "message": f"Database restored from backup: {filename}",
            "details": result
        }
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to restore database: {str(e)}"
        )
