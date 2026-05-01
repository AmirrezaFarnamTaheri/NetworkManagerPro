import json
import zipfile

import lucid_cli
import plugin_host
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
    assert plan["environment"]["plugin_id"] == "demo"
    assert plan["environment"]["lock_path"].endswith("environment-lock.json")
    assert plan["permissions"][0]["permission"] == "events"


def test_environment_lock_records_dependency_metadata(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    lock = plugin_platform.write_environment_lock(
        {"id": "demo", "dependencies": ["requests==2.0", "requests==2.0"], "requirements": "requirements.txt"},
        created_by="test",
    )

    assert lock["plugin_id"] == "demo"
    assert lock["dependencies"] == ["requests==2.0"]
    assert lock["created_by"] == "test"
    assert (tmp_path / "LucidNet" / "plugin_envs" / "demo" / "environment-lock.json").exists()


def test_create_plugin_environment_can_write_lock_without_installing_dependencies(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    result = plugin_platform.create_plugin_environment({"id": "demo", "dependencies": ["requests==2.0"]})

    assert result["ok"] is True
    assert any(action["action"] == "install_dependencies" for action in result["actions"])
    assert (tmp_path / "LucidNet" / "plugin_envs" / "demo" / "environment-lock.json").exists()


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


def test_marketplace_install_plan_marks_signature_risk():
    plan = plugin_platform.marketplace_install_plan(
        {
            "schema_version": 1,
            "plugins": [
                {"id": "demo", "name": "Demo", "version": "2", "publisher": "Lab", "permissions": ["events"]},
            ],
        },
        {"demo": "1"},
    )

    assert plan["plugins"][0]["action"] == "update"
    assert plan["plugins"][0]["signature_state"] == "missing"
    assert plan["plugins"][0]["risk"] == "high"


def test_marketplace_operation_blocks_unsigned_install():
    registry = {
        "schema_version": 1,
        "plugins": [{"id": "demo", "name": "Demo", "version": "1", "publisher": "Lab", "permissions": ["events"]}],
    }

    result = plugin_platform.marketplace_operation(registry, "demo", "install")

    assert result["ok"] is False
    assert "Signed bundle metadata" in result["error"]


def test_signed_bundle_install_enforces_trusted_publisher(tmp_path):
    plugin_dir = write_plugin(tmp_path, "signed")
    bundle = plugin_platform.bundle_manifest(str(plugin_dir))
    signature = plugin_platform.signed_bundle_metadata(str(plugin_dir), "Lab", "key-1", signature="placeholder")
    (plugin_dir / "bundle-manifest.json").write_text(json.dumps(bundle), encoding="utf-8")
    (plugin_dir / "signature.json").write_text(json.dumps(signature), encoding="utf-8")
    archive = tmp_path / "signed.lucid-plugin"
    with zipfile.ZipFile(archive, "w") as zf:
        for path in plugin_dir.iterdir():
            zf.write(path, path.name)

    install_root = tmp_path / "installed"
    result = plugin_platform.install_plugin_bundle(str(archive), str(install_root), trusted_publishers=["Other"])

    assert result["ok"] is False
    assert any("Publisher is not trusted" in item for item in result["failures"])


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


def test_plugin_manager_selectively_reloads_changed_plugins(monkeypatch, tmp_path):
    user_plugins = tmp_path / "plugins"
    write_plugin(user_plugins, "one", body="def on_start(api):\n    api.get_config({'value': 1})\n")
    write_plugin(user_plugins, "two", body="def on_start(api):\n    api.get_config({'value': 2})\n")
    monkeypatch.setattr("core.plugins_dir", lambda: str(user_plugins))
    monkeypatch.setattr("core.bundled_plugins_dir", lambda: str(tmp_path / "bundled"))

    manager = PluginManager({"plugins": {"enabled": ["one", "two"], "settings": {}}})
    manager.load_enabled()
    (user_plugins / "one" / "plugin.py").write_text("def on_start(api):\n    api.get_config({'value': 3})\n", encoding="utf-8")
    reloaded = manager.reload_changed()

    assert [item["manifest"]["id"] for item in reloaded] == ["one"]
    assert sorted(item["manifest"]["id"] for item in manager.plugins) == ["one", "two"]


def test_plugin_host_run_once_captures_plugin_events(tmp_path):
    manifest_path = write_plugin(tmp_path, body="def on_start(api):\n    api.emit_event('ready', 'Ready', {'ok': True})\n") / "plugin.json"

    result = plugin_host.run_once(str(manifest_path))

    assert result["ok"] is True
    assert result["events"][0]["type"] == "plugin.demo_plugin.ready"


def test_cli_plugin_host_health_json(capsys):
    code = lucid_cli.run(["--json", "plugins", "host-health"])
    output = json.loads(capsys.readouterr().out)

    assert code == 0
    assert output["ok"] is True
    assert output["host"] == "plugin_host"
