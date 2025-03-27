"""HackerNews API integration service."""
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

import httpx
from sqlmodel import Session

from app.core.config import settings
from app.db import crud, models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HackerNewsService:
    """Service for interacting with the HackerNews API."""

    def __init__(self, db: Session):
        """Initialize the service with a database session."""
        self.db = db
        self.base_url = settings.HACKERNEWS_API_URL
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def get_item(self, item_id: int) -> Optional[Dict[str, Any]]:
        """Get an item from the HackerNews API."""
        try:
            response = await self.client.get(f"{self.base_url}/item/{item_id}.json")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error fetching item {item_id}: {e}")
            return None

    async def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Get a user from the HackerNews API."""
        try:
            response = await self.client.get(f"{self.base_url}/user/{username}.json")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error fetching user {username}: {e}")
            return None

    async def get_top_stories(self) -> List[int]:
        """Get the IDs of the top stories from the HackerNews API."""
        try:
            response = await self.client.get(f"{self.base_url}/topstories.json")
            response.raise_for_status()
            return response.json()[:settings.TOP_STORIES_LIMIT]
        except httpx.HTTPError as e:
            logger.error(f"Error fetching top stories: {e}")
            return []

    async def process_user(self, username: str) -> Optional[int]:
        """Process a user and store in the database."""
        if not username:
            return None

        db_user = crud.get_user_by_username(self.db, username)
        if db_user:
            return db_user.user_id

        user_data = await self.get_user(username)
        if not user_data:
            db_user = crud.create_user(self.db, username)
            return db_user.user_id

        created_time = datetime.fromtimestamp(user_data.get("created", 0))
        db_user = crud.create_user(
            self.db,
            username=username,
            karma=user_data.get("karma"),
            created_time=created_time,
            about=user_data.get("about")
        )
        return db_user.user_id

    async def process_story(self, story_id: int, is_top: bool = False) -> Optional[int]:
        """Process a story and store in the database."""
        story_data = await self.get_item(story_id)
        if not story_data or story_data.get("type") != "story":
            logger.warning(f"Item {story_id} is not a valid story")
            return None

        by_user_id = await self.process_user(story_data.get("by"))

        db_story = crud.get_story_by_hn_id(self.db, story_id)
        if db_story:
            crud.update_story(
                self.db,
                db_story.story_id,
                {
                    "title": story_data.get("title", ""),
                    "url": story_data.get("url"),
                    "score": story_data.get("score"),
                    "descendants": story_data.get("descendants"),
                    "text": story_data.get("text"),
                    "is_top": is_top
                }
            )
            return db_story.story_id

        time_value = datetime.fromtimestamp(story_data.get("time", 0))
        db_story = crud.create_story(
            self.db,
            hn_id=story_id,
            title=story_data.get("title", ""),
            url=story_data.get("url"),
            score=story_data.get("score"),
            time=time_value,
            by_user_id=by_user_id,
            descendants=story_data.get("descendants"),
            text=story_data.get("text"),
            type=story_data.get("type"),
            is_top=is_top
        )
        return db_story.story_id

    async def process_comment(self, comment_id: int, level: int = 0) -> Optional[int]:
        """Process a comment and store in the database."""
        comment_data = await self.get_item(comment_id)
        if not comment_data or comment_data.get("type") != "comment":
            logger.warning(f"Item {comment_id} is not a valid comment")
            return None

        by_user_id = await self.process_user(comment_data.get("by"))

        db_comment = crud.get_comment_by_hn_id(self.db, comment_id)
        if db_comment:
            crud.update_comment(
                self.db,
                db_comment.comment_id,
                {
                    "text": comment_data.get("text"),
                    "level": level
                }
            )
            return db_comment.comment_id

        time_value = datetime.fromtimestamp(comment_data.get("time", 0))
        db_comment = crud.create_comment(
            self.db,
            hn_id=comment_id,
            text=comment_data.get("text"),
            time=time_value,
            by_user_id=by_user_id,
            parent_id=comment_data.get("parent"),
            level=level,
            is_top_comment=(level == 0)
        )
        return db_comment.comment_id

    async def process_story_comments(self, story_id: int, db_story_id: int) -> int:
        """Process comments for a story and store in the database."""
        story_data = await self.get_item(story_id)
        if not story_data or not story_data.get("kids"):
            return 0

        comment_ids = story_data.get("kids", [])[:settings.TOP_COMMENTS_LIMIT]
        processed_count = 0

        for rank, comment_id in enumerate(comment_ids):
            db_comment_id = await self.process_comment(comment_id, level=0)
            if db_comment_id:
                crud.link_story_comment(self.db, db_story_id, db_comment_id, rank)
                processed_count += 1

        return processed_count

    async def refresh_data(self) -> Dict[str, Any]:
        """Refresh data from the HackerNews API."""
        try:
            top_story_ids = await self.get_top_stories()
            if not top_story_ids:
                return self._log_refresh(0, 0, "error", "Failed to fetch top stories")

            db_story_ids = []
            for story_id in top_story_ids:
                db_story_id = await self.process_story(story_id, is_top=True)
                if db_story_id:
                    db_story_ids.append(db_story_id)

            crud.mark_top_stories(self.db, db_story_ids)

            total_comments = 0
            for i, story_id in enumerate(top_story_ids):
                if i < len(db_story_ids):
                    comments_count = await self.process_story_comments(story_id, db_story_ids[i])
                    total_comments += comments_count

            return self._log_refresh(len(db_story_ids), total_comments, "success")

        except Exception as e:
            logger.exception("Error refreshing data")
            return self._log_refresh(0, 0, "error", str(e))

    def _log_refresh(self, stories_count: int, comments_count: int, 
                    status: str, error_message: Optional[str] = None) -> Dict[str, Any]:
        """Log a refresh operation to the database."""
        log_entry = crud.log_refresh(
            self.db,
            stories_refreshed=stories_count,
            comments_refreshed=comments_count,
            status=status,
            error_message=error_message
        )
        
        return {
            "refresh_id": log_entry.refresh_id,
            "refresh_time": log_entry.refresh_time,
            "stories_refreshed": log_entry.stories_refreshed,
            "comments_refreshed": log_entry.comments_refreshed,
            "status": log_entry.status,
            "error_message": log_entry.error_message
        }


async def refresh_hackernews_data(db: Session) -> Dict[str, Any]:
    """Refresh HackerNews data in the database."""
    service = HackerNewsService(db)
    try:
        result = await service.refresh_data()
        return result
    finally:
        await service.close()
