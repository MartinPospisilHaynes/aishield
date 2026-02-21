"""
AIshield.cz — Structured Logging & Request Context

Robustní logovací systém s DVOJITÝM výstupem:
  1. stdout  → zachyceno systemd journalem (journalctl -u aishield-api)
  2. soubor  → /var/log/aishield.log (rotovaný, NIKDY se nepřepíše)

Každý request dostane unikátní request_id propagované přes contextvars.
Logy jsou strukturované JSON v produkci, plain text pro lokální vývoj.
"""

import json
import logging
import os
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

# ── Context variable for request_id propagation ──
# Set in middleware, readable anywhere in the same async context.
_request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

# ── Log file paths ──
LOG_DIR = Path(os.getenv("AISHIELD_LOG_DIR", "/var/log"))
MAIN_LOG = LOG_DIR / "aishield.log"
ERROR_LOG = LOG_DIR / "aishield-errors.log"


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
        for key in ("scan_id", "client_id", "url", "elapsed_ms", "status_code",
                     "company_id", "email", "error_type", "endpoint"):
            val = getattr(record, key, None)
            if val is not None:
                log_entry[key] = val

        return json.dumps(log_entry, ensure_ascii=False, default=str)


def setup_logging(*, level: int = logging.INFO, json_format: bool = True) -> None:
    """
    Configure centralized logging for the entire application.

    DUAL OUTPUT:
      1. stdout handler  → systemd journal (vždy běží)
      2. file handler    → /var/log/aishield.log (rotovaný, 10 MB × 5 souborů = max 50 MB)
      3. error file      → /var/log/aishield-errors.log (jen WARNING+, rotovaný)

    Args:
        level: Log level (default INFO)
        json_format: If True, use JSON formatter. If False, use plain text
                     (useful for local dev).
    """
    root = logging.getLogger()
    root.setLevel(level)

    # Remove any existing handlers
    root.handlers.clear()

    # ── Formatter ──
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-7s | %(name)s | [%(request_id)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            defaults={"request_id": "-"},
        )

    # ── 1. stdout handler (systemd journal / konzole) ──
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(level)
    stdout_handler.setFormatter(formatter)
    root.addHandler(stdout_handler)

    # ── 2. file handler — hlavní log (ALL levels) ──
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            str(MAIN_LOG),
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,              # Uchovává 5 rotovaných souborů
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
    except (PermissionError, OSError) as e:
        # Pokud nemáme oprávnění k zápisu (dev prostředí), pokračujeme jen s stdout
        print(f"[logging] WARNING: Cannot write to {MAIN_LOG}: {e}", file=sys.stderr)

    # ── 3. error file handler — jen WARNING a vyšší ──
    try:
        error_handler = RotatingFileHandler(
            str(ERROR_LOG),
            maxBytes=5 * 1024 * 1024,   # 5 MB
            backupCount=3,              # Uchovává 3 rotované soubory
            encoding="utf-8",
        )
        error_handler.setLevel(logging.WARNING)
        error_handler.setFormatter(formatter)
        root.addHandler(error_handler)
    except (PermissionError, OSError):
        pass  # Dev prostředí — neblokujeme

    # Silence noisy libraries
    for name in ("httpx", "httpcore", "hpack", "urllib3", "multipart"):
        logging.getLogger(name).setLevel(logging.WARNING)
