# src/core/logger.py - Simple version

import logging
import sys

def setup_logging():
    """Configure simple logging for Docker"""
    logger = logging.getLogger("ai-magento-api")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger