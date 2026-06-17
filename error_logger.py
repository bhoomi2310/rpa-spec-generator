import logging
import os
from datetime import datetime

LOG_FILE = "rpa_error_log.txt"

# Set up file logger
logger = logging.getLogger("RPALogger")
logger.setLevel(logging.DEBUG)

# File handler — appends to rpa_error_log.txt
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setLevel(logging.DEBUG)

# Console handler — prints to terminal
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)

formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

def log_info(message: str):
    logger.info(message)

def log_warning(message: str):
    logger.warning(message)

def log_error(message: str, exc: Exception = None):
    if exc:
        logger.error(f"{message} | Exception: {type(exc).__name__}: {str(exc)}")
    else:
        logger.error(message)

def log_success(message: str):
    logger.info(f"SUCCESS: {message}")

def get_log_contents() -> str:
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                return f.read()
        return "No log entries yet."
    except Exception as e:
        return f"Could not read log file: {e}"

def clear_log():
    try:
        open(LOG_FILE, "w").close()
    except:
        pass
