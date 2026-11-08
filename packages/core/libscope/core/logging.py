"""
Structured logging configuration with credential redaction.
"""
import logging
import re
import sys
from typing import Any

# Patterns to sanitize from log output
REDACT_PATTERNS = [
    re.compile(r"(ghp_[a-zA-Z0-9]{36,})"),
    re.compile(r"(github_pat_[a-zA-Z0-9_]{50,})"),
    re.compile(r"(sk-or-v1-[a-zA-Z0-9]{50,})"),
    re.compile(r"(sk-[a-zA-Z0-9]{32,})"),
    re.compile(r"(AIzaSy[a-zA-Z0-9_\-]{33})"),
    re.compile(r"(Bearer\s+)[a-zA-Z0-9_\-\.]{20,}", re.IGNORECASE),
]


class SecretSanitizingFormatter(logging.Formatter):
    """Logging formatter that redacts detected API tokens and secrets."""

    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        sanitized = original
        for pattern in REDACT_PATTERNS:
            sanitized = pattern.sub(r"***REDACTED***", sanitized)
        return sanitized


def setup_logging(level: str = "INFO", json_format: bool = False) -> logging.Logger:
    """Configure root and libscope loggers with sanitization."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Avoid duplicate handlers if setup_logging is called multiple times
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)

        if json_format:
            fmt = '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
        else:
            fmt = "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"

        formatter = SecretSanitizingFormatter(fmt, datefmt="%Y-%m-%d %H:%M:%S")
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)

    # Silence verbose 3rd party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    return logging.getLogger("libscope")


def get_logger(name: str) -> logging.Logger:
    """Return a scoped logger under libscope."""
    return logging.getLogger(f"libscope.{name}")

