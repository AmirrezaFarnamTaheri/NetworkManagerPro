import json

import core
from plugin_api import PluginAPI
from plugin_manager import PluginManager


def write_plugin(root, plugin_id, manifest_updates=None, code="def on_start(api):\n    pass\n"):
    plugin_dir = root / plugin_id
    plugin_dir.mkdir()
    (plugin_dir / "plugin.py").write_text(code, encoding="utf-8")
    manifest = {
        "id": plugin_id,
        "name": "Demo",
        "version": "0.1.0",
        "api_version": PluginAPI.api_version,
        "entrypoint": "plugin.py",
        "permissions": [],
    }
    if manifest_updates:
        manifest.update(manifest_updates)
    (plugin_dir / "plugin.json").write_text(json.dumps(manifest), encoding="utf-8")
    return plugin_dir / "plugin.json"


def test_load_manifest_rejects_missing_keys_invalid_id_api_and_permissions(tmp_path):
    manager = PluginManager({})

    missing = tmp_path / "missing.json"
    missing.write_text(json.dumps({"id": "demo"}), encoding="utf-8")
    try:
        manager._load_manifest(str(missing))
        raise AssertionError("missing manifest keys should fail")
    except ValueError as exc:
        assert "Missing manifest keys" in str(exc)

    invalid_id = write_plugin(tmp_path, "bad_id", {"id": "bad id"})
    try:
        manager._load_manifest(str(invalid_id))
        raise AssertionError("invalid plugin id should fail")
    except ValueError as exc:
        assert "Plugin id may only contain" in str(exc)

    invalid_api = write_plugin(tmp_path, "bad_api", {"api_version": "999"})
    try:
        manager._load_manifest(str(invalid_api))
        raise AssertionError("invalid plugin API should fail")
    except ValueError as exc:
        assert "Unsupported plugin API version" in str(exc)

    invalid_permissions = write_plugin(tmp_path, "bad_permissions", {"permissions": "network_state"})
    try:
        manager._load_manifest(str(invalid_permissions))
        raise AssertionError("invalid permissions should fail")
    except ValueError as exc:
        assert "Plugin permissions must be a list" in str(exc)


def test_load_plugin_rejects_entrypoint_path_traversal(tmp_path):
    manifest_path = write_plugin(tmp_path, "escape", {"entrypoint": "../outside.py"})
    manifest = PluginManager({})._load_manifest(str(manifest_path))

    try:
        PluginManager({})._load_plugin(str(manifest_path), manifest)
        raise AssertionError("entrypoint traversal should fail")
    except ValueError as exc:
        assert "Entrypoint must stay inside plugin directory" in str(exc)


def test_load_enabled_skips_disabled_plugins_and_loads_enabled_plugins(monkeypatch, tmp_path):
    user_plugins = tmp_path / "user_plugins"
    bundled_plugins = tmp_path / "bundled_plugins"
    user_plugins.mkdir()
    bundled_plugins.mkdir()
    write_plugin(user_plugins, "enabled")
    write_plugin(user_plugins, "disabled")

    monkeypatch.setattr(core, "plugins_dir", lambda: str(user_plugins))
    monkeypatch.setattr(core, "bundled_plugins_dir", lambda: str(bundled_plugins))

    manager = PluginManager({"plugins": {"enabled": ["enabled"]}})
    loaded = manager.load_enabled()

    assert [item["manifest"]["id"] for item in loaded] == ["enabled"]


def test_duplicate_plugin_ids_emit_failure_and_do_not_double_load(monkeypatch, tmp_path):
    user_plugins = tmp_path / "user_plugins"
    bundled_plugins = tmp_path / "bundled_plugins"
    user_plugins.mkdir()
    bundled_plugins.mkdir()
    write_plugin(user_plugins, "demo")
    write_plugin(bundled_plugins, "demo")
    events = []

    class EventStore:
        def append(self, event_type, summary, details):
            events.append((event_type, summary, details))

    monkeypatch.setattr(core, "plugins_dir", lambda: str(user_plugins))
    monkeypatch.setattr(core, "bundled_plugins_dir", lambda: str(bundled_plugins))

    loaded = PluginManager({"plugins": {"enabled": ["demo"]}}, event_store=EventStore()).load_enabled()

    assert [item["manifest"]["id"] for item in loaded] == ["demo"]
    assert any(event[0] == "plugin.load_failed" and "Duplicate plugin id" in event[2]["error"] for event in events)
