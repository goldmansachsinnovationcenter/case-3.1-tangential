"""Tests for the Streamlit frontend components."""
import pytest
from unittest.mock import patch, MagicMock
import streamlit as st
from datetime import datetime
import pytz

from app.components.story_card import story_card, format_time
from app.components.comment_card import comment_card, comment_thread


def test_format_time():
    """Test the format_time function."""
    now = datetime.now(pytz.UTC)
    
    assert format_time(now.isoformat()) == "just now"
    
    minutes_ago = (now.replace(minute=now.minute - 5)).isoformat()
    assert "minute" in format_time(minutes_ago)
    
    hours_ago = (now.replace(hour=now.hour - 2)).isoformat()
    assert "hour" in format_time(hours_ago)
    
    days_ago = (now.replace(day=now.day - 3)).isoformat()
    assert "day" in format_time(days_ago)
    
    months_ago = (now.replace(month=(now.month - 2) % 12 or 12)).isoformat()
    assert "month" in format_time(months_ago)
    
    years_ago = (now.replace(year=now.year - 1)).isoformat()
    assert "year" in format_time(years_ago)


@patch("streamlit.container")
@patch("streamlit.columns")
@patch("streamlit.markdown")
@patch("streamlit.metric")
@patch("streamlit.button")
@patch("streamlit.expander")
def test_story_card(mock_expander, mock_button, mock_metric, mock_markdown, mock_columns, mock_container):
    """Test the story_card function."""
    story = {
        "id": 1,
        "title": "Test Story",
        "url": "https://example.com",
        "score": 100,
        "by": "testuser",
        "time": datetime.now(pytz.UTC).isoformat(),
        "descendants": 10,
        "text": "This is a test story"
    }
    
    story_card(story)
    
    mock_container.assert_called()
    mock_columns.assert_called()
    mock_markdown.assert_called()
    mock_metric.assert_called_with("Score", 100)
    mock_button.assert_called()


@patch("streamlit.container")
@patch("streamlit.columns")
@patch("streamlit.markdown")
def test_comment_card(mock_markdown, mock_columns, mock_container):
    """Test the comment_card function."""
    comment = {
        "id": 1,
        "text": "This is a test comment",
        "by": "testuser",
        "time": datetime.now(pytz.UTC).isoformat(),
        "level": 0
    }
    
    comment_card(comment)
    
    mock_container.assert_called()
    mock_markdown.assert_called()


@patch("app.components.comment_card.comment_card")
def test_comment_thread(mock_comment_card):
    """Test the comment_thread function."""
    comments = [
        {
            "id": 1,
            "text": "Top level comment",
            "by": "user1",
            "time": datetime.now(pytz.UTC).isoformat(),
            "level": 0,
            "parent_id": None
        },
        {
            "id": 2,
            "text": "Reply to top level",
            "by": "user2",
            "time": datetime.now(pytz.UTC).isoformat(),
            "level": 1,
            "parent_id": 1
        }
    ]
    
    comment_thread(comments)
    
    assert mock_comment_card.call_count >= 1
