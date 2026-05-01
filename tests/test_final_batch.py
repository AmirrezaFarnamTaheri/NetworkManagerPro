import json

import anomaly_detection
import forensics_plan
import monitor_service
import lucid_cli
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


def test_power_efficiency_policy_can_be_disabled():
    cfg = {"settings": {"check_interval_seconds": 60, "reduce_background_on_battery": False}}
    policy = power_policy.power_efficiency_policy(cfg, {"on_battery": True, "battery_saver": True})

    assert policy["reduced_mode"] is False
    assert policy["poll_interval_seconds"] == 60
    assert policy["pause_ddns"] is False


def test_monitor_interval_combines_metered_and_power_policy(monkeypatch, tmp_path):
    cfg = {"settings": {"check_interval_seconds": 60, "pause_background_on_metered": False}}
    service = monitor_service.MonitorService(cfg, str(tmp_path / "config.json"))

    monkeypatch.setattr("core.get_metered_connection_status", lambda: {"metered": False})
    monkeypatch.setattr("power_policy.get_power_status", lambda: {"on_battery": True, "battery_saver": False})

    assert service._interval(cfg) == 300


def test_cli_status_json_outputs_machine_readable_payload(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setattr(lucid_cli.core, "is_admin", lambda: False)
    monkeypatch.setattr(lucid_cli.core, "get_active_interface_alias", lambda: "Wi-Fi")
    monkeypatch.setattr(lucid_cli.core, "get_dns_servers", lambda: ["1.1.1.1", "1.0.0.1"])
    monkeypatch.setattr(lucid_cli.core, "get_proxy_state", lambda: (True, "127.0.0.1:8080"))
    exit_code = lucid_cli.run(["--json", "status"])
    output = capsys.readouterr().out
    payload = json.loads(output)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["app"] == "Lucid Net"
    assert payload["version"]
    assert payload["active_interface"] == "Wi-Fi"
    assert payload["dns_servers"] == ["1.1.1.1", "1.0.0.1"]
    assert payload["proxy_enabled"] is True


def test_cli_json_flag_is_position_flexible(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    exit_code = lucid_cli.run(["list-dns", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert "Cloudflare" in payload["dns_profiles"]


def test_cli_list_dns_json_outputs_profiles(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    exit_code = lucid_cli.run(["--json", "list-dns"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert "Cloudflare" in payload["dns_profiles"]


def test_cli_dns_apply_profile_calls_core_set_dns(capsys, monkeypatch):
    calls = []
    monkeypatch.setattr(
        lucid_cli.core,
        "load_config",
        lambda: {"dns_profiles": {"Cloudflare": ["1.1.1.1", "1.0.0.1"]}, "settings": {}},
    )
    monkeypatch.setattr(lucid_cli.core, "set_dns", lambda servers, interface=None: calls.append((servers, interface)) or (True, "ok"))

    exit_code = lucid_cli.run(["--json", "dns", "apply", "--profile", "Cloudflare", "--interface", "Wi-Fi"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["success"] is True
    assert calls == [(["1.1.1.1", "1.0.0.1"], "Wi-Fi")]


def test_cli_dns_apply_unknown_profile_fails(capsys, monkeypatch):
    monkeypatch.setattr(lucid_cli.core, "load_config", lambda: {"dns_profiles": {"Cloudflare": ["1.1.1.1"]}, "settings": {}})

    exit_code = lucid_cli.run(["--json", "dns", "apply", "--profile", "Missing"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert payload["ok"] is False
    assert "Unknown DNS profile" in payload["error"]


def test_cli_dns_clear_proxy_and_ddns_mutations(capsys, monkeypatch):
    calls = []
    monkeypatch.setattr(lucid_cli.core, "clear_dns", lambda interface=None: calls.append(("clear_dns", interface)) or (True, "dns cleared"))
    monkeypatch.setattr(lucid_cli.core, "set_proxy", lambda enabled, server="": calls.append(("set_proxy", enabled, server)) or (True, "proxy ok"))
    monkeypatch.setattr(lucid_cli.core, "load_config", lambda: {"settings": {}, "ddns": {"update_url": "https://example.test/update"}})
    monkeypatch.setattr(lucid_cli.core, "get_ddns_update_url", lambda cfg: "https://example.test/update")
    monkeypatch.setattr(lucid_cli.core, "update_ddns", lambda url: calls.append(("update_ddns", url)) or (True, "ddns ok"))

    assert lucid_cli.run(["--json", "dns", "clear", "--interface", "Ethernet"]) == 0
    assert json.loads(capsys.readouterr().out)["message"] == "dns cleared"

    assert lucid_cli.run(["--json", "proxy", "enable", "--server", "127.0.0.1:8080"]) == 0
    assert json.loads(capsys.readouterr().out)["message"] == "proxy ok"

    assert lucid_cli.run(["--json", "proxy", "disable"]) == 0
    assert json.loads(capsys.readouterr().out)["message"] == "proxy ok"

    assert lucid_cli.run(["--json", "ddns", "force"]) == 0
    assert json.loads(capsys.readouterr().out)["message"] == "ddns ok"

    assert calls == [
        ("clear_dns", "Ethernet"),
        ("set_proxy", True, "127.0.0.1:8080"),
        ("set_proxy", False, ""),
        ("update_ddns", "https://example.test/update"),
    ]


def test_cli_profile_proxy_ddns_hosts_and_traffic_commands(capsys, monkeypatch, tmp_path):
    cfg = {
        "settings": {},
        "dns_profiles": {"OfficeDNS": ["1.1.1.1"]},
        "network_profiles": [{"name": "Office", "ssid": "CorpWifi", "dns_profile": "OfficeDNS", "auto_apply": True}],
    }
    monkeypatch.setattr(lucid_cli.core, "load_config", lambda: cfg)
    monkeypatch.setattr(lucid_cli.core, "set_pac_proxy", lambda url: (True, f"pac {url}"))
    monkeypatch.setattr(lucid_cli.core, "set_socks5_proxy", lambda server: (True, f"socks {server}"))
    monkeypatch.setattr(lucid_cli.core, "update_ddns_dual_stack", lambda config: {"ok": True, "results": [], "message": "dual ok"})
    monkeypatch.setattr(
        "traffic_collector.history_summary",
        lambda db_path, limit=24: {"rows": [], "summary": {"samples": 0}, "limit": limit},
    )

    assert lucid_cli.run(["--json", "profiles", "preview", "--ssid", "CorpWifi"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["matched"] is True
    assert payload["steps"][0]["profile"] == "OfficeDNS"

    assert lucid_cli.run(["--json", "proxy", "pac", "--url", "https://proxy.test/wpad.pac"]) == 0
    assert json.loads(capsys.readouterr().out)["message"] == "pac https://proxy.test/wpad.pac"

    assert lucid_cli.run(["--json", "proxy", "socks5", "--server", "127.0.0.1:1080"]) == 0
    assert json.loads(capsys.readouterr().out)["message"] == "socks 127.0.0.1:1080"

    assert lucid_cli.run(["--json", "ddns", "force", "--dual-stack"]) == 0
    assert json.loads(capsys.readouterr().out)["message"] == "dual ok"

    hosts_path = tmp_path / "hosts"
    hosts_path.write_text("127.0.0.1 localhost\n", encoding="utf-8")
    assert lucid_cli.run(["--json", "hosts", "preview", "--file", str(hosts_path), "--group", "dev", "--entry", "10.0.0.2,dev.local,dev"]) == 0
    assert "dev.local" in json.loads(capsys.readouterr().out)["preview"]

    assert lucid_cli.run(["--json", "traffic-history", "--limit", "5"]) == 0
    assert json.loads(capsys.readouterr().out)["limit"] == 5


def test_cli_diagnostics_require_consent(capsys):
    exit_code = lucid_cli.run(["--json", "diagnose", "dns", "--domain", "example.test"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert payload["ok"] is False
    assert "consent" in payload["error"].lower()


def test_cli_diagnostics_emit_mocked_dns_result(capsys, monkeypatch):
    monkeypatch.setattr(
        "deep_diagnostics.run_dns_integrity_diagnostic",
        lambda domain: {"test_id": "dns_integrity", "status": "normal", "evidence": {"domain": domain}},
    )

    exit_code = lucid_cli.run(["--json", "diagnose", "dns", "--domain", "example.test", "--i-consent"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["test_id"] == "dns_integrity"
    assert payload["evidence"]["domain"] == "example.test"


def test_cli_overlay_and_multiwan_are_read_only(capsys, monkeypatch):
    monkeypatch.setattr("overlay_networks.detect_overlay_tools", lambda: {"tailscale": {"installed": False, "path": ""}})
    exit_code = lucid_cli.run(["--json", "overlay-status"])
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
    exit_code = lucid_cli.run(["--json", "multiwan-status"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["recommendation"]["primary"] == "Ethernet"


def test_cli_pcap_plan_and_anomalies(capsys, monkeypatch):
    exit_code = lucid_cli.run(["--json", "pcap-plan", "--duration", "999", "--interface", "Wi-Fi"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["duration_seconds"] == 300
    assert payload["requires_explicit_start"] is True

    monkeypatch.setattr("anomaly_detection.findings_from_metrics_db", lambda: [{"status": "spike"}])
    exit_code = lucid_cli.run(["--json", "anomalies"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["findings"] == [{"status": "spike"}]


def test_adapter_inventory_supports_query_injection():
    inventory = forensics_plan.adapter_inventory(
        query=lambda: [{"name": "Ethernet", "up": True, "gateway": "192.0.2.1", "metric": 10}]
    )

    assert inventory == [{"name": "Ethernet", "up": True, "gateway": "192.0.2.1", "metric": 10}]


def test_findings_from_metrics_db_uses_persisted_metrics(monkeypatch):
    rows = [
        {"bytes_recv": 10, "bytes_sent": 10, "latency_ms": 10},
        {"bytes_recv": 11, "bytes_sent": 10, "latency_ms": 11},
        {"bytes_recv": 12, "bytes_sent": 10, "latency_ms": 12},
        {"bytes_recv": 1000, "bytes_sent": 10, "latency_ms": 13},
    ]
    monkeypatch.setattr("traffic_collector.recent_metrics", lambda db_path, limit=120: list(reversed(rows)))

    findings = anomaly_detection.findings_from_metrics_db("metrics.db")

    assert findings
    assert findings[0]["status"] == "spike"
    assert findings[0]["evidence"]["field"] == "bytes_recv"
