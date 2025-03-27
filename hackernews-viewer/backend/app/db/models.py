"""SQLite database models for the HackerNews Viewer."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class DimUser(Base):
    """Dimension table for users."""
    __tablename__ = "dim_users"

    user_id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    karma = Column(Integer, nullable=True)
    created_time = Column(DateTime, nullable=True)
    about = Column(Text, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow)

    stories = relationship("DimStory", back_populates="user")
    comments = relationship("DimComment", back_populates="user")


class DimStory(Base):
    """Dimension table for stories."""
    __tablename__ = "dim_stories"

    story_id = Column(Integer, primary_key=True)
    hn_id = Column(Integer, unique=True, nullable=False)
    title = Column(String, nullable=False)
    url = Column(String, nullable=True)
    score = Column(Integer, nullable=True)
    time = Column(DateTime, nullable=True)
    by_user_id = Column(Integer, ForeignKey("dim_users.user_id"), nullable=True)
    descendants = Column(Integer, nullable=True)  # Total comment count
    text = Column(Text, nullable=True)  # For Ask HN, etc.
    type = Column(String, nullable=True)  # Type of item (story, job, etc.)
    last_updated = Column(DateTime, default=datetime.utcnow)
    is_top = Column(Boolean, default=False)  # Flag for top stories

    user = relationship("DimUser", back_populates="stories")
    story_comments = relationship("FactStoryComment", back_populates="story")


class DimComment(Base):
    """Dimension table for comments."""
    __tablename__ = "dim_comments"

    comment_id = Column(Integer, primary_key=True)
    hn_id = Column(Integer, unique=True, nullable=False)
    text = Column(Text, nullable=True)
    time = Column(DateTime, nullable=True)
    by_user_id = Column(Integer, ForeignKey("dim_users.user_id"), nullable=True)
    parent_id = Column(Integer, nullable=True)  # Parent comment ID
    level = Column(Integer, default=0)  # Nesting level
    last_updated = Column(DateTime, default=datetime.utcnow)
    is_top_comment = Column(Boolean, default=False)  # Flag for top-level comments

    user = relationship("DimUser", back_populates="comments")
    story_comments = relationship("FactStoryComment", back_populates="comment")


class FactStoryComment(Base):
    """Fact table linking stories and comments."""
    __tablename__ = "fact_story_comments"

    fact_id = Column(Integer, primary_key=True)
    story_id = Column(Integer, ForeignKey("dim_stories.story_id"), nullable=False)
    comment_id = Column(Integer, ForeignKey("dim_comments.comment_id"), nullable=False)
    comment_rank = Column(Integer, nullable=True)  # Rank within the story
    refresh_time = Column(DateTime, default=datetime.utcnow)

    story = relationship("DimStory", back_populates="story_comments")
    comment = relationship("DimComment", back_populates="story_comments")


class FactRefreshLog(Base):
    """Fact table for refresh operations."""
    __tablename__ = "fact_refresh_log"

    refresh_id = Column(Integer, primary_key=True)
    refresh_time = Column(DateTime, default=datetime.utcnow)
    stories_refreshed = Column(Integer, default=0)
    comments_refreshed = Column(Integer, default=0)
    status = Column(String, nullable=False)  # Success/failure
    error_message = Column(Text, nullable=True)


def init_db(db_url="sqlite:///hackernews.db"):
    """Initialize the database."""
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    return engine
