"""Script to refresh HackerNews data for cron job."""
import asyncio
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db, engine
from app.services.hackernews import refresh_hackernews_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(Path(settings.DATA_DIR) / "logs" / "refresh.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def main():
    """Main function to refresh data."""
    logger.info("Starting data refresh")
    
    logs_dir = Path(settings.DATA_DIR) / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    with Session(engine) as db:
        try:
            result = await refresh_hackernews_data(db)
            logger.info(f"Data refresh completed: {result}")
        except Exception as e:
            logger.exception("Error refreshing data")


if __name__ == "__main__":
    asyncio.run(main())
