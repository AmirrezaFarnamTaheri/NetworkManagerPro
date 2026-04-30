from __future__ import annotations

import hashlib
import json
import os
import sys

import core


ALLOWED_PERMISSIONS = {
    "network_state",
    "events",
    "ui",
    "scheduled_tasks",
}

CAPABILITY_DESCRIPTIONS = {
    "network_state": "Read the current monitor snapshot.",
    "events": "Append plugin-scoped events to local history.",
    "ui": "Register plugin UI tabs.",
    "scheduled_tasks": "Run cooperative periodic background tasks.",
}


def validate_permissions(permissions):
    if not isinstance(permissions, list) or not all(isinstance(item, str) for item in permissions):
        return False, "Plugin permissions must be a list of strings."
    unknown = sorted(set(permissions) - ALLOWED_PERMISSIONS)
    if unknown:
        return False, f"Unknown plugin permissions: {', '.join(unknown)}"
    return True, sorted(set(permissions))


def capability_summary(permissions):
    ok, normalized_or_error = validate_permissions(permissions)
    if not ok:
        return []
    return [
        {"permission": permission, "description": CAPABILITY_DESCRIPTIONS[permission]}
        for permission in normalized_or_error
    ]


def plugin_venv_path(plugin_id):
    safe_id = str(plugin_id or "").replace("/", "_").replace("\\", "_")
    return os.path.join(core.app_data_dir(), "plugin_envs", safe_id)


def isolation_plan(manifest):
    plugin_id = str((manifest or {}).get("id") or "")
    return {
        "mode": str((manifest or {}).get("isolation", "subprocess")),
        "plugin_id": plugin_id,
        "host_command": [sys.executable, "-m", "plugin_host", plugin_id],
        "timeout_seconds": int((manifest or {}).get("timeout_seconds", 10) or 10),
        "venv_path": plugin_venv_path(plugin_id),
        "permissions": capability_summary((manifest or {}).get("permissions", [])),
    }


def manifest_fingerprint(manifest_path):
    root = os.path.dirname(os.path.abspath(manifest_path))
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    entrypoint = os.path.abspath(os.path.join(root, manifest.get("entrypoint", "")))
    paths = [manifest_path]
    if os.path.isfile(entrypoint):
        paths.append(entrypoint)
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(os.path.basename(path).encode("utf-8"))
        with open(path, "rb") as f:
            digest.update(f.read())
    return digest.hexdigest()


def bundle_manifest(plugin_dir):
    plugin_dir = os.path.abspath(plugin_dir)
    files = []
    for root, _dirs, names in os.walk(plugin_dir):
        for name in sorted(names):
            path = os.path.join(root, name)
            rel = os.path.relpath(path, plugin_dir).replace("\\", "/")
            files.append({"path": rel, "sha256": _sha256_file(path), "size": os.path.getsize(path)})
    return {"schema_version": 1, "files": files}


def verify_bundle_manifest(plugin_dir, bundle):
    plugin_dir = os.path.abspath(plugin_dir)
    failures = []
    for item in (bundle or {}).get("files", []):
        rel = str(item.get("path") or "")
        path = os.path.abspath(os.path.join(plugin_dir, rel))
        if os.path.commonpath([plugin_dir, path]) != plugin_dir:
            failures.append(f"Path escapes plugin directory: {rel}")
            continue
        if not os.path.exists(path):
            failures.append(f"Missing file: {rel}")
            continue
        actual = _sha256_file(path)
        if actual != str(item.get("sha256") or "").lower():
            failures.append(f"Digest mismatch: {rel}")
    return len(failures) == 0, failures


def parse_marketplace_registry(registry):
    registry = registry if isinstance(registry, dict) else {}
    plugins = []
    for raw in registry.get("plugins", []):
        if not isinstance(raw, dict):
            continue
        plugin = {
            "id": str(raw.get("id") or "").strip(),
            "name": str(raw.get("name") or "").strip(),
            "version": str(raw.get("version") or "").strip(),
            "publisher": str(raw.get("publisher") or "").strip(),
            "bundle_url": str(raw.get("bundle_url") or "").strip(),
            "sha256": str(raw.get("sha256") or "").strip().lower(),
            "permissions": raw.get("permissions") or [],
            "signature": raw.get("signature") or {},
        }
        ok, normalized_or_error = validate_permissions(plugin["permissions"])
        if plugin["id"] and plugin["name"] and ok:
            plugin["permissions"] = normalized_or_error
            plugins.append(plugin)
    return {"schema_version": int(registry.get("schema_version", 1) or 1), "plugins": plugins}


def _sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
