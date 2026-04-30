from __future__ import annotations

from dataclasses import dataclass
import os
import sqlite3
import time

import psutil


@dataclass
class ProcessTrafficSnapshot:
    pid: int
    name: str
    connections: int
    established: int
    remotes: list[str]


def collect_connections(limit=80):
    """Best-effort per-process connection inventory for the Traffic panel."""
    by_pid = {}
    try:
        connections = psutil.net_connections(kind="inet")
    except (psutil.AccessDenied, OSError):
        connections = []

    for conn in connections:
        pid = conn.pid
        if not pid:
            continue
        item = by_pid.setdefault(pid, {"connections": 0, "established": 0, "remotes": set()})
        item["connections"] += 1
        if conn.status == psutil.CONN_ESTABLISHED:
            item["established"] += 1
        if conn.raddr:
            item["remotes"].add(f"{conn.raddr.ip}:{conn.raddr.port}")

    snapshots = []
    for pid, item in by_pid.items():
        try:
            name = psutil.Process(pid).name()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            name = "Unknown"
        snapshots.append(
            ProcessTrafficSnapshot(
                pid=pid,
                name=name,
                connections=item["connections"],
                established=item["established"],
                remotes=sorted(item["remotes"])[:3],
            )
        )

    snapshots.sort(key=lambda p: (p.established, p.connections), reverse=True)
    return snapshots[:limit]


def system_totals():
    try:
        counters = psutil.net_io_counters()
    except OSError:
        return {"bytes_sent": 0, "bytes_recv": 0, "packets_sent": 0, "packets_recv": 0}
    return {
        "bytes_sent": counters.bytes_sent,
        "bytes_recv": counters.bytes_recv,
        "packets_sent": counters.packets_sent,
        "packets_recv": counters.packets_recv,
    }


def init_metrics_db(db_path):
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS traffic_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                bytes_sent INTEGER NOT NULL,
                bytes_recv INTEGER NOT NULL,
                packets_sent INTEGER NOT NULL,
                packets_recv INTEGER NOT NULL,
                latency_ms REAL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_traffic_metrics_timestamp ON traffic_metrics(timestamp)")


def append_metrics(db_path, totals=None, latency_ms=None, timestamp=None):
    init_metrics_db(db_path)
    totals = totals or system_totals()
    stamp = float(timestamp if timestamp is not None else time.time())
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO traffic_metrics (
                timestamp, bytes_sent, bytes_recv, packets_sent, packets_recv, latency_ms
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                stamp,
                int(totals.get("bytes_sent", 0)),
                int(totals.get("bytes_recv", 0)),
                int(totals.get("packets_sent", 0)),
                int(totals.get("packets_recv", 0)),
                latency_ms,
            ),
        )
    return stamp


def recent_metrics(db_path, limit=120):
    init_metrics_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT timestamp, bytes_sent, bytes_recv, packets_sent, packets_recv, latency_ms
            FROM traffic_metrics
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (max(1, int(limit)),),
        ).fetchall()
    return [dict(row) for row in rows]


def summarize_metric_deltas(rows):
    ordered = sorted(rows, key=lambda row: row.get("timestamp", 0))
    if len(ordered) < 2:
        return {"samples": len(ordered), "bytes_sent_delta": 0, "bytes_recv_delta": 0, "duration_seconds": 0}
    first = ordered[0]
    last = ordered[-1]
    return {
        "samples": len(ordered),
        "bytes_sent_delta": max(0, int(last.get("bytes_sent", 0)) - int(first.get("bytes_sent", 0))),
        "bytes_recv_delta": max(0, int(last.get("bytes_recv", 0)) - int(first.get("bytes_recv", 0))),
        "duration_seconds": max(0, float(last.get("timestamp", 0)) - float(first.get("timestamp", 0))),
    }


def format_bytes(value):
    try:
        amount = float(value)
    except (TypeError, ValueError):
        amount = 0.0
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if amount < 1024 or unit == "TB":
            return f"{amount:.0f} {unit}" if unit == "B" else f"{amount:.1f} {unit}"
        amount /= 1024
