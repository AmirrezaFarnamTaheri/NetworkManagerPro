from __future__ import annotations

import hashlib
import json
import os
import subprocess


MANIFEST_SCHEMA_VERSION = 1


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_release_manifest(paths, version):
    artifacts = []
    for path in paths:
        full_path = os.path.abspath(path)
        artifacts.append(
            {
                "name": os.path.basename(full_path),
                "path": full_path,
                "sha256": sha256_file(full_path),
                "size": os.path.getsize(full_path),
            }
        )
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "version": str(version),
        "artifacts": artifacts,
    }


def write_release_manifest(paths, version, manifest_path):
    manifest = build_release_manifest(paths, version)
    os.makedirs(os.path.dirname(os.path.abspath(manifest_path)), exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
    return manifest


def verify_manifest(manifest_path):
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    failures = []
    for artifact in manifest.get("artifacts", []):
        path = artifact.get("path")
        expected = str(artifact.get("sha256") or "").lower()
        if not path or not os.path.exists(path):
            failures.append(f"Missing artifact: {path}")
            continue
        actual = sha256_file(path)
        if actual.lower() != expected:
            failures.append(f"SHA256 mismatch for {path}: expected {expected}, got {actual}")
    return len(failures) == 0, failures


def verify_authenticode_signature(path, signtool="signtool"):
    try:
        result = subprocess.run(
            [signtool, "verify", "/pa", "/all", os.path.abspath(path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    output = (result.stdout or "") + (result.stderr or "")
    return result.returncode == 0, output.strip()
