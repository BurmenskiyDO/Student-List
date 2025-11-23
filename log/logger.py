# logging/logger.py
import os
import logging
from logging.handlers import RotatingFileHandler

LOG_FILE = os.path.join(os.path.dirname(__file__), "logs", "app.log")

formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def create_rotating_logger(name: str, level=logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        handler = RotatingFileHandler(LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


students_logger = create_rotating_logger("students_logger")
grades_logger = create_rotating_logger("grades_logger")
