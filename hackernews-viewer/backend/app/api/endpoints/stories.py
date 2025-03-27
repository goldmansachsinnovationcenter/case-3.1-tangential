"""API endpoints for stories and comments."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.db import crud
from app.services.hackernews import refresh_hackernews_data

router = APIRouter()


@router.get("/top")
async def get_top_stories(
    limit: int = Query(5, ge=1, le=10),
    db: Session = Depends(get_db)
):
    """Get top stories."""
    stories = crud.get_top_stories(db, limit=limit)
    
    result = []
    for story in stories:
        result.append({
            "id": story.story_id,
            "hn_id": story.hn_id,
            "title": story.title,
            "url": story.url,
            "score": story.score,
            "time": story.time.isoformat() if story.time else None,
            "by": story.user.username if story.user else None,
            "descendants": story.descendants,
            "text": story.text,
            "type": story.type
        })
    
    return result


@router.get("/{story_id}")
async def get_story(
    story_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific story by ID."""
    story = crud.get_story(db, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    result = {
        "id": story.story_id,
        "hn_id": story.hn_id,
        "title": story.title,
        "url": story.url,
        "score": story.score,
        "time": story.time.isoformat() if story.time else None,
        "by": story.user.username if story.user else None,
        "descendants": story.descendants,
        "text": story.text,
        "type": story.type
    }
    
    return result


@router.get("/{story_id}/comments")
async def get_story_comments(
    story_id: int,
    limit: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """Get comments for a specific story."""
    story = crud.get_story(db, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    comments = crud.get_top_comments_for_story(db, story_id, limit=limit)
    
    result = []
    for comment in comments:
        result.append({
            "id": comment.comment_id,
            "hn_id": comment.hn_id,
            "text": comment.text,
            "time": comment.time.isoformat() if comment.time else None,
            "by": comment.user.username if comment.user else None,
            "level": comment.level,
            "parent_id": comment.parent_id
        })
    
    return result
