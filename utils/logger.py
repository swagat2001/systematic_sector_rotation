"""
Logging utility for the strategy
Provides structured logging with file rotation and different levels
"""

import logging
import sys
from pathlib import Path
from config import Config

def setup_logger(name=None):
    """
    Setup logger with configuration for both console and file output
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        logger: Configured logger instance
    """
    
    # Create logger
    logger = logging.getLogger(name or 'SectorRotationStrategy')
    logger.setLevel(getattr(logging, Config.LOG_LEVEL))
    
    # Clear existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Create formatters
    console_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, Config.LOG_LEVEL))
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    log_file = Config.LOG_DIR / "strategy.log"
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(getattr(logging, Config.LOG_LEVEL))
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Prevent propagation to avoid duplicate logs
    logger.propagate = False
    
    return logger
