"""Tests for CRUD operations."""
import pytest
from datetime import datetime
from sqlmodel import Session, select

from app.db.models import DimUser, DimStory, DimComment, FactStoryComment, FactRefreshLog
from app.db import crud


@pytest.fixture
def test_user():
    """Create a test user for testing."""
    return {
        "username": "testuser",
        "karma": 1000,
        "created_time": datetime.utcnow(),
        "about": "Test user"
    }


@pytest.fixture
def test_story(request):
    """Create a test story for testing."""
    test_name = request.node.name if hasattr(request, "node") else "default"
    hn_id = int(hash(test_name) % 100000) + 10000  # Ensure positive and reasonable size
    
    return {
        "hn_id": hn_id,
        "title": f"Test Story for {test_name}",
        "url": "https://example.com",
        "score": 100,
        "time": datetime.utcnow(),
        "descendants": 10,
        "text": None,
        "type": "story",
        "is_top": True
    }


@pytest.fixture
def test_comment():
    """Create a test comment for testing."""
    return {
        "hn_id": 67890,
        "text": "Test Comment",
        "time": datetime.utcnow(),
        "level": 0,
        "is_top_comment": True
    }


def test_create_and_get_user(db_session, test_user):
    """Test creating and retrieving a user."""
    user = crud.create_user(db_session, **test_user)
    assert user.username == test_user["username"]
    assert user.karma == test_user["karma"]
    
    retrieved_user = crud.get_user(db_session, user.user_id)
    assert retrieved_user is not None
    assert retrieved_user.username == test_user["username"]
    
    retrieved_user_by_username = crud.get_user_by_username(db_session, test_user["username"])
    assert retrieved_user_by_username is not None
    assert retrieved_user_by_username.user_id == user.user_id


def test_create_and_get_story(db_session, test_story):
    """Test creating and retrieving a story."""
    story = crud.create_story(db_session, **test_story)
    assert story.hn_id == test_story["hn_id"]
    assert story.title == test_story["title"]
    assert story.score == test_story["score"]
    
    retrieved_story = crud.get_story(db_session, story.story_id)
    assert retrieved_story is not None
    assert retrieved_story.hn_id == test_story["hn_id"]
    
    retrieved_story_by_hn_id = crud.get_story_by_hn_id(db_session, test_story["hn_id"])
    assert retrieved_story_by_hn_id is not None
    assert retrieved_story_by_hn_id.story_id == story.story_id


def test_get_top_stories(db_session, test_story):
    """Test retrieving top stories."""
    story = crud.create_story(db_session, **test_story)
    
    top_stories = crud.get_top_stories(db_session)
    assert len(top_stories) > 0
    assert any(s.story_id == story.story_id for s in top_stories)
    
    if len(top_stories) > 1:
        for i in range(1, len(top_stories)):
            assert top_stories[i-1].score >= top_stories[i].score


def test_mark_top_stories(db_session, test_story):
    """Test marking stories as top stories."""
    story1 = crud.create_story(db_session, **test_story)
    
    test_story2 = test_story.copy()
    test_story2["hn_id"] = 67890
    test_story2["title"] = "Another Test Story"
    test_story2["is_top"] = False
    story2 = crud.create_story(db_session, **test_story2)
    
    crud.mark_top_stories(db_session, [story2.story_id])
    
    updated_story1 = crud.get_story(db_session, story1.story_id)
    updated_story2 = crud.get_story(db_session, story2.story_id)
    assert not updated_story1.is_top
    assert updated_story2.is_top


def test_create_and_get_comment(db_session, test_comment, test_story):
    """Test creating and retrieving a comment."""
    story = crud.create_story(db_session, **test_story)
    
    comment = crud.create_comment(db_session, **test_comment)
    assert comment.hn_id == test_comment["hn_id"]
    assert comment.text == test_comment["text"]
    
    crud.link_story_comment(db_session, story.story_id, comment.comment_id, 1)
    
    retrieved_comment = crud.get_comment(db_session, comment.comment_id)
    assert retrieved_comment is not None
    assert retrieved_comment.hn_id == test_comment["hn_id"]
    
    retrieved_comment_by_hn_id = crud.get_comment_by_hn_id(db_session, test_comment["hn_id"])
    assert retrieved_comment_by_hn_id is not None
    assert retrieved_comment_by_hn_id.comment_id == comment.comment_id
    
    top_comments = crud.get_top_comments_for_story(db_session, story.story_id)
    assert len(top_comments) > 0
    assert any(c.comment_id == comment.comment_id for c in top_comments)


def test_log_and_get_refresh(db_session):
    """Test logging and retrieving refresh operations."""
    refresh_log = crud.log_refresh(db_session, 5, 50, "success")
    assert refresh_log.stories_refreshed == 5
    assert refresh_log.comments_refreshed == 50
    assert refresh_log.status == "success"
    
    last_refresh = crud.get_last_refresh(db_session)
    assert last_refresh is not None
    assert last_refresh.refresh_id == refresh_log.refresh_id
    assert last_refresh.stories_refreshed == 5
    assert last_refresh.comments_refreshed == 50
