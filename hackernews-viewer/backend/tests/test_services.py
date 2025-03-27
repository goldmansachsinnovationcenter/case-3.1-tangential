"""Tests for the HackerNews service."""
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

from app.services.hackernews import HackerNewsService, refresh_hackernews_data


@pytest.fixture
def mock_db():
    """Mock database session."""
    return MagicMock()


@pytest.fixture
def hn_service(mock_db):
    """HackerNews service with mocked database."""
    service = HackerNewsService(mock_db)
    return service


@pytest.mark.asyncio
async def test_get_item(hn_service):
    """Test the get_item method."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "id": 12345,
        "title": "Test Story",
        "by": "testuser",
        "score": 100,
        "time": 1616161616,
        "type": "story"
    }
    mock_response.raise_for_status = AsyncMock()
    
    hn_service.client.get = AsyncMock(return_value=mock_response)
    
    result = await hn_service.get_item(12345)
    
    assert result["id"] == 12345
    assert result["title"] == "Test Story"
    assert result["score"] == 100
    
    hn_service.client.get.assert_called_once_with(f"{hn_service.base_url}/item/12345.json")


@pytest.mark.asyncio
async def test_get_user(hn_service):
    """Test the get_user method."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "id": "testuser",
        "karma": 1000,
        "created": 1616161616,
        "about": "Test user"
    }
    mock_response.raise_for_status = AsyncMock()
    
    hn_service.client.get = AsyncMock(return_value=mock_response)
    
    result = await hn_service.get_user("testuser")
    
    assert result["id"] == "testuser"
    assert result["karma"] == 1000
    assert result["about"] == "Test user"
    
    hn_service.client.get.assert_called_once_with(f"{hn_service.base_url}/user/testuser.json")


@pytest.mark.asyncio
async def test_get_top_stories(hn_service):
    """Test the get_top_stories method."""
    mock_response = MagicMock()
    mock_response.json.return_value = [12345, 67890, 54321, 98765, 13579]
    mock_response.raise_for_status = AsyncMock()
    
    hn_service.client.get = AsyncMock(return_value=mock_response)
    
    result = await hn_service.get_top_stories()
    
    assert len(result) == 5
    assert result[0] == 12345
    assert result[4] == 13579
    
    hn_service.client.get.assert_called_once_with(f"{hn_service.base_url}/topstories.json")


@pytest.mark.asyncio
async def test_process_user(hn_service):
    """Test the process_user method."""
    mock_exec_result = MagicMock()
    mock_exec_result.first.return_value = None
    hn_service.db.exec = MagicMock(return_value=mock_exec_result)
    
    hn_service.get_user = AsyncMock(return_value={
        "id": "testuser",
        "karma": 1000,
        "created": 1616161616,
        "about": "Test user"
    })
    
    mock_user = MagicMock()
    mock_user.user_id = 1
    hn_service.db.add = MagicMock()
    hn_service.db.commit = MagicMock()
    hn_service.db.refresh = MagicMock()
    
    with patch("app.services.hackernews.crud.create_user", return_value=mock_user) as mock_create_user:
        result = await hn_service.process_user("testuser")
        
        assert result == 1
        
        mock_create_user.assert_called_once()
        assert mock_create_user.call_args[0][0] == hn_service.db
        assert mock_create_user.call_args[1]["username"] == "testuser"
        assert mock_create_user.call_args[1]["karma"] == 1000


@pytest.mark.asyncio
async def test_process_story(hn_service):
    """Test the process_story method."""
    hn_service.get_item = AsyncMock(return_value={
        "id": 12345,
        "title": "Test Story",
        "by": "testuser",
        "score": 100,
        "time": 1616161616,
        "type": "story",
        "url": "https://example.com",
        "descendants": 10
    })
    
    hn_service.process_user = AsyncMock(return_value=1)
    
    mock_exec_result = MagicMock()
    mock_exec_result.first.return_value = None
    hn_service.db.exec = MagicMock(return_value=mock_exec_result)
    
    mock_story = MagicMock()
    mock_story.story_id = 1
    
    with patch("app.services.hackernews.crud.create_story", return_value=mock_story) as mock_create_story:
        result = await hn_service.process_story(12345, is_top=True)
        
        assert result == 1
        
        mock_create_story.assert_called_once()
        assert mock_create_story.call_args[0][0] == hn_service.db
        assert mock_create_story.call_args[1]["hn_id"] == 12345
        assert mock_create_story.call_args[1]["title"] == "Test Story"
        assert mock_create_story.call_args[1]["score"] == 100
        assert mock_create_story.call_args[1]["by_user_id"] == 1
        assert mock_create_story.call_args[1]["is_top"] == True


@pytest.mark.asyncio
async def test_refresh_data(hn_service):
    """Test the refresh_data method."""
    hn_service.get_top_stories = AsyncMock(return_value=[12345, 67890])
    
    hn_service.process_story = AsyncMock(side_effect=[1, 2])
    
    hn_service.process_story_comments = AsyncMock(return_value=5)
    
    with patch("app.services.hackernews.crud.mark_top_stories") as mock_mark_top_stories:
        mock_log = MagicMock()
        mock_log.refresh_id = 1
        mock_log.refresh_time = datetime.now()
        mock_log.stories_refreshed = 2
        mock_log.comments_refreshed = 10
        mock_log.status = "success"
        mock_log.error_message = None
        
        with patch("app.services.hackernews.crud.log_refresh", return_value=mock_log) as mock_log_refresh:
            result = await hn_service.refresh_data()
            
            assert result["refresh_id"] == 1
            assert result["stories_refreshed"] == 2
            assert result["comments_refreshed"] == 10
            assert result["status"] == "success"
            
            mock_mark_top_stories.assert_called_once_with(hn_service.db, [1, 2])
            
            mock_log_refresh.assert_called_once()
            assert mock_log_refresh.call_args[0][0] == hn_service.db
            assert mock_log_refresh.call_args[1]["stories_refreshed"] == 2
            assert mock_log_refresh.call_args[1]["comments_refreshed"] == 10
            assert mock_log_refresh.call_args[1]["status"] == "success"


@pytest.mark.asyncio
async def test_refresh_hackernews_data(mock_db):
    """Test the refresh_hackernews_data function."""
    mock_service = MagicMock()
    mock_service.refresh_data = AsyncMock(return_value={"status": "success"})
    mock_service.close = AsyncMock()
    
    with patch("app.services.hackernews.HackerNewsService", return_value=mock_service):
        result = await refresh_hackernews_data(mock_db)
        
        assert result["status"] == "success"
        
        mock_service.refresh_data.assert_called_once()
        mock_service.close.assert_called_once()
