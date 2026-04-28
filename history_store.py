import json
import os
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field

import core


@dataclass
class Event:
    type: str
    summary: str
    details: dict = field(default_factory=dict)
    attribution: str = "NetworkManagerPro"
    timestamp: float = field(default_factory=time.time)
    id: str = field(default_factory=lambda: uuid.uuid4().hex)


class EventStore:
    def __init__(self, path=None, max_bytes=5_000_000):
        self.path = path or core.history_events_path()
        self.max_bytes = max_bytes
        self._lock = threading.RLock()
        os.makedirs(os.path.dirname(self.path), exist_ok=True)

    def append(self, event_type, summary, details=None, attribution="NetworkManagerPro"):
        event = Event(event_type, summary, core.redact_value(details or {}), attribution)
        record = asdict(event)
        with self._lock:
            self._rotate_if_needed()
            with open(self.path, "a", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(record, ensure_ascii=False, sort_keys=True, default=str) + "\n")
                f.flush()
                os.fsync(f.fileno())
        core.logger().info("event type=%s summary=%s", event_type, summary)
        return record

    def recent(self, limit=100, event_type=None):
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = 100
        if limit <= 0:
            return []
        if not os.path.exists(self.path):
            return []
        with self._lock:
            with open(self.path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        events = []
        for line in reversed(lines):
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event_type and item.get("type") != event_type:
                continue
            events.append(item)
            if len(events) >= limit:
                break
        return list(reversed(events))

    def clear(self):
        with self._lock:
            open(self.path, "w", encoding="utf-8").close()
        self.append("history.cleared", "History cleared")

    def _rotate_if_needed(self):
        if os.path.exists(self.path) and os.path.getsize(self.path) > self.max_bytes:
            backup = self.path + ".1"
            try:
                if os.path.exists(backup):
                    os.remove(backup)
                os.replace(self.path, backup)
            except OSError:
                core.logger().warning("history_rotate_failed path=%s", self.path, exc_info=True)
