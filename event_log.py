from __future__ import annotations

import json
import subprocess

import core


SOURCE = "NetworkManagerPro"
LOG_NAME = "Application"


def event_payload(event_type, summary, details=None):
    return {
        "app": core.APP_NAME,
        "type": str(event_type or "app.event"),
        "summary": str(summary or ""),
        "details": core.redact_value(details or {}),
    }


def format_event_message(event_type, summary, details=None):
    return json.dumps(event_payload(event_type, summary, details), sort_keys=True, default=str)


def register_event_source_command(source=SOURCE):
    safe_source = str(source or SOURCE).replace("'", "''")
    return (
        "if (-not [System.Diagnostics.EventLog]::SourceExists('{0}')) "
        "{{ New-EventLog -LogName Application -Source '{0}' }}"
    ).format(safe_source)


def write_event(event_type, summary, details=None, event_id=2000, source=SOURCE):
    message = format_event_message(event_type, summary, details)
    safe_source = str(source or SOURCE).replace("'", "''")
    script = (
        f"Write-EventLog -LogName {LOG_NAME} -Source '{safe_source}' "
        f"-EventId {int(event_id)} -EntryType Information -Message @'\n{message}\n'@"
    )
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    if result.returncode != 0:
        return False, (result.stderr or result.stdout or "").strip()
    return True, "Event written."
