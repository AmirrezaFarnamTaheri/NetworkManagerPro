import anomaly_detection
import forensics_plan


def test_pcap_capture_plan_is_bounded_and_warns(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    plan = forensics_plan.pcap_capture_plan(duration_seconds=999, interface="Wi-Fi")

    assert plan["duration_seconds"] == 300
    assert plan["requires_explicit_start"] is True
    assert "sensitive content" in plan["warning"]
    assert plan["interface"] == "Wi-Fi"


def test_sidecar_request_and_result_validation():
    request = forensics_plan.sidecar_request("version", {"safe": True}, timeout_seconds=999)
    assert request["timeout_seconds"] == 300
    assert request["command"] == "version"

    assert forensics_plan.validate_sidecar_result({"schema_version": 1, "ok": True, "findings": []}) == (True, "")
    ok, msg = forensics_plan.validate_sidecar_result({"schema_version": 1, "ok": True})
    assert ok is False
    assert "findings" in msg


def test_enforcement_gate_blocks_frontier_work_without_reviews():
    decision = forensics_plan.enforcement_research_gate("windivert", reviewed=False, signed_driver=False, rollback=False)
    assert decision["decision"] == "research_only"
    assert "legal/ethical/safety review" in decision["blockers"]
    assert "driver/signing feasibility" in decision["blockers"]

    allowed = forensics_plan.enforcement_research_gate("wfp", reviewed=True, signed_driver=True, rollback=True)
    assert allowed["decision"] == "prototype_allowed"


def test_adapter_failover_recommendation_orders_by_metric():
    result = forensics_plan.adapter_failover_recommendation(
        [
            {"name": "Wi-Fi", "up": True, "gateway": "192.0.2.1", "metric": 50},
            {"name": "Ethernet", "up": True, "gateway": "192.0.2.254", "metric": 10},
        ]
    )

    assert result["status"] == "failover_candidate"
    assert result["primary"] == "Ethernet"
    assert result["backup"] == "Wi-Fi"


def test_anomaly_detection_finds_statistical_spike():
    rows = [
        {"bytes_recv": 100, "bytes_sent": 50, "latency_ms": 10},
        {"bytes_recv": 110, "bytes_sent": 55, "latency_ms": 11},
        {"bytes_recv": 90, "bytes_sent": 45, "latency_ms": 9},
        {"bytes_recv": 105, "bytes_sent": 52, "latency_ms": 10},
        {"bytes_recv": 1000, "bytes_sent": 52, "latency_ms": 10},
    ]

    finding = anomaly_detection.detect_spike(rows, "bytes_recv", z_threshold=3)
    assert finding["status"] == "spike"
    assert finding["confidence"] == "medium"

    findings = anomaly_detection.explain_anomalies(rows)
    assert any(item["evidence"]["field"] == "bytes_recv" for item in findings)
