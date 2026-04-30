import copy
import threading

import core


class PluginAPI:
    api_version = "1"
    min_periodic_interval_seconds = 5

    def __init__(self, plugin_id, config, monitor, event_store, ui_host=None, permissions=None):
        self.plugin_id = plugin_id
        self._config = config
        self._monitor = monitor
        self._event_store = event_store
        self._ui_host = ui_host
        self._permissions = set(permissions or [])
        self._tasks = []
        self._tasks_lock = threading.RLock()

    def _has_permission(self, permission):
        return permission in self._permissions

    def _require_permission(self, permission):
        if not self._has_permission(permission):
            core.logger().warning("plugin_permission_denied id=%s permission=%s", self.plugin_id, permission)
            raise PermissionError(f"Plugin manifest does not grant {permission} permission.")

    def network_state(self):
        self._require_permission("network_state")
        return self._monitor.snapshot() if self._monitor else None

    def emit_event(self, event_type, summary, details=None):
        self._require_permission("events")
        if self._event_store:
            return self._event_store.append(f"plugin.{self.plugin_id}.{event_type}", summary, details or {}, self.plugin_id)
        return None

    def get_config(self, default=None):
        if not isinstance(self._config, dict):
            self._config = {}
        plugins = self._config.get("plugins")
        if not isinstance(plugins, dict):
            plugins = {}
            self._config["plugins"] = plugins
        settings = plugins.get("settings")
        if not isinstance(settings, dict):
            settings = {}
            plugins["settings"] = settings
        if self.plugin_id not in settings:
            settings[self.plugin_id] = copy.deepcopy(default) if default is not None else {}
        return settings[self.plugin_id]

    def register_tab(self, title, builder):
        self._require_permission("ui")
        if self._ui_host:
            self._ui_host.register_plugin_tab(self.plugin_id, title, builder)

    def register_periodic_task(self, name, interval_seconds, callback):
        self._require_permission("scheduled_tasks")
        stop = threading.Event()
        try:
            interval = max(self.min_periodic_interval_seconds, int(interval_seconds))
        except (TypeError, ValueError):
            interval = 60

        def _runner():
            while not stop.wait(interval):
                try:
                    callback(self)
                except Exception as exc:
                    if self._has_permission("events") and not self.emit_event("task_failed", f"{name} failed", {"error": str(exc)}):
                        core.logger().warning("plugin_task_failed id=%s name=%s error=%s", self.plugin_id, name, exc, exc_info=True)
                    elif not self._has_permission("events"):
                        core.logger().warning("plugin_task_failed id=%s name=%s error=%s", self.plugin_id, name, exc, exc_info=True)

        thread = threading.Thread(target=_runner, name=f"PluginTask-{self.plugin_id}-{name}", daemon=True)
        with self._tasks_lock:
            self._tasks.append((stop, thread, name))
        thread.start()

    def stop(self):
        with self._tasks_lock:
            tasks = list(self._tasks)
        for stop, _thread, _name in tasks:
            stop.set()
        still_running = []
        for _stop, thread, name in tasks:
            if thread.is_alive():
                thread.join(timeout=1)
            if thread.is_alive():
                core.logger().warning("plugin_task_stop_timeout id=%s name=%s", self.plugin_id, name)
                still_running.append((_stop, thread, name))
        with self._tasks_lock:
            self._tasks = still_running
