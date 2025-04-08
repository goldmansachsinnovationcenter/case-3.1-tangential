"""Utility functions for database backup and restore operations."""
import logging
import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

logs_dir = Path(settings.DATA_DIR) / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)

file_handler = logging.FileHandler(logs_dir / "backup.log")
logger.addHandler(file_handler)


def ensure_backup_dir() -> Path:
    """Ensure the backup directory exists and return its path."""
    backup_dir = Path(settings.BACKUP_DIR)
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def get_db_path() -> Path:
    """Get the path to the database file."""
    data_dir = Path(settings.DATA_DIR)
    data_dir.mkdir(parents=True, exist_ok=True)
    
    db_url = settings.DATABASE_URL
    if not db_url.startswith("sqlite:///"):
        logger.error(f"Unsupported database URL: {db_url}")
        raise ValueError(f"Unsupported database URL: {db_url}")
        
    return Path(db_url.replace("sqlite:///", ""))


def cleanup_old_backups(keep: int = 10) -> None:
    """Clean up old backups, keeping only the most recent ones.
    
    Args:
        keep: Number of recent backups to keep.
    """
    try:
        backup_dir = ensure_backup_dir()
        backup_files = list(backup_dir.glob("hackernews_*.db"))
        
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        for old_file in backup_files[keep:]:
            old_file.unlink()
            logger.info(f"Removed old backup: {old_file}")
    except Exception as e:
        logger.exception(f"Error cleaning up old backups: {e}")


def create_backup() -> Dict[str, Any]:
    """Create a backup of the current database.
    
    Returns:
        Dict with backup metadata including filename, timestamp, and size.
        
    Raises:
        FileNotFoundError: If the database file doesn't exist.
        Exception: If the backup operation fails.
    """
    try:
        db_path = get_db_path()
        if not db_path.exists():
            logger.error(f"Database file not found at {db_path}")
            raise FileNotFoundError(f"Database file not found at {db_path}")
        
        backup_dir = ensure_backup_dir()
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        backup_filename = f"hackernews_{timestamp}.db"
        backup_path = backup_dir / backup_filename
        
        shutil.copy2(db_path, backup_path)
        logger.info(f"Database backup created: {backup_path}")
        
        file_size = backup_path.stat().st_size
        
        cleanup_old_backups()
        
        return {
            "filename": backup_filename,
            "path": str(backup_path),
            "timestamp": timestamp,
            "created_at": datetime.utcnow().isoformat(),
            "size_bytes": file_size
        }
    except Exception as e:
        logger.exception(f"Error backing up database: {e}")
        raise


def list_backups() -> List[Dict[str, Any]]:
    """List all available database backups.
    
    Returns:
        List of dictionaries with backup metadata.
    """
    backup_dir = ensure_backup_dir()
    backups = []
    
    for backup_file in backup_dir.glob("hackernews_*.db"):
        try:
            timestamp = backup_file.name.replace("hackernews_", "").replace(".db", "")
            created_at = datetime.strptime(timestamp, "%Y%m%d%H%M%S")
            
            backups.append({
                "filename": backup_file.name,
                "path": str(backup_file),
                "timestamp": timestamp,
                "created_at": created_at.isoformat(),
                "size_bytes": backup_file.stat().st_size
            })
        except (ValueError, OSError) as e:
            logger.warning(f"Skipping invalid backup file: {backup_file} - {str(e)}")
            continue
    
    return sorted(backups, key=lambda x: x["timestamp"], reverse=True)


def get_backup_by_filename(filename: str) -> Optional[Dict[str, Any]]:
    """Get backup metadata by filename.
    
    Args:
        filename: The backup filename to find.
        
    Returns:
        Dictionary with backup metadata or None if not found.
    """
    backups = list_backups()
    for backup in backups:
        if backup["filename"] == filename:
            return backup
    return None


def validate_backup(backup_path: Path) -> bool:
    """Validate that a backup file is a valid SQLite database.
    
    Args:
        backup_path: Path to the backup file.
        
    Returns:
        True if valid, False otherwise.
    """
    if not backup_path.exists() or backup_path.stat().st_size == 0:
        logger.error(f"Backup file does not exist or is empty: {backup_path}")
        return False
    
    try:
        conn = sqlite3.connect(str(backup_path))
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        conn.close()
        
        is_valid = result and result[0] == "ok"
        if not is_valid:
            logger.error(f"Backup file failed integrity check: {backup_path}")
        return is_valid
    except sqlite3.Error as e:
        logger.error(f"Error validating backup file: {backup_path} - {str(e)}")
        return False


def restore_from_backup(filename: str) -> Dict[str, Any]:
    """Restore the database from a backup file.
    
    Args:
        filename: The backup filename to restore from.
        
    Returns:
        Dictionary with restore operation metadata.
        
    Raises:
        FileNotFoundError: If the backup file doesn't exist.
        ValueError: If the backup file is invalid.
    """
    try:
        logger.info(f"Starting database restore from: {filename}")
        
        backup = get_backup_by_filename(filename)
        if not backup:
            logger.error(f"Backup file not found: {filename}")
            raise FileNotFoundError(f"Backup file not found: {filename}")
        
        backup_path = Path(backup["path"])
        if not validate_backup(backup_path):
            logger.error(f"Invalid backup file: {filename}")
            raise ValueError(f"Invalid backup file: {filename}")
        
        db_path = get_db_path()
        
        temp_backup = None
        if db_path.exists():
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            temp_backup_path = ensure_backup_dir() / f"pre_restore_{timestamp}.db"
            shutil.copy2(db_path, temp_backup_path)
            temp_backup = str(temp_backup_path)
            logger.info(f"Created safety backup before restore: {temp_backup_path}")
        
        shutil.copy2(backup_path, db_path)
        logger.info(f"Database successfully restored from: {filename}")
        
        return {
            "success": True,
            "restored_from": filename,
            "restored_at": datetime.utcnow().isoformat(),
            "temp_backup": temp_backup
        }
    except Exception as e:
        logger.exception(f"Error restoring database: {e}")
        raise
