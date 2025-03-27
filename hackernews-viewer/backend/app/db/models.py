"""SQLite database models for the HackerNews Viewer."""
from datetime import datetime
from typing import List, Optional
from sqlmodel import Field, Relationship, Session, SQLModel, create_engine


class DimUser(SQLModel, table=True):
    """Dimension table for users."""
    __tablename__ = "dim_users"

    user_id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, nullable=False)
    karma: Optional[int] = Field(default=None)
    created_time: Optional[datetime] = Field(default=None)
    about: Optional[str] = Field(default=None)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    stories: List["DimStory"] = Relationship(back_populates="user")
    comments: List["DimComment"] = Relationship(back_populates="user")


class DimStory(SQLModel, table=True):
    """Dimension table for stories."""
    __tablename__ = "dim_stories"

    story_id: Optional[int] = Field(default=None, primary_key=True)
    hn_id: int = Field(unique=True, nullable=False)
    title: str = Field(nullable=False)
    url: Optional[str] = Field(default=None)
    score: Optional[int] = Field(default=None)
    time: Optional[datetime] = Field(default=None)
    by_user_id: Optional[int] = Field(default=None, foreign_key="dim_users.user_id")
    descendants: Optional[int] = Field(default=None)  # Total comment count
    text: Optional[str] = Field(default=None)  # For Ask HN, etc.
    type: Optional[str] = Field(default=None)  # Type of item (story, job, etc.)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    is_top: bool = Field(default=False)  # Flag for top stories

    user: Optional[DimUser] = Relationship(back_populates="stories")
    story_comments: List["FactStoryComment"] = Relationship(back_populates="story")


class DimComment(SQLModel, table=True):
    """Dimension table for comments."""
    __tablename__ = "dim_comments"

    comment_id: Optional[int] = Field(default=None, primary_key=True)
    hn_id: int = Field(unique=True, nullable=False)
    text: Optional[str] = Field(default=None)
    time: Optional[datetime] = Field(default=None)
    by_user_id: Optional[int] = Field(default=None, foreign_key="dim_users.user_id")
    parent_id: Optional[int] = Field(default=None)  # Parent comment ID
    level: int = Field(default=0)  # Nesting level
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    is_top_comment: bool = Field(default=False)  # Flag for top-level comments

    user: Optional[DimUser] = Relationship(back_populates="comments")
    story_comments: List["FactStoryComment"] = Relationship(back_populates="comment")


class FactStoryComment(SQLModel, table=True):
    """Fact table linking stories and comments."""
    __tablename__ = "fact_story_comments"

    fact_id: Optional[int] = Field(default=None, primary_key=True)
    story_id: int = Field(foreign_key="dim_stories.story_id", nullable=False)
    comment_id: int = Field(foreign_key="dim_comments.comment_id", nullable=False)
    comment_rank: Optional[int] = Field(default=None)  # Rank within the story
    refresh_time: datetime = Field(default_factory=datetime.utcnow)

    story: DimStory = Relationship(back_populates="story_comments")
    comment: DimComment = Relationship(back_populates="story_comments")


class FactRefreshLog(SQLModel, table=True):
    """Fact table for refresh operations."""
    __tablename__ = "fact_refresh_log"

    refresh_id: Optional[int] = Field(default=None, primary_key=True)
    refresh_time: datetime = Field(default_factory=datetime.utcnow)
    stories_refreshed: int = Field(default=0)
    comments_refreshed: int = Field(default=0)
    status: str = Field(nullable=False)  # Success/failure
    error_message: Optional[str] = Field(default=None)


def init_db(db_url="sqlite:///hackernews.db"):
    """Initialize the database."""
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return engine
