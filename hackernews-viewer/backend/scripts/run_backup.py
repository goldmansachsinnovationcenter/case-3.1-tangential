"""Script to backup the HackerNews SQLite database.

This script calls the backup utility functions in app.utils.backup
to create a backup of the current database.
"""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.utils.backup import create_backup, logger

def main():
    """Main function to backup the database."""
    logger.info("Starting database backup")
    try:
        backup_info = create_backup()
        logger.info(f"Database backup completed successfully: {backup_info['filename']}")
        return True
    except Exception as e:
        logger.error(f"Database backup failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
