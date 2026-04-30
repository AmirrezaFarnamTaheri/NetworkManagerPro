from __future__ import annotations

import shutil
import subprocess


TOOLS = {
    "tailscale": {"commands": [["tailscale", "status", "--json"], ["tailscale", "status"]]},
    "zerotier": {"commands": [["zerotier-cli", "info"], ["zerotier-cli", "listnetworks"]]},
}


def detect_overlay_tools(which=None):
    which = which or shutil.which
    found = {}
    for name in TOOLS:
        path = which(name) or which(f"{name}.exe")
        found[name] = {"installed": bool(path), "path": path or ""}
    return found


def read_only_status_command(tool):
    meta = TOOLS.get(str(tool or "").lower())
    if not meta:
        return None
    return list(meta["commands"][0])


def overlay_operation_gate(operation, consent=False, vendor_reviewed=False):
    blockers = []
    if operation != "read_status" and not consent:
        blockers.append("explicit user consent")
    if operation not in ("read_status",) and not vendor_reviewed:
        blockers.append("vendor CLI/API stability review")
    return {
        "operation": str(operation or ""),
        "read_only": operation == "read_status",
        "allowed": not blockers,
        "blockers": blockers,
    }


def run_read_only_status(tool, runner=None):
    command = read_only_status_command(tool)
    if not command:
        return {"ok": False, "tool": str(tool or ""), "output": "", "error": "Unsupported overlay tool."}
    runner = runner or subprocess.run
    try:
        result = runner(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "tool": tool, "output": "", "error": str(exc)}
    return {
        "ok": result.returncode == 0,
        "tool": tool,
        "output": (result.stdout or "").strip()[:4000],
        "error": (result.stderr or "").strip()[:1000],
    }
