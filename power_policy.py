from __future__ import annotations

import subprocess

import core


def get_power_status(query=None):
    query = query or _query_powercfg
    try:
        status = query()
    except Exception as exc:
        return {"on_battery": None, "battery_saver": None, "source": "error", "detail": str(exc)}
    if isinstance(status, dict):
        return {
            "on_battery": status.get("on_battery") if isinstance(status.get("on_battery"), bool) else None,
            "battery_saver": status.get("battery_saver") if isinstance(status.get("battery_saver"), bool) else None,
            "source": str(status.get("source") or "windows"),
            "detail": str(status.get("detail") or ""),
        }
    return {"on_battery": None, "battery_saver": None, "source": "unknown", "detail": ""}


def power_efficiency_policy(config, power_status=None, minimized=False):
    cfg = core.normalize_config(config)
    settings = cfg.get("settings") or {}
    interval = int(settings.get("check_interval_seconds", 60))
    reduce_on_battery = core.parse_bool(settings.get("reduce_background_on_battery", True), True)
    pause_when_minimized = core.parse_bool(settings.get("pause_ui_refresh_when_minimized", True), True)
    on_battery = isinstance(power_status, dict) and power_status.get("on_battery") is True
    battery_saver = isinstance(power_status, dict) and power_status.get("battery_saver") is True
    reduced = reduce_on_battery and (on_battery or battery_saver)
    pause_ui = pause_when_minimized and bool(minimized)
    effective_reduced = reduced or pause_ui
    return {
        "reduced_mode": effective_reduced,
        "poll_interval_seconds": max(interval, 300) if effective_reduced else interval,
        "suspend_expensive_analytics": effective_reduced,
        "pause_ddns": bool(battery_saver and reduce_on_battery),
        "pause_ui_refresh": pause_ui,
        "reason": "power saving" if effective_reduced else "normal",
    }


def _query_powercfg():
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "(Get-CimInstance -ClassName Win32_Battery | Select-Object -First 1 -ExpandProperty BatteryStatus)"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"on_battery": None, "battery_saver": None, "source": "powershell", "detail": str(exc)}
    text = (result.stdout or "").strip()
    # Win32_Battery BatteryStatus 1 means discharging; 2+ usually means AC/charging/charged.
    return {"on_battery": text == "1", "battery_saver": None, "source": "powershell", "detail": text}
