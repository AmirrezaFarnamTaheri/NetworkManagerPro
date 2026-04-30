import json

import plugin_platform
from plugin_manager import PluginManager


def write_plugin(root, plugin_id="demo_plugin", body="def on_start(api):\n    pass\n"):
    plugin_dir = root / plugin_id
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "plugin.py").write_text(body, encoding="utf-8")
    manifest = {
        "id": plugin_id,
        "name": "Demo",
        "version": "1.0.0",
        "api_version": "1",
        "entrypoint": "plugin.py",
        "permissions": ["events"],
    }
    (plugin_dir / "plugin.json").write_text(json.dumps(manifest), encoding="utf-8")
    return plugin_dir


def test_plugin_permission_validation_rejects_unknown_capabilities():
    assert plugin_platform.validate_permissions(["events", "events"]) == (True, ["events"])
    ok, msg = plugin_platform.validate_permissions(["network_state", "raw_socket"])
    assert ok is False
    assert "raw_socket" in msg


def test_isolation_plan_and_venv_path_are_deterministic(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    plan = plugin_platform.isolation_plan({"id": "demo", "permissions": ["events"], "timeout_seconds": 7})

    assert plan["mode"] == "subprocess"
    assert plan["plugin_id"] == "demo"
    assert plan["timeout_seconds"] == 7
    assert plan["venv_path"].endswith("plugin_envs\\demo") or plan["venv_path"].endswith("plugin_envs/demo")
    assert plan["permissions"][0]["permission"] == "events"


def test_bundle_manifest_verifies_digest_and_detects_tampering(tmp_path):
    plugin_dir = write_plugin(tmp_path)
    bundle = plugin_platform.bundle_manifest(str(plugin_dir))

    ok, failures = plugin_platform.verify_bundle_manifest(str(plugin_dir), bundle)
    assert ok is True
    assert failures == []

    (plugin_dir / "plugin.py").write_text("changed = True\n", encoding="utf-8")
    ok, failures = plugin_platform.verify_bundle_manifest(str(plugin_dir), bundle)
    assert ok is False
    assert "Digest mismatch" in failures[0]


def test_marketplace_registry_filters_invalid_permissions():
    registry = plugin_platform.parse_marketplace_registry(
        {
            "schema_version": 1,
            "plugins": [
                {"id": "ok", "name": "Okay", "version": "1", "permissions": ["events"]},
                {"id": "bad", "name": "Bad", "version": "1", "permissions": ["raw_socket"]},
            ],
        }
    )

    assert [item["id"] for item in registry["plugins"]] == ["ok"]


def test_plugin_manager_detects_changed_manifest_fingerprint(monkeypatch, tmp_path):
    user_plugins = tmp_path / "plugins"
    write_plugin(user_plugins)
    monkeypatch.setattr("core.plugins_dir", lambda: str(user_plugins))
    monkeypatch.setattr("core.bundled_plugins_dir", lambda: str(tmp_path / "bundled"))

    manager = PluginManager({"plugins": {"enabled": ["demo_plugin"], "settings": {}}})
    manager.load_enabled()
    assert manager.changed_manifests() == []

    plugin_file = user_plugins / "demo_plugin" / "plugin.py"
    plugin_file.write_text("def on_start(api):\n    api.get_config({})\n", encoding="utf-8")
    changed = manager.changed_manifests()
    assert len(changed) == 1
    assert changed[0].endswith("plugin.json")
