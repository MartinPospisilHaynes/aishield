"""
AIshield.cz — Structured Logging & Request Context
Provides:
  - JSON log formatter for machine-parseable logs
  - request_id propagation via contextvars (available in any handler/module)
"""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone

# ── Context variable for request_id propagation ──
# Set in middleware, readable anywhere in the same async context.
_request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


def get_request_id() -> str:
    """Get the current request_id from context (or '-' if not in a request)."""
    return _request_id_var.get()


def set_request_id(request_id: str) -> None:
    """Set request_id in the current async context."""
    _request_id_var.set(request_id)


class JSONFormatter(logging.Formatter):
    """
    Structured JSON log formatter.
    Each log line is a single JSON object with consistent fields:
      {"ts", "level", "logger", "msg", "request_id", ...extra}

    Benefits:
      - Machine-parseable by Loki, Datadog, CloudWatch, jq
      - request_id automatically injected from contextvars
      - Exception info included as "exc" field
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ"
            ),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": _request_id_var.get(),
        }

        # Include exception traceback if present
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exc"] = self.formatException(record.exc_info)

        # Include extra fields if passed via `logger.info("msg", extra={...})`
        for key in ("scan_id", "client_id", "url", "elapsed_ms", "status_code"):
            val = getattr(record, key, None)
            if val is not None:
                log_entry[key] = val

        return json.dumps(log_entry, ensure_ascii=False, default=str)


def setup_logging(*, level: int = logging.INFO, json_format: bool = True) -> None:
    """
    Configure centralized logging for the entire application.

    Args:
        level: Log level (default INFO)
        json_format: If True, use JSON formatter. If False, use plain text
                     (useful for local dev).
    """
    root = logging.getLogger()
    root.setLevel(level)

    # Remove any existing handlers
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    if json_format:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-7s | %(name)s | [%(request_id)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            defaults={"request_id": "-"},
        ))

    root.addHandler(handler)

    # Silence noisy libraries
    for name in ("httpx", "httpcore", "hpack", "urllib3", "multipart"):
        logging.getLogger(name).setLevel(logging.WARNING)
