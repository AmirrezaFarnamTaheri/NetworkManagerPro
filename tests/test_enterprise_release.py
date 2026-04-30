import json

import core
import enterprise_policy
import event_log
import release_verification


def test_enterprise_policy_overrides_user_config():
    cfg = core.normalize_config(
        {
            "settings": {"check_interval_seconds": 30, "rollback_on_connectivity_loss": False},
            "plugins": {"enabled": ["demo_plugin"], "settings": {}},
        }
    )
    policies = {
        "DisablePlugins": 1,
        "ForceRollbackOnConnectivityLoss": 1,
        "MinimumCheckIntervalSeconds": 300,
    }

    updated, managed = enterprise_policy.apply_policy_overrides(cfg, policies)

    assert updated["plugins"]["enabled"] == []
    assert updated["settings"]["rollback_on_connectivity_loss"] is True
    assert updated["settings"]["check_interval_seconds"] == 300
    assert "plugins.enabled" in managed
    assert "settings.rollback_on_connectivity_loss" in managed


def test_event_log_payload_redacts_sensitive_details():
    message = event_log.format_event_message(
        "ddns.sync",
        "updated",
        {"url": "https://provider.test/update?token=secret", "password": "secret"},
    )
    payload = json.loads(message)

    assert payload["type"] == "ddns.sync"
    assert payload["details"]["password"] == "***"
    assert "secret" not in message


def test_release_manifest_roundtrip_and_mismatch_detection(tmp_path):
    artifact = tmp_path / "NetworkManagerPro.exe"
    artifact.write_bytes(b"release artifact")
    manifest_path = tmp_path / "release.json"

    manifest = release_verification.write_release_manifest([str(artifact)], "2.0.0", str(manifest_path))
    assert manifest["version"] == "2.0.0"
    ok, failures = release_verification.verify_manifest(str(manifest_path))
    assert ok is True
    assert failures == []

    artifact.write_bytes(b"changed")
    ok, failures = release_verification.verify_manifest(str(manifest_path))
    assert ok is False
    assert "SHA256 mismatch" in failures[0]


def test_register_event_source_command_escapes_source():
    command = event_log.register_event_source_command("Network'Manager")
    assert "Network''Manager" in command
