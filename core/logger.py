"""
Process-Aware Logger using loguru with Selective Visual Markers
Linus: "Simple tools that do one thing well"

Design Principle: Less is more
- Emoji only at KEY MOMENTS (milestones, final status)
- Plain text for intermediate steps (use indentation for hierarchy)
- Visual noise = no visual signal
"""

import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from functools import lru_cache

from loguru import logger


# ============================================================
# Visual Markers - Use Sparingly
# ============================================================

# Final status ONLY (not for intermediate steps)
OK = "✓"                # Success - simple checkmark
FAIL = "✗"              # Failure - simple X
WARN = "!"              # Warning - exclamation

# Task completion markers (highly visible)
TASK_OK = "══ ✅ COMPLETE ══"
TASK_FAIL = "══ ❌ FAILED ══"

# System mode markers (KEY distinction)
SYS1 = "⚡"             # System 1: Fast/Intuitive
SYS2 = "🧠"             # System 2: Deep/Analytical

# Agent role markers
AGENT = {
    "planner": "▷",     # Planning
    "executor": "▶",    # Execution
    "reviewer": "◁",    # Review
}

# Phase identifiers (use at major transitions)
PHASE = {
    "kernel": "◆",      # System entry/exit
    "router": "◇",      # Routing decision
    "orchestrator": "◈", # Coordination
    "tool": "○",        # Tool call
}


# ============================================================
# Styled Logger - Minimal but Meaningful
# ============================================================

class StyledLogger:
    """
    Semantic logging with selective visual markers.

    Philosophy:
    - Markers at MILESTONES only (start/end of major phases)
    - Plain text for details (with indentation)
    - Status markers only for FINAL outcomes

    Usage:
        from core.logger import log

        log.milestone("Orchestration started")      # ◈ Orchestration started
        log.detail("agents", ["planner", "exec"])   #   agents: ['planner', 'exec']
        log.success("Task complete")                # ✓ Task complete
    """

    def __init__(self, base_logger):
        self._logger = base_logger

    # --- System Mode (KEY distinction) ---

    def system1(self, message: str, **kwargs):
        """Log System 1 (fast/intuitive) decision"""
        self._logger.info(f"{SYS1} [S1] {message}", **kwargs)

    def system2(self, message: str, **kwargs):
        """Log System 2 (deep/analytical) processing"""
        self._logger.info(f"{SYS2} [S2] {message}", **kwargs)

    # --- Agent Role ---

    def agent(self, role: str, message: str, **kwargs):
        """Log agent action with role marker"""
        marker = AGENT.get(role.lower(), "●")
        self._logger.info(f"{marker} [{role.capitalize()}] {message}", **kwargs)

    def agent_done(self, role: str, message: str, **kwargs):
        """Log agent completion"""
        marker = AGENT.get(role.lower(), "●")
        self._logger.info(f"{marker} [{role.capitalize()}] {message} {OK}", **kwargs)

    # --- Milestones (KEY MOMENTS) ---

    def milestone(self, message: str, phase: str = None, **kwargs):
        """Log a major milestone - USE SPARINGLY"""
        marker = PHASE.get(phase, "●") if phase else "●"
        self._logger.info(f"{marker} {message}", **kwargs)

    # --- Details (plain text with indentation) ---

    def detail(self, key: str, value: Any, indent: int = 1, **kwargs):
        """Log a detail - no emoji, just indentation"""
        prefix = "  " * indent
        self._logger.info(f"{prefix}{key}: {value}", **kwargs)

    def step(self, message: str, indent: int = 1, **kwargs):
        """Log a sub-step - plain text"""
        prefix = "  " * indent
        self._logger.info(f"{prefix}→ {message}", **kwargs)

    # --- Final Status (use markers) ---

    def success(self, message: str, **kwargs):
        """Log SUCCESS outcome - use at END of operation"""
        self._logger.info(f"{OK} {message}", **kwargs)

    def failure(self, message: str, **kwargs):
        """Log FAILURE outcome - use at END of operation"""
        self._logger.error(f"{FAIL} {message}", **kwargs)

    def warning(self, message: str, **kwargs):
        """Log WARNING - important issues only"""
        self._logger.warning(f"{WARN} {message}", **kwargs)

    # --- Task Completion (highly visible) ---

    def task_complete(self, message: str = "", duration_ms: float = None, **kwargs):
        """Log TASK COMPLETE - highly visible final marker"""
        self._logger.info("─" * 50, **kwargs)
        time_str = f" ({duration_ms:.0f}ms)" if duration_ms else ""
        self._logger.info(f"{TASK_OK}{time_str}", **kwargs)
        if message:
            self._logger.info(f"  {message}", **kwargs)
        self._logger.info("─" * 50, **kwargs)

    def task_failed(self, message: str = "", error: str = None, **kwargs):
        """Log TASK FAILED - highly visible final marker"""
        self._logger.info("─" * 50, **kwargs)
        self._logger.error(f"{TASK_FAIL}", **kwargs)
        if message:
            self._logger.error(f"  {message}", **kwargs)
        if error:
            self._logger.error(f"  Error: {error}", **kwargs)
        self._logger.info("─" * 50, **kwargs)

    # --- Plain passthrough (most common) ---

    def info(self, message: str, **kwargs):
        """Plain info - no markers"""
        self._logger.info(message, **kwargs)

    def debug(self, message: str, **kwargs):
        """Debug info"""
        self._logger.debug(message, **kwargs)

    def error(self, message: str, **kwargs):
        """Error without marker (use failure() for final status)"""
        self._logger.error(message, **kwargs)

    def exception(self, message: str, **kwargs):
        """Exception with traceback"""
        self._logger.exception(message, **kwargs)

    # --- Structural helpers ---

    def divider(self, width: int = 50):
        """Visual divider for major sections"""
        self._logger.info("─" * width)

    def section(self, title: str):
        """Section header"""
        self._logger.info(f"── {title} ──")


# ============================================================
# Logger Configuration
# ============================================================

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
    # Rotation strategy:
    # - File per day: run_YYYYMMDD.log
    # - When exceeds 5MB: rotate to run_YYYYMMDD.001.log, .002.log, etc.
    # - retention: Keep 7 days of logs
    #
    # Example file sequence:
    #   run_20260130.log      (current, being written)
    #   run_20260130.001.log  (first rotation when exceeded 5MB)
    #   run_20260130.002.log  (second rotation)
    #   run_20260129.log      (yesterday's log)
    logger.add(
        log_dir / "run_{time:YYYYMMDD}.log",
        level=file_level,
        format=_config.get("format_file", _DEFAULT_CONFIG["format_file"]),
        rotation="5 MB",       # Rotate when file exceeds 5MB
        retention="7 days",    # Keep logs for 7 days
        filter=lambda record: "run_id" in record["extra"],
        encoding="utf-8",
        errors="replace",
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

        # Only mark final status, not intermediate timings
        if success:
            logger.info(f"{self.event} ({duration_ms:.0f}ms) {OK}")
        else:
            logger.error(f"{self.event} ({duration_ms:.0f}ms) {FAIL} {exc_val}")

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

# Create styled logger instance
log = StyledLogger(logger)


# Convenience exports
__all__ = [
    # Core logger
    "logger",
    "log",  # Styled logger with selective markers
    "configure",
    "contextualize",
    "bind",
    "get_logger",
    "timer",
    # Markers for custom usage
    "OK", "FAIL", "WARN",
    "SYS1", "SYS2",
    "AGENT", "PHASE",
    "StyledLogger",
]
