from __future__ import annotations

import os
import shutil
import time
from dataclasses import dataclass


MANAGED_BEGIN = "# NetworkManagerPro BEGIN"
MANAGED_END = "# NetworkManagerPro END"


@dataclass
class HostsEntry:
    address: str
    hostname: str
    comment: str = ""


def parse_entries(text):
    entries = []
    for line in str(text or "").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        body, _, comment = stripped.partition("#")
        parts = body.split()
        if len(parts) >= 2:
            entries.append(HostsEntry(parts[0], parts[1], comment.strip()))
    return entries


def render_group(name, entries):
    safe_name = str(name or "managed").strip() or "managed"
    lines = [f"{MANAGED_BEGIN} {safe_name}"]
    for entry in entries:
        suffix = f" # {entry.comment}" if entry.comment else ""
        lines.append(f"{entry.address} {entry.hostname}{suffix}")
    lines.append(f"{MANAGED_END} {safe_name}")
    return "\n".join(lines) + "\n"


def preview_apply(current_text, group_name, entries, enabled=True):
    unmanaged = remove_managed_group(current_text, group_name)
    if not enabled:
        return unmanaged.rstrip() + "\n"
    managed = render_group(group_name, entries)
    return unmanaged.rstrip() + "\n\n" + managed


def remove_managed_group(text, group_name):
    safe_name = str(group_name or "managed").strip() or "managed"
    begin = f"{MANAGED_BEGIN} {safe_name}"
    end = f"{MANAGED_END} {safe_name}"
    output = []
    skipping = False
    for line in str(text or "").splitlines():
        if line.strip() == begin:
            skipping = True
            continue
        if skipping and line.strip() == end:
            skipping = False
            continue
        if not skipping:
            output.append(line)
    return "\n".join(output).rstrip() + "\n"


def backup_hosts_file(hosts_path, backup_dir=None):
    hosts_path = os.path.abspath(hosts_path)
    backup_dir = backup_dir or os.path.dirname(hosts_path)
    os.makedirs(backup_dir, exist_ok=True)
    backup_path = os.path.join(backup_dir, f"hosts.{int(time.time())}.bak")
    shutil.copy2(hosts_path, backup_path)
    return backup_path


def apply_group(hosts_path, group_name, entries, enabled=True, backup_dir=None):
    hosts_path = os.path.abspath(hosts_path)
    with open(hosts_path, "r", encoding="utf-8", errors="replace") as f:
        current = f.read()
    backup_path = backup_hosts_file(hosts_path, backup_dir=backup_dir)
    updated = preview_apply(current, group_name, entries, enabled=enabled)
    tmp_path = hosts_path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(updated)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, hosts_path)
    return backup_path
