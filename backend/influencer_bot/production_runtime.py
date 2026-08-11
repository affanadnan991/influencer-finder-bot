"""Production-oriented runtime helpers for the influencer discovery engine."""

from __future__ import annotations

import json
import logging
import os
import queue
import sqlite3
import tempfile
import threading
import time
from datetime import datetime
from typing import Any, Callable, Optional

from config import OUTPUT_DIR, TIMEOUT


class StructuredLogger:
    """Write structured JSONL logs with a stable run identifier."""

    def __init__(self, run_id: Optional[str] = None, log_dir: Optional[str] = None):
        self.run_id = run_id or datetime.now().strftime("%Y%m%d-%H%M%S")
        self.log_dir = log_dir or OUTPUT_DIR
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_path = os.path.join(self.log_dir, f"{self.run_id}.jsonl")
        self._lock = threading.Lock()
        self._python_logger = logging.getLogger(f"influencer_bot.{self.run_id}")
        self._python_logger.setLevel(logging.INFO)
        self._python_logger.propagate = False
        if not self._python_logger.handlers:
            handler = logging.FileHandler(self.log_path)
            handler.setFormatter(logging.Formatter("%(message)s"))
            self._python_logger.addHandler(handler)

    def _write(self, level: str, message: str, **context: Any) -> None:
        payload = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "run_id": self.run_id,
            "level": level,
            "message": message,
            **context,
        }
        with self._lock:
            with open(self.log_path, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
            self._python_logger.info(json.dumps(payload, ensure_ascii=False))

    def info(self, message: str, **context: Any) -> None:
        self._write("INFO", message, **context)

    def warning(self, message: str, **context: Any) -> None:
        self._write("WARNING", message, **context)

    def error(self, message: str, **context: Any) -> None:
        self._write("ERROR", message, **context)


def retry_with_backoff(operation: Callable[[], Any], max_attempts: int = 3, base_delay: float = 1.0, retryable_errors: Optional[tuple[type[Exception], ...]] = None):
    """Retry an operation with exponential backoff and jitter for transient failures."""
    retryable_errors = retryable_errors or (TimeoutError, ConnectionError, RuntimeError)
    last_error: Optional[Exception] = None
    for attempt in range(1, max_attempts + 1):
        try:
            return operation()
        except retryable_errors as exc:  # type: ignore[misc]
            last_error = exc
            if attempt >= max_attempts:
                break
            delay = base_delay * (2 ** (attempt - 1)) + (0.1 * attempt)
            time.sleep(delay)
    if last_error is not None:
        raise last_error
    raise RuntimeError("retry_with_backoff exhausted without a result")


class BrowserManager:
    """Central browser lifecycle manager for the discovery engine."""

    def __init__(self, allow_browser_start: bool = True, browser_factory: Optional[Callable[[], Any]] = None):
        self.allow_browser_start = allow_browser_start
        self.browser_factory = browser_factory
        self.browser = None
        self.context = None
        self.page = None
        self.lock = threading.Lock()

    def ensure_browser(self):
        if self.browser and self.context and self.page:
            return True
        if not self.allow_browser_start:
            return False
        if self.browser_factory is None:
            return False
        with self.lock:
            if self.browser and self.context and self.page:
                return True
            self.browser, self.context, self.page = self.browser_factory()
            return True

    def reset(self):
        self.browser = None
        self.context = None
        self.page = None


class CAPTCHAState:
    """Tracks CAPTCHA handling state for a run without blocking the whole process."""

    def __init__(self):
        self.waiting = False
        self.last_error = None
        self.lock = threading.Lock()

    def mark_waiting(self, value: bool = True, error: Optional[Exception] = None):
        with self.lock:
            self.waiting = value
            self.last_error = error

    def is_waiting(self) -> bool:
        with self.lock:
            return self.waiting


class URLWorkQueue:
    """A lightweight queue for discovery URLs that can be processed by workers."""

    def __init__(self):
        self._queue = queue.Queue()

    def enqueue(self, item: Any) -> None:
        self._queue.put(item)

    def dequeue(self, block: bool = True, timeout: Optional[float] = None) -> Any:
        return self._queue.get(block=block, timeout=timeout)

    def size(self) -> int:
        return self._queue.qsize()


class VisitedCache:
    """Persist visited profile URLs in SQLite so repeated work is skipped."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.path.join(OUTPUT_DIR, "visited_cache.db")
        os.makedirs(os.path.dirname(self.db_path) or OUTPUT_DIR, exist_ok=True)
        self._initialize()

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS visited_urls (url TEXT PRIMARY KEY, visited_at TEXT NOT NULL)"
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def mark_visited(self, url: str) -> None:
        if not url:
            return
        timestamp = datetime.now().isoformat(timespec="seconds")
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO visited_urls (url, visited_at) VALUES (?, ?)",
                (url, timestamp),
            )

    def is_visited(self, url: str) -> bool:
        if not url:
            return True
        with self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM visited_urls WHERE url = ?", (url,)
            ).fetchone()
            return row is not None
