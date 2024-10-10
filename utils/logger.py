import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name, log_file, level=logging.INFO):
    """Function to setup as many loggers as you want"""

    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
    
    # File handler
    file_handler = RotatingFileHandler(log_file, maxBytes=10000000, backupCount=5)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)

    # Get or create logger
    logger = logging.getLogger(name)
    
    # In case the logger already has handlers, remove them.
    if logger.hasHandlers():
        logger.handlers.clear()
    
    logger.setLevel(level)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Prevent the log messages from being propagated to the root logger
    logger.propagate = False

    return logger

# Create a default logger
default_logger = setup_logger('default', 'logs/app.log')

def get_logger(name=None):
    """Get a logger by name, or return the default logger"""
    if name:
        return setup_logger(name, f'logs/{name}.log')
    return default_logger