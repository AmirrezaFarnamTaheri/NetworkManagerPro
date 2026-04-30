from __future__ import annotations

import json
import os
import subprocess
import time

import core
import psutil
import psutil


SCHEMA_VERSION = 1


def pcap_capture_plan(duration_seconds=30, output_dir=None, interface=""):
    duration = max(5, min(300, int(duration_seconds)))
    output_dir = output_dir or os.path.join(core.app_data_dir(), "forensics")
    return {
        "schema_version": SCHEMA_VERSION,
        "type": "pcap_capture_plan",
        "duration_seconds": duration,
        "output_dir": output_dir,
        "interface": str(interface or ""),
        "requires_explicit_start": True,
        "warning": (
            "Packet captures can contain sensitive content, metadata, hostnames, IP addresses, and credentials. "
            "Only capture traffic you are authorized to inspect."
        ),
        "allowed_outputs": ["pcapng", "json_summary"],
    }


def sidecar_request(command, args=None, timeout_seconds=15):
    return {
        "schema_version": SCHEMA_VERSION,
        "request_id": f"sidecar-{int(time.time() * 1000)}",
        "command": str(command or ""),
        "args": args or {},
        "timeout_seconds": max(1, min(300, int(timeout_seconds))),
    }


def validate_sidecar_result(result):
    if not isinstance(result, dict):
        return False, "Sidecar result must be an object."
    if result.get("schema_version") != SCHEMA_VERSION:
        return False, "Unsupported sidecar schema version."
    if "ok" not in result or "findings" not in result:
        return False, "Sidecar result must include ok and findings."
    if not isinstance(result.get("findings"), list):
        return False, "Sidecar findings must be a list."
    return True, ""


def run_sidecar(executable, request):
    timeout = max(1, min(300, int((request or {}).get("timeout_seconds", 15))))
    try:
        result = subprocess.run(
            [os.path.abspath(executable)],
            input=json.dumps(request),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"schema_version": SCHEMA_VERSION, "ok": False, "findings": [], "error": str(exc)}
    if result.returncode != 0:
        return {"schema_version": SCHEMA_VERSION, "ok": False, "findings": [], "error": (result.stderr or "").strip()}
    try:
        parsed = json.loads(result.stdout or "{}")
    except ValueError as exc:
        return {"schema_version": SCHEMA_VERSION, "ok": False, "findings": [], "error": str(exc)}
    ok, msg = validate_sidecar_result(parsed)
    if not ok:
        return {"schema_version": SCHEMA_VERSION, "ok": False, "findings": [], "error": msg}
    return core.redact_value(parsed)


def enforcement_research_gate(feature, reviewed=False, signed_driver=False, rollback=False):
    """Return whether frontier enforcement research can move beyond lab-only planning."""
    blockers = []
    if not reviewed:
        blockers.append("legal/ethical/safety review")
    if feature in ("wfp", "windivert", "per_app_routing") and not signed_driver:
        blockers.append("driver/signing feasibility")
    if not rollback:
        blockers.append("rollback design")
    return {
        "feature": str(feature or ""),
        "lab_only": bool(blockers),
        "blockers": blockers,
        "decision": "research_only" if blockers else "prototype_allowed",
    }


def adapter_failover_recommendation(adapters):
    usable = []
    for adapter in adapters or []:
        if not isinstance(adapter, dict):
            continue
        if adapter.get("up") and adapter.get("gateway"):
            usable.append(adapter)
    if len(usable) < 2:
        return {"status": "single_path", "recommendation": "No multi-adapter failover recommendation is available."}
    ordered = sorted(usable, key=lambda item: (int(item.get("metric", 9999)), str(item.get("name", ""))))
    return {
        "status": "failover_candidate",
        "primary": ordered[0].get("name"),
        "backup": ordered[1].get("name"),
        "recommendation": "Prefer explicit failover guidance before attempting load balancing or bonding.",
    }


def adapter_inventory(query=None):
    """Return a sanitized local adapter inventory for failover recommendations."""
    if query:
        return [dict(item) for item in query()]
    try:
        stats = psutil.net_if_stats()
    except OSError:
        stats = {}
    adapters = []
    for name, stat in sorted(stats.items()):
        gateway = core.get_default_gateway(name) if getattr(stat, "isup", False) else None
        adapters.append(
            {
                "name": name,
                "up": bool(getattr(stat, "isup", False)),
                "gateway": gateway or "",
                "metric": 9999,
                "speed_mbps": int(getattr(stat, "speed", 0) or 0),
            }
        )
    return adapters


def adapter_inventory():
    """Return safe local adapter facts for failover recommendations."""
    stats = psutil.net_if_stats()
    addrs = psutil.net_if_addrs()
    gateways = _default_gateways_by_interface()
    adapters = []
    for name, stat in stats.items():
        addresses = []
        for addr in addrs.get(name, []):
            family = str(getattr(addr.family, "name", addr.family))
            if "AF_INET" in family:
                addresses.append(addr.address)
        adapters.append(
            {
                "name": name,
                "up": bool(stat.isup),
                "speed_mbps": int(stat.speed or 0),
                "gateway": gateways.get(name, ""),
                "metric": _adapter_metric_hint(name, stat),
                "addresses": addresses[:4],
            }
        )
    return adapters


def _default_gateways_by_interface():
    routes = {}
    if hasattr(psutil, "net_if_addrs"):
        try:
            ok, output = core.run_powershell(
                "Get-NetRoute -DestinationPrefix '0.0.0.0/0' | "
                "Select-Object InterfaceAlias,NextHop,RouteMetric | ConvertTo-Json"
            )
        except Exception:
            return routes
        if not ok or not output or output == "Success":
            return routes
        try:
            parsed = json.loads(output)
        except ValueError:
            return routes
        rows = parsed if isinstance(parsed, list) else [parsed]
        for row in rows:
            if isinstance(row, dict):
                name = str(row.get("InterfaceAlias") or "")
                if name:
                    routes[name] = str(row.get("NextHop") or "")
    return routes


def _adapter_metric_hint(name, stat):
    if not getattr(stat, "isup", False):
        return 9999
    lowered = str(name or "").lower()
    if "ethernet" in lowered:
        return 10
    if "wi-fi" in lowered or "wifi" in lowered or "wireless" in lowered:
        return 50
    return 100
