"""Script to refresh HackerNews data for cron job."""
import asyncio
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.services.hackernews import refresh_hackernews_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(Path(__file__).resolve().parent.parent / "logs" / "refresh.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def main():
    """Main function to refresh data."""
    logger.info("Starting data refresh")
    
    logs_dir = Path(__file__).resolve().parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    db = SessionLocal()
    try:
        result = await refresh_hackernews_data(db)
        logger.info(f"Data refresh completed: {result}")
    except Exception as e:
        logger.exception("Error refreshing data")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
