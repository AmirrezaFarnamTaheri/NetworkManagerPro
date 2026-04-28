from __future__ import annotations

import copy
import os
import threading
import time
from dataclasses import dataclass, field

import core


@dataclass
class NetworkState:
    timestamp: float = field(default_factory=time.time)
    interface: str | None = None
    gateway: str | None = None
    dns_servers: list[str] = field(default_factory=list)
    proxy_enabled: bool = False
    proxy_server: str | None = None
    public_ip: str | None = None
    latency: str = "n/a"
    ddns_last_result: str = "Not run"
    config_mtime: float = 0.0
    monitor_error: str | None = None


class MonitorService:
    """Single polling loop for GUI status, DDNS, and settings-change events."""

    def __init__(self, config, config_path, event_store=None):
        self.config = core.normalize_config(copy.deepcopy(config)) if isinstance(config, dict) else core.default_config()
        self.config_path = config_path
        self.event_store = event_store
        self._state = NetworkState()
        self._state_lock = threading.RLock()
        self._stop = threading.Event()
        self._thread = None
        self._last_seen_public_ip = None
        self._last_ddns_success_ip = None
        self._ddns_failures = 0
        self._next_ddns_retry = 0.0
        self._last_snapshot = None
        self._ddns_last_result = "Not run"

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, name="NetworkMonitor", daemon=True)
        self._thread.start()
        self.emit_event("monitor.started", "Network monitor started")

    def stop(self):
        self._stop.set()
        if self._thread and self._thread.is_alive() and threading.current_thread() is not self._thread:
            self._thread.join(timeout=3)

    def snapshot(self):
        with self._state_lock:
            return copy.deepcopy(self._state)

    def config_snapshot(self):
        with self._state_lock:
            return copy.deepcopy(self.config)

    def update_config(self, cfg):
        if isinstance(cfg, dict):
            with self._state_lock:
                self.config = core.normalize_config(copy.deepcopy(cfg))

    def emit_event(self, event_type, summary, details=None, attribution="NetworkManagerPro"):
        if self.event_store:
            try:
                return self.event_store.append(event_type, summary, details or {}, attribution)
            except Exception:
                core.logger().warning("event_emit_failed type=%s", event_type, exc_info=True)
        return None

    def force_ddns_sync(self):
        cfg = self.config_snapshot()
        url = core.get_ddns_update_url(cfg)
        valid, normalized_or_error = core.validate_http_url(url, required=True)
        if not valid:
            self._set_ddns_result(normalized_or_error)
            self.emit_event("ddns.sync", normalized_or_error, {"ok": False, "url": ""})
            return False, normalized_or_error
        ok, msg = core.update_ddns(normalized_or_error)
        public_ip = self.snapshot().public_ip
        if ok and public_ip:
            self._mark_ddns_success(public_ip)
        self._set_ddns_result(msg)
        self.emit_event("ddns.sync", msg, {"ok": ok, "url": core.sanitize_url(normalized_or_error, redact_path=True)})
        return ok, msg

    def _run(self):
        while not self._stop.is_set():
            started = time.monotonic()
            try:
                cfg = self._reload_config_if_changed()
                state = self._collect_state(cfg)
                with self._state_lock:
                    state.config_mtime = self._state.config_mtime
                self._detect_settings_changes(state)
                ddns_result = self._maybe_update_ddns(cfg, state.public_ip)
                with self._state_lock:
                    if ddns_result:
                        self._ddns_last_result = ddns_result
                    state.ddns_last_result = self._ddns_last_result
                    self._state = state
                core.logger().debug("monitor_collect duration=%.3fs", time.monotonic() - started)
                self._sleep(self._interval(cfg))
            except Exception as exc:
                core.logger().warning("monitor_loop_failed error=%s", exc, exc_info=True)
                self.emit_event("monitor.error", "Network monitor recovered from an error", {"error": str(exc)})
                with self._state_lock:
                    self._state.monitor_error = str(exc)
                self._sleep(15)

    def _reload_config_if_changed(self):
        try:
            mtime = os.path.getmtime(self.config_path)
        except OSError:
            mtime = 0.0
        with self._state_lock:
            current_mtime = self._state.config_mtime
        if mtime and mtime != current_mtime:
            try:
                cfg = core.load_config(self.config_path)
                if isinstance(cfg, dict):
                    with self._state_lock:
                        self.config = cfg
                        self._state.config_mtime = mtime
                    self.emit_event("config.reload", "Configuration reloaded from disk")
            except Exception:
                core.logger().warning("config_reload_failed path=%s", self.config_path, exc_info=True)
        with self._state_lock:
            cfg = copy.deepcopy(self.config)
            self._state.config_mtime = mtime
        return cfg

    def _collect_state(self, cfg):
        interface = self._safe_call(core.get_active_interface_alias)
        dns = self._safe_call(core.get_dns_servers, interface, default=[])
        gateway = self._safe_call(core.get_default_gateway, interface)
        proxy_enabled, proxy_server = self._safe_call(core.get_proxy_state, default=(False, None))
        public_ip = self._safe_call(core.get_public_ip)
        profile = self._selected_profile(cfg)
        primary = profile[0] if profile else None
        latency = self._safe_call(core.measure_latency, primary, default="n/a") if primary else "n/a"
        return NetworkState(
            interface=interface,
            gateway=gateway,
            dns_servers=dns,
            proxy_enabled=proxy_enabled,
            proxy_server=proxy_server,
            public_ip=public_ip,
            latency=latency,
        )

    def _detect_settings_changes(self, state):
        snapshot = {
            "interface": state.interface,
            "dns_servers": state.dns_servers,
            "proxy_enabled": state.proxy_enabled,
            "proxy_server": state.proxy_server,
        }
        if self._last_snapshot is not None and snapshot != self._last_snapshot:
            self.emit_event("settings.changed", "Effective network settings changed", snapshot, "Unknown")
        self._last_snapshot = snapshot

    def _maybe_update_ddns(self, cfg, public_ip):
        settings = cfg.get("settings") or {}
        auto_update = core.parse_bool(settings.get("auto_update_ddns", False), False)
        if public_ip:
            self._last_seen_public_ip = public_ip
        if not public_ip or not auto_update or public_ip == self._last_ddns_success_ip:
            return None
        now = time.monotonic()
        if now < self._next_ddns_retry:
            return None

        url = core.get_ddns_update_url(cfg)
        valid, normalized_or_error = core.validate_http_url(url, required=True)
        if not valid:
            msg = normalized_or_error
            self._set_ddns_result(msg)
            self._schedule_ddns_retry()
            self.emit_event("ddns.auto_sync", msg, {"ok": False, "public_ip": public_ip, "url": ""})
            return msg

        ok, msg = core.update_ddns(normalized_or_error)
        if ok:
            self._mark_ddns_success(public_ip)
        else:
            self._schedule_ddns_retry()
        self._set_ddns_result(msg)
        self.emit_event(
            "ddns.auto_sync",
            msg,
            {"ok": ok, "public_ip": public_ip, "url": core.sanitize_url(normalized_or_error, redact_path=True)},
        )
        return msg

    def _mark_ddns_success(self, public_ip):
        self._last_ddns_success_ip = public_ip
        self._ddns_failures = 0
        self._next_ddns_retry = 0.0

    def _schedule_ddns_retry(self):
        self._ddns_failures += 1
        self._next_ddns_retry = time.monotonic() + min(3600, 30 * (2 ** min(self._ddns_failures - 1, 6)))

    def _set_ddns_result(self, msg):
        with self._state_lock:
            self._ddns_last_result = msg
            self._state.ddns_last_result = msg

    def _selected_profile(self, cfg):
        profiles = cfg.get("dns_profiles") or {}
        if not isinstance(profiles, dict) or not profiles:
            return []
        first = next(iter(profiles.values()))
        return first if isinstance(first, list) else []

    def _interval(self, cfg):
        settings = cfg.get("settings") or {}
        try:
            return max(15, min(86400, int(settings.get("check_interval_seconds", 60))))
        except (TypeError, ValueError):
            return 60

    def _safe_call(self, func, *args, default=None):
        try:
            return func(*args)
        except Exception as exc:
            core.logger().warning(
                "monitor_collect_call_failed func=%s error=%s",
                getattr(func, "__name__", func),
                exc,
                exc_info=True,
            )
            return default

    def _sleep(self, seconds):
        end = time.monotonic() + seconds
        while not self._stop.is_set() and time.monotonic() < end:
            self._stop.wait(min(1.0, max(0.0, end - time.monotonic())))
