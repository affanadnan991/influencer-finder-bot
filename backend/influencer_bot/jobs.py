"""Background job manager — runs discovery engine in a thread, tracks progress.

Supports WebSocket listeners for real-time progress updates.
"""

from __future__ import annotations

import asyncio
import json
import threading
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

from discovery_engine.engine import DiscoveryEngine
from storage import ProfileStore


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Job:
    """Represents a single search job."""

    def __init__(self, target: str, keywords: list[str], max_following: int = 200):
        self.id: str = uuid.uuid4().hex[:12]
        self.target = target
        self.keywords = keywords
        self.max_following = max_following
        self.status: JobStatus = JobStatus.QUEUED
        self.phase: str = ""
        self.detail: str = ""
        self.counters: dict[str, int] = {}
        self.results: list[dict[str, Any]] = []
        self.csv_path: str = ""
        self.error: str = ""
        self.created_at: str = datetime.now().isoformat()
        self.finished_at: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.id,
            "target": self.target,
            "keywords": self.keywords,
            "max_following": self.max_following,
            "status": self.status.value,
            "phase": self.phase,
            "detail": self.detail,
            "counters": self.counters,
            "result_count": len(self.results),
            "csv_path": self.csv_path,
            "error": self.error,
            "created_at": self.created_at,
            "finished_at": self.finished_at,
        }


# ── In-memory job store ──────────────────────────────────────────

_jobs: dict[str, Job] = {}
_lock = threading.Lock()

# ── WebSocket listener registry ──────────────────────────────────
# Maps job_id -> set of async callback functions
_ws_listeners: dict[str, set[Callable]] = {}
_ws_lock = threading.Lock()
# Reference to the asyncio event loop (set by main.py on startup)
_event_loop: Optional[asyncio.AbstractEventLoop] = None


def set_event_loop(loop: asyncio.AbstractEventLoop) -> None:
    """Called once at server startup to store the main event loop."""
    global _event_loop
    _event_loop = loop


def add_ws_listener(job_id: str, callback: Callable) -> None:
    with _ws_lock:
        _ws_listeners.setdefault(job_id, set()).add(callback)


def remove_ws_listener(job_id: str, callback: Callable) -> None:
    with _ws_lock:
        listeners = _ws_listeners.get(job_id)
        if listeners:
            listeners.discard(callback)
            if not listeners:
                del _ws_listeners[job_id]


def _notify_listeners(job: Job) -> None:
    """Send job state to all WebSocket listeners (thread-safe)."""
    with _ws_lock:
        listeners = _ws_listeners.get(job.id)
        if not listeners:
            return
        listeners_copy = list(listeners)

    if not _event_loop:
        return

    data = job.to_dict()
    for cb in listeners_copy:
        try:
            _event_loop.call_soon_threadsafe(
                asyncio.ensure_future,
                cb(data),
            )
        except Exception:
            pass


# ── Public API ───────────────────────────────────────────────────

def get_job(job_id: str) -> Optional[Job]:
    return _jobs.get(job_id)


def list_jobs() -> list[dict[str, Any]]:
    return [j.to_dict() for j in _jobs.values()]


def start_search(target: str, keywords: list[str], max_following: int = 200) -> Job:
    """Create a job and run it in a background thread."""
    job = Job(target=target, keywords=keywords, max_following=max_following)
    with _lock:
        _jobs[job.id] = job

    thread = threading.Thread(target=_run_job, args=(job,), daemon=True)
    thread.start()
    return job


def _run_job(job: Job) -> None:
    """Execute the discovery engine inside a thread."""
    job.status = JobStatus.RUNNING
    job.phase = "starting"
    _notify_listeners(job)

    def on_progress(phase: str, detail: str, counters: dict[str, int], csv_path: str = "") -> None:
        job.phase = phase
        job.detail = detail
        job.counters = counters
        if csv_path:
            job.csv_path = csv_path
        _notify_listeners(job)

    def on_match(profile: dict) -> None:
        # Pushed the moment a profile is matched and written to the CSV —
        # lets the frontend show results live instead of only at the end.
        job.results.append(profile)
        _notify_listeners(job)

    try:
        store = ProfileStore()
        engine = DiscoveryEngine(
            target=job.target,
            keywords=job.keywords,
            store=store,
            progress_callback=on_progress,
            on_match=on_match,
        )
        engine.discover(max_following=job.max_following)

        job.counters = engine.counters
        job.status = JobStatus.COMPLETED
        job.finished_at = datetime.now().isoformat()

    except Exception as exc:
        job.status = JobStatus.FAILED
        job.error = str(exc)
        job.finished_at = datetime.now().isoformat()

    _notify_listeners(job)
