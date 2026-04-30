from __future__ import annotations

import copy

try:
    import winreg
except ImportError:  # pragma: no cover - Windows app, import guard for portability.
    winreg = None

import core


POLICY_ROOT = r"SOFTWARE\Policies\NetworkManagerPro"

POLICY_DEFINITIONS = {
    "DisablePlugins": {"path": ("plugins", "enabled"), "type": "disable_list"},
    "DisableProxyChanges": {"path": ("settings", "policy_disable_proxy_changes"), "type": "bool"},
    "DisableDiagnosticsExport": {"path": ("settings", "policy_disable_diagnostics_export"), "type": "bool"},
    "DisableAutoUpdates": {"path": ("settings", "policy_disable_auto_updates"), "type": "bool"},
    "ForceRollbackOnConnectivityLoss": {"path": ("settings", "rollback_on_connectivity_loss"), "type": "bool"},
    "MinimumCheckIntervalSeconds": {"path": ("settings", "check_interval_seconds"), "type": "min_int"},
}


def read_hklm_policies(reader=None):
    """Read machine policies from HKLM or an injected reader for tests."""
    reader = reader or _read_registry_values
    values = reader()
    return normalize_policy_values(values)


def normalize_policy_values(values):
    values = values if isinstance(values, dict) else {}
    clean = {}
    for name, definition in POLICY_DEFINITIONS.items():
        if name not in values:
            continue
        value = values[name]
        if definition["type"] == "bool":
            clean[name] = core.parse_bool(value, False)
        elif definition["type"] == "min_int":
            try:
                clean[name] = max(15, min(86400, int(value)))
            except (TypeError, ValueError):
                continue
        elif definition["type"] == "disable_list":
            clean[name] = bool(core.parse_bool(value, False))
    return clean


def apply_policy_overrides(config, policies):
    """Return (config, managed_state) with HKLM-style policy overrides applied."""
    cfg = core.normalize_config(copy.deepcopy(config))
    managed = {}
    policies = normalize_policy_values(policies)
    for name, value in policies.items():
        definition = POLICY_DEFINITIONS[name]
        target = definition["path"]
        if definition["type"] == "disable_list" and value:
            cfg["plugins"]["enabled"] = []
            managed["plugins.enabled"] = "Disabled by machine policy."
            continue
        if definition["type"] == "min_int":
            current = int(cfg["settings"].get("check_interval_seconds", 60))
            if current < value:
                cfg["settings"]["check_interval_seconds"] = value
                managed["settings.check_interval_seconds"] = f"Minimum enforced by machine policy: {value}"
            continue
        parent = cfg
        for part in target[:-1]:
            parent = parent.setdefault(part, {})
        parent[target[-1]] = value
        managed[".".join(target)] = "Managed by machine policy."
    cfg["_managed_by_policy"] = managed
    return cfg, managed


def _read_registry_values():
    if winreg is None:
        return {}
    values = {}
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, POLICY_ROOT, 0, winreg.KEY_READ) as key:
            index = 0
            while True:
                try:
                    name, value, _kind = winreg.EnumValue(key, index)
                except OSError:
                    break
                values[name] = value
                index += 1
    except OSError:
        return {}
    return values
