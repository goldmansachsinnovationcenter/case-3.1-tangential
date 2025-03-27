"""API endpoints for users."""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.database import get_db
from app.db import crud

router = APIRouter()


@router.get("/{username}")
async def get_user(
    username: str,
    db: Session = Depends(get_db)
):
    """Get a user by username."""
    user = crud.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = {
        "id": user.user_id,
        "username": user.username,
        "karma": user.karma,
        "created_time": user.created_time.isoformat() if user.created_time else None,
        "about": user.about
    }
    
    return result
