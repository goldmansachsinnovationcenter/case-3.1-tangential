"""CRUD operations for the HackerNews Viewer database."""
from datetime import datetime
from typing import List, Optional, Dict, Any, Union

from sqlmodel import Session, select

from app.db.models import DimUser, DimStory, DimComment, FactStoryComment, FactRefreshLog


def get_user(db: Session, user_id: int) -> Optional[DimUser]:
    """Get a user by ID."""
    return db.execute(select(DimUser).where(DimUser.user_id == user_id)).first()


def get_user_by_username(db: Session, username: str) -> Optional[DimUser]:
    """Get a user by username."""
    return db.execute(select(DimUser).where(DimUser.username == username)).first()


def create_user(db: Session, username: str, karma: Optional[int] = None,
                created_time: Optional[datetime] = None, about: Optional[str] = None) -> DimUser:
    """Create a new user."""
    db_user = DimUser(
        username=username,
        karma=karma,
        created_time=created_time,
        about=about,
        last_updated=datetime.utcnow()
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_id: int, data: Dict[str, Any]) -> Optional[DimUser]:
    """Update a user."""
    db_user = get_user(db, user_id)
    if db_user:
        for key, value in data.items():
            setattr(db_user, key, value)
        db_user.last_updated = datetime.utcnow()
        db.commit()
        db.refresh(db_user)
    return db_user


def get_story(db: Session, story_id: int) -> Optional[DimStory]:
    """Get a story by ID."""
    return db.execute(select(DimStory).where(DimStory.story_id == story_id)).first()


def get_story_by_hn_id(db: Session, hn_id: int) -> Optional[DimStory]:
    """Get a story by HackerNews ID."""
    return db.execute(select(DimStory).where(DimStory.hn_id == hn_id)).first()


def get_top_stories(db: Session, limit: int = 5) -> List[DimStory]:
    """Get top stories."""
    return db.execute(select(DimStory).where(DimStory.is_top == True).order_by(DimStory.score.desc()).limit(limit)).all()


def create_story(db: Session, hn_id: int, title: str, url: Optional[str] = None,
                score: Optional[int] = None, time: Optional[datetime] = None,
                by_user_id: Optional[int] = None, descendants: Optional[int] = None,
                text: Optional[str] = None, type: Optional[str] = None,
                is_top: bool = False) -> DimStory:
    """Create a new story."""
    db_story = DimStory(
        hn_id=hn_id,
        title=title,
        url=url,
        score=score,
        time=time,
        by_user_id=by_user_id,
        descendants=descendants,
        text=text,
        type=type,
        is_top=is_top,
        last_updated=datetime.utcnow()
    )
    db.add(db_story)
    db.commit()
    db.refresh(db_story)
    return db_story


def update_story(db: Session, story_id: int, data: Dict[str, Any]) -> Optional[DimStory]:
    """Update a story."""
    db_story = get_story(db, story_id)
    if db_story:
        for key, value in data.items():
            setattr(db_story, key, value)
        db_story.last_updated = datetime.utcnow()
        db.commit()
        db.refresh(db_story)
    return db_story


def mark_top_stories(db: Session, story_ids: List[int]) -> None:
    """Mark stories as top stories."""
    stories = db.execute(select(DimStory)).all()
    for story in stories:
        story.is_top = False
    
    for story_id in story_ids:
        story = get_story(db, story_id)
        if story:
            story.is_top = True
    
    db.commit()


def get_comment(db: Session, comment_id: int) -> Optional[DimComment]:
    """Get a comment by ID."""
    return db.execute(select(DimComment).where(DimComment.comment_id == comment_id)).first()


def get_comment_by_hn_id(db: Session, hn_id: int) -> Optional[DimComment]:
    """Get a comment by HackerNews ID."""
    return db.execute(select(DimComment).where(DimComment.hn_id == hn_id)).first()


def get_top_comments_for_story(db: Session, story_id: int, limit: int = 10) -> List[DimComment]:
    """Get top comments for a story."""
    statement = (
        select(DimComment)
        .join(FactStoryComment, FactStoryComment.comment_id == DimComment.comment_id)
        .where(FactStoryComment.story_id == story_id)
        .order_by(FactStoryComment.comment_rank)
        .limit(limit)
    )
    return db.execute(statement).all()


def create_comment(db: Session, hn_id: int, text: Optional[str] = None,
                  time: Optional[datetime] = None, by_user_id: Optional[int] = None,
                  parent_id: Optional[int] = None, level: int = 0,
                  is_top_comment: bool = False) -> DimComment:
    """Create a new comment."""
    db_comment = DimComment(
        hn_id=hn_id,
        text=text,
        time=time,
        by_user_id=by_user_id,
        parent_id=parent_id,
        level=level,
        is_top_comment=is_top_comment,
        last_updated=datetime.utcnow()
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment


def update_comment(db: Session, comment_id: int, data: Dict[str, Any]) -> Optional[DimComment]:
    """Update a comment."""
    db_comment = get_comment(db, comment_id)
    if db_comment:
        for key, value in data.items():
            setattr(db_comment, key, value)
        db_comment.last_updated = datetime.utcnow()
        db.commit()
        db.refresh(db_comment)
    return db_comment


def link_story_comment(db: Session, story_id: int, comment_id: int, comment_rank: int) -> FactStoryComment:
    """Link a story and comment in the fact table."""
    db_fact = FactStoryComment(
        story_id=story_id,
        comment_id=comment_id,
        comment_rank=comment_rank,
        refresh_time=datetime.utcnow()
    )
    db.add(db_fact)
    db.commit()
    db.refresh(db_fact)
    return db_fact


def log_refresh(db: Session, stories_refreshed: int, comments_refreshed: int,
               status: str, error_message: Optional[str] = None) -> FactRefreshLog:
    """Log a data refresh operation."""
    db_log = FactRefreshLog(
        refresh_time=datetime.utcnow(),
        stories_refreshed=stories_refreshed,
        comments_refreshed=comments_refreshed,
        status=status,
        error_message=error_message
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


def get_last_refresh(db: Session) -> Optional[FactRefreshLog]:
    """Get the last refresh log entry."""
    return db.execute(select(FactRefreshLog).order_by(FactRefreshLog.refresh_time.desc())).first()
