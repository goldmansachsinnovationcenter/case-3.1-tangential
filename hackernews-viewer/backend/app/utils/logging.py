"""Utility functions for logging."""
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

from app.core.config import settings

logs_dir = Path(settings.DATA_DIR) / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)


def get_logger(name: str, log_file: str = None):
    """Get a configured logger instance.
    
    Args:
        name: The name of the logger
        log_file: The name of the log file (without path)
        
    Returns:
        A configured logger instance
    """
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.INFO)
    
    log_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)
    
    if log_file:
        file_path = logs_dir / log_file
        file_handler = RotatingFileHandler(
            file_path, 
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,              # Keep 5 backup files
            encoding="utf-8"
        )
        file_handler.setFormatter(log_format)
        logger.addHandler(file_handler)
    
    return logger
