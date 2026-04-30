from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import venv
import zipfile

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


def plugin_python_path(plugin_id):
    base = plugin_venv_path(plugin_id)
    if os.name == "nt":
        return os.path.join(base, "Scripts", "python.exe")
    return os.path.join(base, "bin", "python")


def dependency_metadata(manifest):
    manifest = manifest if isinstance(manifest, dict) else {}
    dependencies = manifest.get("dependencies") or []
    requirements = str(manifest.get("requirements") or "").strip()
    if not isinstance(dependencies, list):
        dependencies = []
    normalized = sorted({str(item).strip() for item in dependencies if str(item).strip()})
    digest = hashlib.sha256()
    for item in normalized:
        digest.update(item.encode("utf-8"))
        digest.update(b"\0")
    digest.update(requirements.encode("utf-8"))
    return {
        "dependencies": normalized,
        "requirements": requirements,
        "lock_hash": digest.hexdigest(),
    }


def environment_spec(manifest):
    plugin_id = str((manifest or {}).get("id") or "")
    meta = dependency_metadata(manifest)
    venv_path = plugin_venv_path(plugin_id)
    return {
        "schema_version": 1,
        "plugin_id": plugin_id,
        "venv_path": venv_path,
        "python": plugin_python_path(plugin_id),
        "lock_path": os.path.join(venv_path, "environment-lock.json"),
        "dependencies": meta["dependencies"],
        "requirements": meta["requirements"],
        "lock_hash": meta["lock_hash"],
        "created": os.path.exists(plugin_python_path(plugin_id)),
    }


