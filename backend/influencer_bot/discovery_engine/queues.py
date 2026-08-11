"""Persistent queue helpers for breadth-first discovery campaigns."""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Optional


class DiscoveryQueueState:
    """Manage pending, matched, and processed queues for discovery runs."""

    def __init__(self, state_file: Optional[str] = None):
        self.state_file = state_file or os.path.join(os.getcwd(), "output", "discovery_state.json")
        os.makedirs(os.path.dirname(self.state_file) or ".", exist_ok=True)
        self._state = self._load()

    def _load(self) -> dict:
        if not os.path.exists(self.state_file):
            return {
                "pending": [],
                "matched": [],
                "processed": [],
                "last_updated": None,
            }
        try:
            with open(self.state_file, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except Exception:
            return {
                "pending": [],
                "matched": [],
                "processed": [],
                "last_updated": None,
            }

    def save(self) -> None:
        self._state["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.state_file, "w", encoding="utf-8") as handle:
            json.dump(self._state, handle, indent=2, ensure_ascii=False)

    def enqueue_pending(self, values: list[str]) -> None:
        pending = self._state.setdefault("pending", [])
        for value in values:
            if value and value not in pending:
                pending.append(value)
        self.save()

    def mark_matched(self, value: str) -> None:
        matched = self._state.setdefault("matched", [])
        if value and value not in matched:
            matched.append(value)
        self.save()

    def mark_processed(self, value: str) -> None:
        processed = self._state.setdefault("processed", [])
        if value and value not in processed:
            processed.append(value)
        self.save()

    def next_pending(self) -> Optional[str]:
        pending = self._state.setdefault("pending", [])
        if not pending:
            return None
        value = pending.pop(0)
        self.save()
        return value

    def has_pending(self) -> bool:
        return bool(self._state.setdefault("pending", []))

    def is_processed(self, value: str) -> bool:
        processed = self._state.setdefault("processed", [])
        return value in processed

    def snapshot(self) -> dict:
        return {
            "pending": list(self._state.setdefault("pending", [])),
            "matched": list(self._state.setdefault("matched", [])),
            "processed": list(self._state.setdefault("processed", [])),
            "last_updated": self._state.get("last_updated"),
        }
