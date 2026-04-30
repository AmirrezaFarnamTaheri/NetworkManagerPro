import json
import os
import re
import sqlite3
import uuid
import zipfile
from datetime import datetime

import core
from history_store import EventStore


def diagnostics_summary(config=None, monitor_state=None):
    return {
        "app": core.APP_DISPLAY_NAME,
        "version": core.APP_VERSION,
        "admin": core.is_admin(),
        "paths": {
            "app_base": core.app_base_dir(),
            "config": core.config_path(),
            "logs": core.logs_dir(),
            "history": core.history_db_path(),
            "plugins": core.plugins_dir(),
        },
        "config": core.sanitize_config(config or core.load_config() or {}),
        "state": _state_dict(monitor_state),
    }


def copyable_diagnostics(config=None, monitor_state=None):
    return json.dumps(diagnostics_summary(config, monitor_state), indent=2, ensure_ascii=False, default=str)


def export_bundle(config=None, monitor_state=None):
    core.ensure_runtime_dirs()
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = os.path.join(core.app_data_dir(), f"diagnostics-{stamp}-{uuid.uuid4().hex[:6]}.zip")
    summary = json.dumps(diagnostics_summary(config, monitor_state), indent=2, ensure_ascii=False, default=str)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr("summary.json", summary)
        _write_text_if_exists(bundle, core.log_file_path(), "logs/app.log")
        _write_history_if_exists(bundle, core.history_db_path(), "history/events.jsonl")
    return path


def _write_text_if_exists(bundle, source, arcname):
    try:
        if os.path.exists(source):
            with open(source, "r", encoding="utf-8", errors="replace") as f:
                bundle.writestr(arcname, _redact_text(f.read()))
    except OSError as exc:
        bundle.writestr(f"errors/{arcname}.error.txt", str(exc))


def _write_history_if_exists(bundle, source, arcname):
    try:
        if not os.path.exists(source):
            return
        history = EventStore(source).export_jsonl()
        bundle.writestr(arcname, history + ("\n" if history else ""))
    except (OSError, sqlite3.Error) as exc:
        bundle.writestr(f"errors/{arcname}.error.txt", str(exc))


def _redact_text(text):
    text = str(text or "")
    text = re.sub(r"https?://\S+", lambda m: core.sanitize_url(m.group(0).rstrip(".,;"), redact_path=True), text)
    text = re.sub(r"([A-Za-z0-9_.-]+):([^@\s]+)@([A-Za-z0-9_.\[\]:-]+)", r"***@\3", text)
    return text


def _state_dict(state):
    if state is None:
        return {}
    if hasattr(state, "__dict__"):
        return core.redact_value(dict(state.__dict__))
    if isinstance(state, dict):
        return core.redact_value(state)
    return {}
