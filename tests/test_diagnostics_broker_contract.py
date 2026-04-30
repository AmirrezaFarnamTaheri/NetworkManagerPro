import json
import zipfile

import broker_contract
import core
import diagnostics
import traffic_collector
from history_store import EventStore


def test_diagnostics_summary_has_manifest_fields_and_redacts_config(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    cfg = core.normalize_config(
        {
            "plugins": {"enabled": ["demo_plugin"], "settings": {"demo_plugin": {"token": "secret"}}},
            "ddns_update_url": "https://provider.test/update?token=secret",
        }
    )

    summary = diagnostics.diagnostics_summary(cfg, {"public_ip": "203.0.113.10"})

    assert summary["schema_version"] == diagnostics.DIAGNOSTICS_SCHEMA_VERSION
    assert summary["config_schema_version"] == core.CONFIG_VERSION
    assert summary["enabled_plugin_ids"] == ["demo_plugin"]
    assert summary["config"]["plugins"]["settings"]["demo_plugin"]["token"] == "***"


def test_diagnostics_bundle_includes_manifest_history_and_traffic(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    core.ensure_runtime_dirs()
    EventStore(core.history_db_path()).append("test.event", "hello", {"token": "secret"})
    traffic_collector.append_metrics(
        core.traffic_metrics_db_path(),
        totals={"bytes_sent": 1, "bytes_recv": 2, "packets_sent": 3, "packets_recv": 4},
        timestamp=1,
    )

    path = diagnostics.export_bundle(core.default_config(), None)

    with zipfile.ZipFile(path) as bundle:
        names = set(bundle.namelist())
        assert "manifest.json" in names
        assert "summary.json" in names
        assert "history/events.jsonl" in names
        assert "history/traffic_metrics.jsonl" in names
        manifest = json.loads(bundle.read("manifest.json").decode("utf-8"))
        assert manifest["schema_version"] == diagnostics.DIAGNOSTICS_SCHEMA_VERSION


def test_broker_contract_validates_commands_and_required_args():
    request = broker_contract.make_request("dns.set", {"interface": "Wi-Fi", "servers": ["1.1.1.1"]})
    assert broker_contract.validate_request(request) == (True, "")
    assert "dns.set" in broker_contract.privileged_commands()

    bad = broker_contract.make_request("dns.set", {"interface": "Wi-Fi"})
    ok, msg = broker_contract.validate_request(bad)
    assert ok is False
    assert "servers" in msg

    response = broker_contract.make_response(request, True, "ok", event={"type": "broker.command"})
    assert response["request_id"] == request["request_id"]
    assert response["ok"] is True
