import json
import os
import sqlite3
import threading
import time
import uuid
from contextlib import closing
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
    def __init__(self, path=None):
        self.path = path or core.history_db_path()
        self._lock = threading.RLock()
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self._init_db()

    def append(self, event_type, summary, details=None, attribution="NetworkManagerPro"):
        event = Event(event_type, str(summary), core.redact_value(details or {}), str(attribution))
        record = asdict(event)
        details_json = json.dumps(record["details"], ensure_ascii=False, sort_keys=True, default=str)
        with self._lock, closing(self._connect()) as conn:
            with conn:
                conn.execute(
                    """
                    INSERT INTO events (id, timestamp, type, summary, details, attribution)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record["id"],
                        record["timestamp"],
                        record["type"],
                        record["summary"],
                        details_json,
                        record["attribution"],
                    ),
                )
        core.logger().info("event type=%s summary=%s", event_type, summary)
        return record

    def recent(self, limit=100, event_type=None):
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = 100
        if limit <= 0:
            return []
        with self._lock, closing(self._connect()) as conn:
            if event_type:
                rows = conn.execute(
                    """
                    SELECT id, timestamp, type, summary, details, attribution
                    FROM events
                    WHERE type = ?
                    ORDER BY timestamp DESC, rowid DESC
                    LIMIT ?
                    """,
                    (str(event_type), limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, timestamp, type, summary, details, attribution
                    FROM events
                    ORDER BY timestamp DESC, rowid DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
        return list(reversed([self._row_to_event(row) for row in rows]))

    def clear(self):
        with self._lock, closing(self._connect()) as conn:
            with conn:
                conn.execute("DELETE FROM events")
        return self.append("history.cleared", "History cleared")

    def export_jsonl(self):
        rows = self.recent(100000)
        return "\n".join(json.dumps(core.redact_value(row), ensure_ascii=False, sort_keys=True, default=str) for row in rows)

    def _connect(self):
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self):
        with self._lock, closing(self._connect()) as conn:
            with conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS events (
                        id TEXT PRIMARY KEY,
                        timestamp REAL NOT NULL,
                        type TEXT NOT NULL,
                        summary TEXT NOT NULL,
                        details TEXT NOT NULL DEFAULT '{}',
                        attribution TEXT NOT NULL
                    )
                    """
                )
                conn.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_events_type_timestamp ON events(type, timestamp)")

    def _row_to_event(self, row):
        try:
            details = json.loads(row["details"] or "{}")
        except json.JSONDecodeError:
            details = {}
        return {
            "id": row["id"],
            "timestamp": row["timestamp"],
            "type": row["type"],
            "summary": row["summary"],
            "details": core.redact_value(details),
            "attribution": row["attribution"],
        }