def write_environment_lock(manifest, created_by=None):
    spec = environment_spec(manifest)
    os.makedirs(spec["venv_path"], exist_ok=True)
    payload = {
        **spec,
        "created_by": created_by or core.APP_DISPLAY_NAME,
        "updated_at": int(time.time()),
    }
    with open(spec["lock_path"], "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
    return payload


def create_plugin_environment(manifest, dry_run=False, install_dependencies=False):
    spec = environment_spec(manifest)
    actions = [
        {"action": "create_venv", "path": spec["venv_path"]},
        {"action": "write_lock", "path": spec["lock_path"]},
    ]
    if spec["dependencies"] or spec["requirements"]:
        actions.append(
            {
                "action": "install_dependencies",
                "dependencies": spec["dependencies"],
                "requirements": spec["requirements"],
            }
        )
    if dry_run:
        return {"ok": True, "dry_run": True, "spec": spec, "actions": actions}
    venv.EnvBuilder(with_pip=True, clear=False).create(spec["venv_path"])
    lock = write_environment_lock(manifest)
    failures = []
    if install_dependencies and (spec["dependencies"] or spec["requirements"]):
        cmd = [spec["python"], "-m", "pip", "install", "--disable-pip-version-check"]
        if spec["requirements"]:
            cmd += ["-r", os.path.join(os.path.dirname(lock["lock_path"]), spec["requirements"])]
        cmd += spec["dependencies"]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
        if result.returncode != 0:
            failures.append((result.stderr or result.stdout or "").strip())
    if failures:
        return {"ok": False, "dry_run": False, "spec": spec, "actions": actions, "lock": lock, "failures": failures}
    return {"ok": True, "dry_run": False, "spec": spec, "actions": actions, "lock": lock}


def isolation_plan(manifest):
    plugin_id = str((manifest or {}).get("id") or "")
    env = environment_spec(manifest or {})
    return {
        "mode": str((manifest or {}).get("isolation", "subprocess")),
        "plugin_id": plugin_id,
        "host_command": [env["python"] if env["created"] else sys.executable, "-m", "plugin_host", plugin_id],
        "timeout_seconds": int((manifest or {}).get("timeout_seconds", 10) or 10),
        "venv_path": env["venv_path"],
        "environment": env,
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


def signed_bundle_metadata(plugin_dir, publisher, key_id, signature=""):
    bundle = bundle_manifest(plugin_dir)
    digest = hashlib.sha256(json.dumps(bundle, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return {
        "schema_version": 1,
        "publisher": str(publisher or "").strip(),
        "key_id": str(key_id or "").strip(),
        "algorithm": "digest-only-research",
        "bundle_sha256": digest,
        "signature": str(signature or "").strip(),
    }


def verify_signed_bundle(plugin_dir, bundle, signature, trusted_publishers=None):
    ok, failures = verify_bundle_manifest(plugin_dir, bundle)
    signature = signature if isinstance(signature, dict) else {}
    trusted = {str(item) for item in (trusted_publishers or [])}
    publisher = str(signature.get("publisher") or "").strip()
    expected_digest = str(signature.get("bundle_sha256") or "").lower()
    actual_digest = hashlib.sha256(json.dumps(bundle or {}, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    if expected_digest != actual_digest:
        failures.append("Signed bundle digest does not match bundle manifest.")
    if not publisher:
        failures.append("Signed bundle publisher is missing.")
    if trusted and publisher not in trusted:
        failures.append(f"Publisher is not trusted: {publisher}")
    if str(signature.get("algorithm") or "") == "digest-only-research":
        failures.append("Publisher signature is research-only and not a production identity proof.")
    return ok and not failures, failures


def install_plugin_bundle(bundle_zip, install_root, trusted_publishers=None):
    bundle_zip = os.path.abspath(bundle_zip)
    install_root = os.path.abspath(install_root)
    staging = os.path.join(install_root, ".staging")
    if os.path.exists(staging):
        shutil.rmtree(staging)
    os.makedirs(staging, exist_ok=True)
    with zipfile.ZipFile(bundle_zip) as archive:
        archive.extractall(staging)
    manifest_path = os.path.join(staging, "plugin.json")
    bundle_path = os.path.join(staging, "bundle-manifest.json")
    signature_path = os.path.join(staging, "signature.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    with open(bundle_path, "r", encoding="utf-8") as f:
        bundle = json.load(f)
    with open(signature_path, "r", encoding="utf-8") as f:
        signature = json.load(f)
    ok, failures = verify_signed_bundle(staging, bundle, signature, trusted_publishers)
    if not ok:
        shutil.rmtree(staging, ignore_errors=True)
        return {"ok": False, "failures": failures}
    plugin_id = str(manifest.get("id") or "").strip()
    if not plugin_id:
        shutil.rmtree(staging, ignore_errors=True)
        return {"ok": False, "failures": ["Plugin id is missing."]}
    target = os.path.abspath(os.path.join(install_root, plugin_id))
    if os.path.commonpath([install_root, target]) != install_root:
        shutil.rmtree(staging, ignore_errors=True)
        return {"ok": False, "failures": ["Plugin id escapes install root."]}
    if os.path.exists(target):
        shutil.rmtree(target)
    os.replace(staging, target)
    return {"ok": True, "plugin_id": plugin_id, "path": target, "failures": []}


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


def marketplace_install_plan(registry, installed_versions=None):
    installed_versions = installed_versions if isinstance(installed_versions, dict) else {}
    parsed = parse_marketplace_registry(registry)
    rows = []
    for plugin in parsed["plugins"]:
        current = str(installed_versions.get(plugin["id"]) or "")
        action = "install"
        if current and current == plugin["version"]:
            action = "installed"
        elif current:
            action = "update"
        signature = plugin.get("signature") if isinstance(plugin.get("signature"), dict) else {}
        signature_state = "present" if signature.get("publisher") and signature.get("bundle_sha256") else "missing"
        risk = "high" if signature_state == "missing" else "review"
        rows.append(
            {
                **plugin,
                "installed_version": current,
                "action": action,
                "signature_state": signature_state,
                "risk": risk,
            }
        )
    return {"schema_version": parsed["schema_version"], "plugins": rows}


def marketplace_operation(registry, plugin_id, action, installed_versions=None):
    plan = marketplace_install_plan(registry, installed_versions)
    plugin = next((item for item in plan["plugins"] if item["id"] == plugin_id), None)
    if not plugin:
        return {"ok": False, "action": action, "error": "Plugin is not present in the marketplace registry."}
    if action not in ("install", "update", "remove", "inspect"):
        return {"ok": False, "action": action, "error": "Unsupported marketplace action."}
    if action in ("install", "update") and plugin.get("signature_state") != "present":
        return {"ok": False, "action": action, "plugin": plugin, "error": "Signed bundle metadata is required before install or update."}
    return {"ok": True, "action": action, "plugin": plugin}


def _sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
