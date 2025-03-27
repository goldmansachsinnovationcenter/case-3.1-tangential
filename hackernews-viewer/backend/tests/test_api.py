"""Tests for the API endpoints."""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from sqlmodel import Session

from app.main import app
from app.core.database import get_db


@pytest.fixture
def client(override_get_db):
    """Test client with overridden database dependency."""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides = {}


def test_root_endpoint(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the HackerNews Viewer API"}


def test_health_endpoint(client):
    """Test the health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch("app.api.endpoints.stories.crud.get_top_stories")
def test_get_top_stories(mock_get_top_stories, client, db_session):
    """Test the get_top_stories endpoint."""
    mock_story = MagicMock()
    mock_story.story_id = 1
    mock_story.hn_id = 12345
    mock_story.title = "Test Story"
    mock_story.url = "https://example.com"
    mock_story.score = 100
    mock_story.time = None
    mock_story.user = None
    mock_story.descendants = 10
    mock_story.text = None
    mock_story.type = "story"
    
    mock_get_top_stories.return_value = [mock_story]
    
    response = client.get("/api/stories/top")
    
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == 1
    assert response.json()[0]["title"] == "Test Story"
    assert response.json()[0]["score"] == 100


@patch("app.api.endpoints.stories.crud.get_story")
def test_get_story(mock_get_story, client, db_session):
    """Test the get_story endpoint."""
    mock_story = MagicMock()
    mock_story.story_id = 1
    mock_story.hn_id = 12345
    mock_story.title = "Test Story"
    mock_story.url = "https://example.com"
    mock_story.score = 100
    mock_story.time = None
    mock_story.user = None
    mock_story.descendants = 10
    mock_story.text = None
    mock_story.type = "story"
    
    mock_get_story.return_value = mock_story
    
    response = client.get("/api/stories/1")
    
    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["title"] == "Test Story"
    assert response.json()["score"] == 100


@patch("app.api.endpoints.stories.crud.get_story")
def test_get_story_not_found(mock_get_story, client, db_session):
    """Test the get_story endpoint with a non-existent story."""
    mock_get_story.return_value = None
    
    response = client.get("/api/stories/999")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Story not found"


@patch("app.api.endpoints.stories.crud.get_story")
@patch("app.api.endpoints.stories.crud.get_top_comments_for_story")
def test_get_story_comments(mock_get_top_comments, mock_get_story, client, db_session):
    """Test the get_story_comments endpoint."""
    mock_story = MagicMock()
    mock_story.story_id = 1
    mock_get_story.return_value = mock_story
    
    mock_comment = MagicMock()
    mock_comment.comment_id = 1
    mock_comment.hn_id = 67890
    mock_comment.text = "Test Comment"
    mock_comment.time = None
    mock_comment.user = None
    mock_comment.level = 0
    mock_comment.parent_id = None
    
    mock_get_top_comments.return_value = [mock_comment]
    
    response = client.get("/api/stories/1/comments")
    
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == 1
    assert response.json()[0]["text"] == "Test Comment"
    assert response.json()[0]["level"] == 0


@patch("app.api.endpoints.system.crud.get_last_refresh")
def test_get_system_status(mock_get_last_refresh, client, db_session):
    """Test the get_system_status endpoint."""
    mock_refresh = MagicMock()
    mock_refresh.refresh_id = 1
    mock_refresh.refresh_time = datetime.now()  # Use actual datetime instead of None
    mock_refresh.stories_refreshed = 5
    mock_refresh.comments_refreshed = 50
    mock_refresh.status = "success"
    mock_refresh.error_message = None
    
    mock_get_last_refresh.return_value = mock_refresh
    
    response = client.get("/api/system/status")
    
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["last_refresh"]["refresh_id"] == 1
    assert response.json()["last_refresh"]["status"] == "success"


@patch("app.api.endpoints.system.refresh_hackernews_data")
def test_trigger_refresh(mock_refresh, client, db_session):
    """Test the trigger_refresh endpoint."""
    mock_refresh.return_value = {"status": "refresh_started"}
    
    response = client.post("/api/system/refresh")
    
    assert response.status_code == 200
    assert response.json()["status"] == "refresh_started"
