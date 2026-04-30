import json

import nmp_cli
import overlay_networks
import power_policy
import signing_research


def test_overlay_detection_and_operation_gate():
    found = overlay_networks.detect_overlay_tools(which=lambda name: "C:/bin/tailscale.exe" if name == "tailscale" else None)

    assert found["tailscale"]["installed"] is True
    assert found["zerotier"]["installed"] is False
    assert overlay_networks.read_only_status_command("tailscale") == ["tailscale", "status", "--json"]

    read_only = overlay_networks.overlay_operation_gate("read_status")
    assert read_only["allowed"] is True

    mutating = overlay_networks.overlay_operation_gate("set_exit_node", consent=False, vendor_reviewed=False)
    assert mutating["allowed"] is False
    assert "explicit user consent" in mutating["blockers"]


def test_signature_metadata_is_algorithm_agile_but_research_gated():
    classical = signing_research.signature_metadata("ed25519", "first-party")
    assert signing_research.validate_signature_metadata(classical) == (True, "")

    pq = signing_research.signature_metadata("ml-dsa-44", "research")
    assert signing_research.validate_signature_metadata(pq)[0] is False
    assert signing_research.validate_signature_metadata(pq, allow_research=True) == (True, "")

    plan = signing_research.algorithm_agility_plan()
    assert "ml-dsa-44" in plan["research_only_algorithms"]


def test_power_efficiency_policy_reduces_work_on_battery():
    cfg = {"settings": {"check_interval_seconds": 60}}
    policy = power_policy.power_efficiency_policy(cfg, {"on_battery": True, "battery_saver": False})

    assert policy["reduced_mode"] is True
    assert policy["poll_interval_seconds"] == 300
    assert policy["suspend_expensive_analytics"] is True

    normal = power_policy.power_efficiency_policy(cfg, {"on_battery": False, "battery_saver": False})
    assert normal["reduced_mode"] is False
    assert normal["poll_interval_seconds"] == 60


def test_cli_status_json_outputs_machine_readable_payload(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    exit_code = nmp_cli.run(["--json", "status"])
    output = capsys.readouterr().out
    payload = json.loads(output)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["app"] == "Network Manager Pro"
    assert payload["version"]


def test_cli_list_dns_json_outputs_profiles(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    exit_code = nmp_cli.run(["--json", "list-dns"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert "Cloudflare" in payload["dns_profiles"]


def test_cli_diagnostics_require_consent(capsys):
    exit_code = nmp_cli.run(["--json", "diagnose", "dns", "--domain", "example.test"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert payload["ok"] is False
    assert "consent" in payload["error"].lower()


def test_cli_diagnostics_emit_mocked_dns_result(capsys, monkeypatch):
    monkeypatch.setattr(
        "deep_diagnostics.run_dns_integrity_diagnostic",
        lambda domain: {"test_id": "dns_integrity", "status": "normal", "evidence": {"domain": domain}},
    )

    exit_code = nmp_cli.run(["--json", "diagnose", "dns", "--domain", "example.test", "--i-consent"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["test_id"] == "dns_integrity"
    assert payload["evidence"]["domain"] == "example.test"


def test_cli_overlay_and_multiwan_are_read_only(capsys, monkeypatch):
    monkeypatch.setattr("overlay_networks.detect_overlay_tools", lambda: {"tailscale": {"installed": False, "path": ""}})
    exit_code = nmp_cli.run(["--json", "overlay-status"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["statuses"]["tailscale"]["error"] == "Not installed."

    monkeypatch.setattr(
        "forensics_plan.adapter_inventory",
        lambda: [
            {"name": "Ethernet", "up": True, "gateway": "192.0.2.1", "metric": 10},
            {"name": "Wi-Fi", "up": True, "gateway": "192.0.2.2", "metric": 50},
        ],
    )
    exit_code = nmp_cli.run(["--json", "multiwan-status"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["recommendation"]["primary"] == "Ethernet"


def test_cli_pcap_plan_and_anomalies(capsys, monkeypatch):
    exit_code = nmp_cli.run(["--json", "pcap-plan", "--duration", "999", "--interface", "Wi-Fi"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["duration_seconds"] == 300
    assert payload["requires_explicit_start"] is True

    monkeypatch.setattr("anomaly_detection.findings_from_metrics_db", lambda: [{"status": "spike"}])
    exit_code = nmp_cli.run(["--json", "anomalies"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["findings"] == [{"status": "spike"}]
