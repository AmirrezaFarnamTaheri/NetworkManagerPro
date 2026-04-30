from __future__ import annotations

import uuid


SCHEMA_VERSION = 1

COMMANDS = {
    "status": {"privileged": False, "required": []},
    "dns.set": {"privileged": True, "required": ["interface", "servers"]},
    "dns.clear": {"privileged": True, "required": ["interface"]},
    "hosts.apply_group": {"privileged": True, "required": ["group", "entries", "enabled"]},
    "firewall.apply_rule": {"privileged": True, "required": ["rule"]},
}


def make_request(command, args=None, request_id=None):
    return {
        "schema_version": SCHEMA_VERSION,
        "request_id": request_id or uuid.uuid4().hex,
        "command": str(command or ""),
        "args": args or {},
    }


def make_response(request, ok, message, detail="", event=None):
    return {
        "schema_version": SCHEMA_VERSION,
        "request_id": str((request or {}).get("request_id") or ""),
        "ok": bool(ok),
        "message": str(message or ""),
        "detail": str(detail or ""),
        "event": event or {},
    }


def validate_request(request):
    if not isinstance(request, dict):
        return False, "Request must be an object."
    if request.get("schema_version") != SCHEMA_VERSION:
        return False, "Unsupported broker schema version."
    request_id = str(request.get("request_id") or "")
    if not request_id or len(request_id) > 80:
        return False, "Request ID is required and must be short."
    command = str(request.get("command") or "")
    if command not in COMMANDS:
        return False, "Unsupported broker command."
    args = request.get("args")
    if not isinstance(args, dict):
        return False, "Request args must be an object."
    for key in COMMANDS[command]["required"]:
        if key not in args:
            return False, f"Missing required argument: {key}"
    return True, ""


def privileged_commands():
    return sorted(command for command, meta in COMMANDS.items() if meta.get("privileged"))
