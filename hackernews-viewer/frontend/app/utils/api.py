"""API client for the HackerNews Viewer backend."""
import os
from typing import List, Dict, Any, Optional
import httpx
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000/api")


async def get_top_stories(limit: int = 5) -> List[Dict[str, Any]]:
    """Get top stories from the API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_URL}/stories/top?limit={limit}")
        response.raise_for_status()
        return response.json()


async def get_story(story_id: int) -> Dict[str, Any]:
    """Get a specific story from the API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_URL}/stories/{story_id}")
        response.raise_for_status()
        return response.json()


async def get_story_comments(story_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """Get comments for a specific story from the API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_URL}/stories/{story_id}/comments?limit={limit}")
        response.raise_for_status()
        return response.json()


async def get_user(username: str) -> Dict[str, Any]:
    """Get a user from the API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_URL}/users/{username}")
        response.raise_for_status()
        return response.json()


async def get_system_status() -> Dict[str, Any]:
    """Get system status from the API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_URL}/system/status")
        response.raise_for_status()
        return response.json()


async def trigger_refresh() -> Dict[str, Any]:
    """Trigger a manual refresh of the data."""
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{API_URL}/system/refresh")
        response.raise_for_status()
        return response.json()
