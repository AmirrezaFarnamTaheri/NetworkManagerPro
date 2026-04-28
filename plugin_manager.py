import importlib.util
import inspect
import json
import os
import re
import sys

import core
from plugin_api import PluginAPI


class PluginManager:
    def __init__(self, config, monitor=None, event_store=None, ui_host=None):
        self.config = config if isinstance(config, dict) else {}
        self.monitor = monitor
        self.event_store = event_store
        self.ui_host = ui_host
        self.plugins = []
        self._loaded_ids = set()

    def discover(self):
        manifests = []
        seen_dirs = set()
        for root in (core.plugins_dir(), core.bundled_plugins_dir()):
            if root in seen_dirs:
                continue
            seen_dirs.add(root)
            if root == core.plugins_dir():
                os.makedirs(root, exist_ok=True)
            if not os.path.isdir(root):
                continue
            for name in sorted(os.listdir(root)):
                manifest_path = os.path.join(root, name, "plugin.json")
                if os.path.isfile(manifest_path):
                    manifests.append(manifest_path)
        return manifests

    def load_enabled(self):
        enabled = self._enabled_ids()
        seen_ids = set()
        for manifest_path in self.discover():
            try:
                manifest = self._load_manifest(manifest_path)
                plugin_id = manifest["id"]
                if plugin_id in seen_ids:
                    raise ValueError(f"Duplicate plugin id discovered: {plugin_id}")
                seen_ids.add(plugin_id)
                if plugin_id not in enabled:
                    continue
                self._load_plugin(manifest_path, manifest)
            except Exception as exc:
                core.logger().warning("plugin_load_failed manifest=%s error=%s", manifest_path, exc, exc_info=True)
                self._emit("plugin.load_failed", "Plugin failed to load", {"manifest": manifest_path, "error": str(exc)})
        return self.plugins

    def stop_all(self):
        for item in list(self.plugins):
            api = item.get("api")
            module = item.get("module")
            try:
                if hasattr(module, "on_stop"):
                    if len(inspect.signature(module.on_stop).parameters) == 0:
                        module.on_stop()
                    else:
                        module.on_stop(api)
            except Exception:
                core.logger().warning("plugin_stop_failed id=%s", item.get("manifest", {}).get("id"), exc_info=True)
            finally:
                if api:
                    api.stop()
        self.plugins.clear()
        self._loaded_ids.clear()

    def _enabled_ids(self):
        plugins_cfg = self.config.get("plugins") or {}
        enabled = plugins_cfg.get("enabled") or []
        return set(enabled if isinstance(enabled, list) else [])

    def _load_manifest(self, path):
        with open(path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        required = ("id", "name", "version", "api_version", "entrypoint")
        missing = [key for key in required if not manifest.get(key)]
        if missing:
            raise ValueError(f"Missing manifest keys: {', '.join(missing)}")
        if str(manifest["api_version"]) != PluginAPI.api_version:
            raise ValueError(f"Unsupported plugin API version: {manifest['api_version']}")
        if not re.match(r"^[A-Za-z0-9_.-]+$", str(manifest["id"])):
            raise ValueError("Plugin id may only contain letters, numbers, dot, dash, and underscore")
        permissions = manifest.get("permissions", [])
        if not isinstance(permissions, list) or not all(isinstance(item, str) for item in permissions):
            raise ValueError("Plugin permissions must be a list of strings")
        return manifest

    def _load_plugin(self, manifest_path, manifest):
        if manifest["id"] in self._loaded_ids:
            raise ValueError(f"Plugin is already loaded: {manifest['id']}")
        plugin_dir = os.path.dirname(manifest_path)
        entrypoint = os.path.abspath(os.path.join(plugin_dir, manifest["entrypoint"]))
        plugin_root = os.path.abspath(plugin_dir)
        if os.path.commonpath([plugin_root, entrypoint]) != plugin_root:
            raise ValueError("Entrypoint must stay inside plugin directory")
        if not os.path.isfile(entrypoint):
            raise FileNotFoundError(entrypoint)

        spec = importlib.util.spec_from_file_location(f"nmp_plugin_{manifest['id']}", entrypoint)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load plugin entrypoint: {entrypoint}")
        module = importlib.util.module_from_spec(spec)
        sys.path.insert(0, plugin_dir)
        try:
            spec.loader.exec_module(module)
        finally:
            try:
                sys.path.remove(plugin_dir)
            except ValueError:
                pass

        api = PluginAPI(
            manifest["id"],
            self.config,
            self.monitor,
            self.event_store,
            self.ui_host,
            permissions=manifest.get("permissions", []),
        )
        item = {"manifest": manifest, "module": module, "api": api}
        try:
            if hasattr(module, "on_start"):
                module.on_start(api)
            if hasattr(module, "register_ui") and self.ui_host:
                module.register_ui(api)
        except Exception:
            api.stop()
            raise
        self.plugins.append(item)
        self._loaded_ids.add(manifest["id"])
        self._emit("plugin.loaded", f"Plugin loaded: {manifest['name']}", {"id": manifest["id"], "version": manifest["version"]})
        return item

    def _emit(self, event_type, summary, details):
        if self.event_store:
            self.event_store.append(event_type, summary, details)
        else:
            core.logger().info("%s %s %s", event_type, summary, details)
