import json
import os
import re
import sqlite3
import uuid
import zipfile
from datetime import UTC, datetime

import core
import deep_diagnostics
from history_store import EventStore

DIAGNOSTICS_SCHEMA_VERSION = 2


def diagnostics_summary(config=None, monitor_state=None):
    cfg = config or core.load_config() or {}
    return {
        "schema_version": DIAGNOSTICS_SCHEMA_VERSION,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "app": core.APP_DISPLAY_NAME,
        "version": core.APP_VERSION,
        "admin": core.is_admin(),
        "environment": {
            "python": os.sys.version.split()[0],
            "platform": os.sys.platform,
            "pid": os.getpid(),
        },
        "paths": {
            "app_base": core.app_base_dir(),
            "config": core.config_path(),
            "logs": core.logs_dir(),
            "history": core.history_db_path(),
            "traffic_metrics": core.traffic_metrics_db_path(),
            "plugins": core.plugins_dir(),
        },
        "config_schema_version": (cfg or {}).get("config_version"),
        "enabled_plugin_ids": _enabled_plugin_ids(cfg),
        "config": core.sanitize_config(cfg),
        "state": _state_dict(monitor_state),
        "deep_diagnostics": {
            "schema_version": deep_diagnostics.SCHEMA_VERSION,
            "available_tests": sorted(deep_diagnostics.TEST_CATALOG.keys()),
        },
    }


def copyable_diagnostics(config=None, monitor_state=None):
    return json.dumps(diagnostics_summary(config, monitor_state), indent=2, ensure_ascii=False, default=str)


def export_bundle(config=None, monitor_state=None):
    core.ensure_runtime_dirs()
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = os.path.join(core.app_data_dir(), f"diagnostics-{stamp}-{uuid.uuid4().hex[:6]}.zip")
    summary = json.dumps(diagnostics_summary(config, monitor_state), indent=2, ensure_ascii=False, default=str)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr("manifest.json", _manifest(config, monitor_state))
        bundle.writestr("summary.json", summary)
        _write_text_if_exists(bundle, core.log_file_path(), "logs/app.log")
        _write_history_if_exists(bundle, core.history_db_path(), "history/events.jsonl")
        _write_traffic_metrics_if_exists(bundle, core.traffic_metrics_db_path(), "history/traffic_metrics.jsonl")
    return path


def _manifest(config=None, monitor_state=None):
    summary = diagnostics_summary(config, monitor_state)
    manifest = {
        "schema_version": DIAGNOSTICS_SCHEMA_VERSION,
        "generated_at": summary["generated_at"],
        "app": summary["app"],
        "version": summary["version"],
        "files": [
            {"path": "summary.json", "description": "Sanitized runtime, config, environment, and monitor summary."},
            {"path": "logs/app.log", "description": "Redacted application log if present."},
            {"path": "history/events.jsonl", "description": "Redacted recent event history exported from SQLite."},
            {"path": "history/traffic_metrics.jsonl", "description": "Aggregate traffic metrics if present."},
        ],
    }
    return json.dumps(manifest, indent=2, ensure_ascii=False)


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


def _write_traffic_metrics_if_exists(bundle, source, arcname):
    try:
        if not os.path.exists(source):
            return
        with sqlite3.connect(source) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT timestamp, bytes_sent, bytes_recv, packets_sent, packets_recv, latency_ms
                FROM traffic_metrics
                ORDER BY timestamp DESC
                LIMIT 240
                """
            ).fetchall()
        text = "\n".join(json.dumps(dict(row), sort_keys=True, default=str) for row in rows)
        bundle.writestr(arcname, text + ("\n" if text else ""))
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


def _enabled_plugin_ids(config):
    plugins = config.get("plugins") if isinstance(config, dict) else {}
    enabled = plugins.get("enabled") if isinstance(plugins, dict) else []
    return [str(item) for item in enabled] if isinstance(enabled, list) else []
