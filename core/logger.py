"""
Process-Aware Logger using loguru
Linus: "Simple tools that do one thing well"
"""

import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from functools import lru_cache

from loguru import logger


# Remove default handler to configure our own
logger.remove()

# Default configuration
_DEFAULT_CONFIG = {
    "console_level": "INFO",
    "file_level": "DEBUG",
    "log_dir": "workspace/logs",
    "format_console": "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{extra[run_id]}</cyan> | <level>{message}</level>",
    "format_file": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {extra[run_id]} | {name}:{function}:{line} | {message}",
}

# Global config cache
_config: Dict[str, Any] = {}


def _get_log_dir() -> Path:
    """Get log directory from config or environment."""
    log_dir = _config.get("log_dir") or os.getenv("LOG_DIR", _DEFAULT_CONFIG["log_dir"])
    path = Path(log_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def configure(config: Optional[Dict[str, Any]] = None) -> None:
    """
    Configure logger with custom settings.

    Args:
        config: Dictionary with logging configuration:
            - console_level: Log level for console (default: INFO)
            - file_level: Log level for file (default: DEBUG)
            - log_dir: Directory for log files (default: workspace/logs)
    """
    global _config

    if config:
        _config = {**_DEFAULT_CONFIG, **config}
    else:
        _config = _DEFAULT_CONFIG.copy()

    # Remove any existing handlers
    logger.remove()

    # Get configuration values
    console_level = _config.get("console_level", "INFO")
    file_level = _config.get("file_level", "DEBUG")
    log_dir = _get_log_dir()

    # Console handler - concise format for developers
    logger.add(
        sys.stderr,
        level=console_level,
        format=_config.get("format_console", _DEFAULT_CONFIG["format_console"]),
        filter=lambda record: "run_id" in record["extra"],
        colorize=True,
    )

    # File handler - detailed format for debugging
    # encoding="utf-8" with errors="replace" handles invalid Unicode (surrogates)
    logger.add(
        log_dir / "run_{time:YYYYMMDD_HHmmss}.log",
        level=file_level,
        format=_config.get("format_file", _DEFAULT_CONFIG["format_file"]),
        rotation="10 MB",
        retention="7 days",
        compression="gz",
        filter=lambda record: "run_id" in record["extra"],
        encoding="utf-8",
        errors="replace",  # Replace invalid chars instead of raising error
    )

    # Fallback handler for logs without run_id
    logger.add(
        sys.stderr,
        level=console_level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        filter=lambda record: "run_id" not in record["extra"],
        colorize=True,
    )


def get_logger():
    """
    Get the configured logger instance.

    Returns:
        loguru.Logger: Configured logger instance
    """
    return logger


# Context manager for run_id binding
class LogContext:
    """Context manager for binding run_id to log messages."""

    def __init__(self, run_id: str, **extra):
        """
        Initialize log context.

        Args:
            run_id: Unique identifier for the execution run
            **extra: Additional context to bind (e.g., agent="ExecutorAgent")
        """
        self.run_id = run_id
        self.extra = {"run_id": run_id, **extra}
        self._token = None

    def __enter__(self):
        self._token = logger.contextualize(**self.extra)
        self._token.__enter__()
        return self

    def __exit__(self, *args):
        if self._token:
            self._token.__exit__(*args)


def contextualize(run_id: str, **extra):
    """
    Create a context for logging with run_id bound.

    Args:
        run_id: Unique identifier for the execution run
        **extra: Additional context to bind

    Returns:
        LogContext: Context manager for the logging context

    Example:
        with contextualize(run_id="run_abc123", agent="Executor"):
            logger.info("Processing task")  # Will include run_id and agent
    """
    return LogContext(run_id, **extra)


def bind(**kwargs):
    """
    Bind additional context to the logger.

    Args:
        **kwargs: Key-value pairs to bind

    Returns:
        Bound logger instance
    """
    return logger.bind(**kwargs)


class Timer:
    """Context manager for timing operations."""

    def __init__(self, event: str, **kwargs):
        """
        Initialize timer.

        Args:
            event: Name of the operation being timed
            **kwargs: Additional context to log
        """
        self.event = event
        self.kwargs = kwargs
        self.start = None

    def __enter__(self):
        import time
        self.start = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        duration_ms = (time.time() - self.start) * 1000
        success = exc_type is None

        if success:
            logger.info(f"{self.event} ({duration_ms:.0f}ms) ✓")
        else:
            logger.error(f"{self.event} ({duration_ms:.0f}ms) ✗ - {exc_val}")

        return False  # Don't suppress exceptions


def timer(event: str, **kwargs):
    """
    Create a timer context manager for timing operations.

    Args:
        event: Name of the operation being timed
        **kwargs: Additional context to log

    Returns:
        Timer: Context manager that logs duration on exit

    Example:
        with timer("database.query"):
            result = db.execute(query)
        # Logs: "database.query (123ms) ✓"
    """
    return Timer(event, **kwargs)


# Initialize with default configuration
configure()


# Convenience exports
__all__ = ["logger", "configure", "contextualize", "bind", "get_logger", "timer"]
