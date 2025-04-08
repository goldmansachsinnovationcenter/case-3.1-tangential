"""Application configuration."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application settings."""
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "HackerNews Viewer"

    DATA_DIR: str = os.getenv("DATA_DIR", f"{ROOT_DIR}/data")
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/hackernews.db")
    
    HACKERNEWS_API_URL: str = "https://hacker-news.firebaseio.com/v0"
    
    TOP_STORIES_LIMIT: int = 5
    TOP_COMMENTS_LIMIT: int = 10
    
    BACKUP_DIR: str = os.getenv("BACKUP_DIR", f"{DATA_DIR}/backups")
    
    class Config:
        """Pydantic config."""
        env_file = "../../.env"  # Updated path to point to hackernews-viewer/.env
        case_sensitive = True


settings = Settings()
