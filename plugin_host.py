from __future__ import annotations

import importlib.util
import json
import os
import sys
import traceback

from plugin_api import PluginAPI
import plugin_platform


class HostedPluginAPI:
    def __init__(self, plugin_id, manifest, config=None):
        self.plugin_id = plugin_id
        self.manifest = manifest
        self._permissions = set(manifest.get("permissions", []))
        self._config = config if isinstance(config, dict) else {}
        self.events = []
        self.tabs = []
        self.periodic_tasks = []

    def _require_permission(self, permission):
        if permission not in self._permissions:
            raise PermissionError(f"Plugin manifest does not grant {permission} permission.")

    def network_state(self):
        self._require_permission("network_state")
        return None

    def emit_event(self, event_type, summary, details=None):
        self._require_permission("events")
        event = {
            "type": f"plugin.{self.plugin_id}.{event_type}",
            "summary": str(summary),
            "details": details or {},
        }
        self.events.append(event)
        return event

    def get_config(self, default=None):
        settings = self._config.setdefault("settings", {})
        return settings.setdefault(self.plugin_id, default if isinstance(default, dict) else {})

    def register_tab(self, title, builder):
        self._require_permission("ui")
        self.tabs.append({"title": str(title), "builder": getattr(builder, "__name__", str(builder))})

    def register_periodic_task(self, name, interval_seconds, callback):
        self._require_permission("scheduled_tasks")
        self.periodic_tasks.append(
            {
                "name": str(name),
                "interval_seconds": max(PluginAPI.min_periodic_interval_seconds, int(interval_seconds or 0)),
                "callback": getattr(callback, "__name__", str(callback)),
            }
        )


def load_plugin(manifest_path, config=None):
    manifest_path = os.path.abspath(manifest_path)
    manifest = _load_manifest(manifest_path)
    plugin_dir = os.path.dirname(manifest_path)
    entrypoint = os.path.abspath(os.path.join(plugin_dir, manifest["entrypoint"]))
    if os.path.commonpath([plugin_dir, entrypoint]) != plugin_dir:
        raise ValueError("Entrypoint must stay inside plugin directory")
    if not os.path.isfile(entrypoint):
        raise FileNotFoundError(entrypoint)
    spec = importlib.util.spec_from_file_location(f"lucid_hosted_plugin_{manifest['id']}", entrypoint)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load plugin entrypoint: {entrypoint}")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, plugin_dir)
    try:
        spec.loader.exec_module(module)
    finally:
        try:
            sys.path.remove(plugin_dir)
        except ValueError:
            pass
    api = HostedPluginAPI(manifest["id"], manifest, config=config)
    if hasattr(module, "on_start"):
        module.on_start(api)
    return module, api


def run_once(manifest_path, config=None):
    module, api = load_plugin(manifest_path, config=config)
    return {
        "ok": True,
        "id": api.plugin_id,
        "module": getattr(module, "__name__", ""),
        "events": api.events,
        "tabs": api.tabs,
        "periodic_tasks": api.periodic_tasks,
    }


def _load_manifest(path):
    with open(path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    required = ("id", "name", "version", "api_version", "entrypoint")
    missing = [key for key in required if not manifest.get(key)]
    if missing:
        raise ValueError(f"Missing manifest keys: {', '.join(missing)}")
    if str(manifest["api_version"]) != PluginAPI.api_version:
        raise ValueError(f"Unsupported plugin API version: {manifest['api_version']}")
    ok, permissions_or_error = plugin_platform.validate_permissions(manifest.get("permissions", []))
    if not ok:
        raise ValueError(permissions_or_error)
    manifest["permissions"] = permissions_or_error
    return manifest


def handle_request(request):
    command = request.get("command")
    if command == "health":
        return {"ok": True, "host": "plugin_host", "schema_version": 1}
    if command == "run-once":
        return run_once(request["manifest_path"], config=request.get("config"))
    raise ValueError(f"Unknown plugin host command: {command}")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        if argv and argv[0] == "--manifest":
            response = run_once(argv[1] if len(argv) > 1 else "")
            print(json.dumps(response, sort_keys=True, default=str))
            return 0
        for line in sys.stdin:
            if not line.strip():
                continue
            try:
                response = handle_request(json.loads(line))
            except Exception as exc:
                response = {"ok": False, "error": str(exc), "traceback": traceback.format_exc(limit=5)}
            print(json.dumps(response, sort_keys=True, default=str), flush=True)
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
