from __future__ import annotations

from dataclasses import dataclass

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


def format_bytes(value):
    try:
        amount = float(value)
    except (TypeError, ValueError):
        amount = 0.0
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if amount < 1024 or unit == "TB":
            return f"{amount:.0f} {unit}" if unit == "B" else f"{amount:.1f} {unit}"
        amount /= 1024
