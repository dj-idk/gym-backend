import sys
import contextvars
import os

from loguru import logger

request_id_var = contextvars.ContextVar("request_id", default="main")


def setup_logging():
    """Configure Loguru for the application"""
    logger.remove()

    os.makedirs("logs", exist_ok=True)

    def request_id_filter(record):
        if "request_id" not in record["extra"]:
            record["extra"]["request_id"] = request_id_var.get()
        return True

    logger.add(
        sys.stderr,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {extra[request_id]} | {message}",
        level="INFO",
        backtrace=True,
        diagnose=True,
        filter=request_id_filter,
    )

    logger.add(
        "logs/app.log",
        rotation="10 MB",  # Rotate when file reaches 10MB
        retention="1 week",  # Keep logs for 1 week
        compression="zip",  # Compress rotated logs
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {extra[request_id]} | {message}",
        level="INFO",
        backtrace=True,
        diagnose=True,
        filter=request_id_filter,
    )

    logger.add(
        "logs/error.log",
        rotation="10 MB",
        retention="1 month",  # Keep error logs longer
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {extra[request_id]} | {message}",
        level="ERROR",
        backtrace=True,
        diagnose=True,
        filter=request_id_filter,
    )

    return logger


logger = setup_logging()
