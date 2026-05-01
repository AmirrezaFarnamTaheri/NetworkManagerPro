import json

import core
import enterprise_policy
import event_log
from history_store import EventStore
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
        "EnableWindowsEventLogExport": 1,
        "ForceRollbackOnConnectivityLoss": 1,
        "MinimumCheckIntervalSeconds": 300,
    }

    updated, managed = enterprise_policy.apply_policy_overrides(cfg, policies)

    assert updated["plugins"]["enabled"] == []
    assert updated["settings"]["rollback_on_connectivity_loss"] is True
    assert updated["settings"]["policy_enable_windows_event_log_export"] is True
    assert updated["settings"]["check_interval_seconds"] == 300
    assert "plugins.enabled" in managed
    assert "settings.rollback_on_connectivity_loss" in managed
    ui_state = enterprise_policy.managed_ui_state(updated)
    assert ui_state["plugins_locked"] is True
    assert ui_state["messages"]["plugins.enabled"] == "Disabled by machine policy."


def test_enterprise_admx_templates_exist_and_track_policy_names():
    admx = open("enterprise/LucidNet.admx", "r", encoding="utf-8").read()
    adml = open("enterprise/en-US/LucidNet.adml", "r", encoding="utf-8").read()

    assert "LucidNet" in admx
    assert "DisablePlugins" in admx
    assert "EnableWindowsEventLogExport" in admx
    assert "Disable plugins" in adml
    assert "DisablePlugins" in enterprise_policy.admx_policy_names()


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


def test_event_store_can_mirror_sanitized_events_to_event_log(tmp_path):
    calls = []
    store = EventStore(
        str(tmp_path / "events.sqlite3"),
        mirror_event_log=True,
        event_writer=lambda event_type, summary, details: calls.append((event_type, summary, details)) or (True, "ok"),
    )

    store.append("ddns.sync", "updated", {"password": "secret"})

    assert calls == [("ddns.sync", "updated", {"password": "***"})]


def test_release_manifest_roundtrip_and_mismatch_detection(tmp_path):
    artifact = tmp_path / "LucidNet.exe"
    artifact.write_bytes(b"release artifact")
    manifest_path = tmp_path / "release.json"

    manifest = release_verification.write_release_manifest([str(artifact)], "1.0.0", str(manifest_path))
    assert manifest["version"] == "1.0.0"
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
    assert "powershell" in event_log.installer_registration_command("LucidNet")


def test_installer_supports_explicit_user_data_purge_switch():
    text = open("installer/LucidNet.iss", "r", encoding="utf-8").read()

    assert "/PURGEUSERDATA" in text
    assert "CurUninstallStepChanged" in text
    assert "DelTree(ExpandConstant('{localappdata}\\LucidNet')" in text
    assert "{localappdata}\\LucidNet" in text
    assert "New-EventLog" in text


def test_build_script_reads_version_from_runtime_constant_and_writes_manifest():
    text = open("scripts/build_release.ps1", "r", encoding="utf-8").read()

    assert "import branding; print(branding.PRODUCT_VERSION)" in text
    assert "release-manifest.json" in text
    assert "write_release_manifest" in text
    assert "Invoke-SignArtifact" in text
    assert "$env:LOCALAPPDATA\\Programs\\Inno Setup 6\\ISCC.exe" in text
    assert "signtool.exe" in text


def test_release_signing_plan_and_optional_signature_verification(tmp_path):
    artifact = tmp_path / "LucidNet.exe"
    artifact.write_bytes(b"release artifact")
    manifest_path = tmp_path / "release.json"
    release_verification.write_release_manifest([str(artifact)], "1.0.0", str(manifest_path))

    plan = release_verification.signing_plan("cert.pfx")
    assert plan["enabled"] is True
    assert "authenticode_verify" in plan["post_build_checks"]
    ok, failures = release_verification.verify_release_artifacts(str(manifest_path), require_signature=False)
    assert ok is True
    assert failures == []
