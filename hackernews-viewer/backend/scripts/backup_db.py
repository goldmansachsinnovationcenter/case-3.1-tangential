"""Script to backup the HackerNews SQLite database."""
import logging
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(Path(settings.DATA_DIR) / "logs" / "backup.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def backup_database():
    """Backup the SQLite database to the backup directory."""
    db_url = settings.DATABASE_URL
    if not db_url.startswith("sqlite:///"):
        logger.error(f"Unsupported database URL: {db_url}")
        return False
    
    db_path = db_url.replace("sqlite:///", "")
    db_file = Path(db_path)
    
    if not db_file.exists():
        logger.error(f"Database file not found: {db_file}")
        return False
    
    backup_dir = Path(settings.BACKUP_DIR)
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"hackernews_{timestamp}.db"
    
    try:
        shutil.copy2(db_file, backup_file)
        logger.info(f"Database backup created: {backup_file}")
        
        cleanup_old_backups(backup_dir)
        
        return True
    except Exception as e:
        logger.exception(f"Error backing up database: {e}")
        return False


def cleanup_old_backups(backup_dir, keep=10):
    """Clean up old backups, keeping only the most recent ones."""
    try:
        backup_files = list(backup_dir.glob("hackernews_*.db"))
        
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        for old_file in backup_files[keep:]:
            old_file.unlink()
            logger.info(f"Removed old backup: {old_file}")
    except Exception as e:
        logger.exception(f"Error cleaning up old backups: {e}")


if __name__ == "__main__":
    logs_dir = Path(settings.DATA_DIR) / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting database backup")
    success = backup_database()
    if success:
        logger.info("Database backup completed successfully")
    else:
        logger.error("Database backup failed")
