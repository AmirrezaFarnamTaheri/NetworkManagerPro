import json
from pathlib import Path

import diagnostics
import frontier_policy
import nmp_cli


def test_frontier_catalog_contains_all_major_capability_families():
    ids = {item["id"] for item in frontier_policy.capability_catalog()}

    assert "etw_per_process_bandwidth" in ids
    assert "plugin_sandboxing" in ids
    assert "windows_service_architecture" in ids
    assert "doh_dot_controls" in ids
    assert "pcap_export" in ids
    assert "wfp_enforcement" in ids
    assert "windivert_enforcement" in ids
    assert "per_app_routing" in ids
    assert "multi_wan_load_balancing" in ids
    assert "ai_anomaly_detection" in ids
    assert "overlay_orchestration" in ids
    assert "domain_fronting_research" in ids
    assert "traffic_camouflage_research" in ids
    assert "advanced_anti_censorship" in ids
    assert "post_quantum_plugin_signing" in ids
    assert "siem_opentelemetry_export" in ids
    assert "transport_route_diagnostics" in ids
    assert "wasm_plugin_runtime" in ids


def test_operational_bypass_and_evasion_operations_are_blocked_even_with_reviews():
    for operation in ("bypass", "evasion", "traffic_camouflage", "domain_fronting"):
        decision = frontier_policy.evaluate_capability(
            "advanced_anti_censorship",
            operation=operation,
            consent=True,
            reviews=frontier_policy.EXTERNAL_REVIEWS,
            lab_mode=True,
        )

        assert decision["allowed"] is False
        assert decision["decision"] == "blocked_operational_bypass"
        assert "operational bypass/evasion is not implemented" in decision["blockers"]


def test_research_prototype_requires_consent_lab_mode_and_reviews():
    blocked = frontier_policy.evaluate_capability("wfp_enforcement", operation="prototype")
    assert blocked["allowed"] is False
    assert "explicit user consent" in blocked["blockers"]
    assert "lab mode" in blocked["blockers"]
    assert any("reviews missing" in item for item in blocked["blockers"])

    allowed = frontier_policy.evaluate_capability(
        "wfp_enforcement",
        operation="prototype",
        consent=True,
        reviews=frontier_policy.DRIVER_REVIEWS,
        lab_mode=True,
    )
    assert allowed["allowed"] is True
    assert allowed["decision"] == "allowed"

    implementation = frontier_policy.evaluate_capability(
        "wfp_enforcement",
        operation="implement",
        consent=True,
        reviews=frontier_policy.DRIVER_REVIEWS,
        lab_mode=True,
    )
    assert implementation["allowed"] is False
    assert "implementation is not approved" in " ".join(implementation["blockers"])


def test_diagnostics_summary_exposes_frontier_policy_counts():
    summary = diagnostics.diagnostics_summary({}, None)

    assert summary["frontier_policy"]["schema_version"] == frontier_policy.SCHEMA_VERSION
    assert summary["frontier_policy"]["capability_count"] >= 14
    assert "policy bypass" in summary["frontier_policy"]["safety_boundary"]


def test_cli_frontier_catalog_and_gate_are_machine_readable(capsys):
    assert nmp_cli.run(["--json", "frontier", "catalog"]) == 0
    catalog = json.loads(capsys.readouterr().out)
    assert catalog["ok"] is True
    assert any(item["id"] == "wfp_enforcement" for item in catalog["capabilities"])

    assert nmp_cli.run(["--json", "frontier", "gate", "--capability", "advanced_anti_censorship", "--operation", "bypass"]) == 2
    blocked = json.loads(capsys.readouterr().out)
    assert blocked["ok"] is False
    assert blocked["decision"] == "blocked_operational_bypass"

    assert (
        nmp_cli.run(
            [
                "--json",
                "frontier",
                "gate",
                "--capability",
                "overlay_orchestration",
                "--operation",
                "diagnose",
                "--i-consent",
            ]
        )
        == 0
    )
    allowed = json.loads(capsys.readouterr().out)
    assert allowed["ok"] is True
    assert allowed["allowed"] is True


def test_consolidated_frontier_backlog_is_single_docs_entry_point():
    backlog = Path("docs/RESEARCH_AND_FRONTIER_BACKLOG.md")
    text = backlog.read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")

    assert backlog.exists()
    for keyword in (
        "ETW",
        "WFP",
        "WinDivert",
        "DoH",
        "DoT",
        "PCAP",
        "Windows Service",
        "Tailscale",
        "ZeroTier",
        "domain-fronting",
        "traffic camouflage",
        "post-quantum",
        "SIEM",
        "OpenTelemetry",
        "WASM",
    ):
        assert keyword in text

    assert "docs/RESEARCH_AND_FRONTIER_BACKLOG.md" in readme
    assert "FRONTIER_FORENSICS" not in readme
    assert "OVERLAY_AND_FRONTIER" not in readme
    for old_doc_stem in (
        "ETW_PER_PROCESS_BANDWIDTH",
        "FRONTIER_FORENSICS_AND_ENFORCEMENT",
        "OVERLAY_AND_FRONTIER",
        "PLUGIN_SIGNING",
        "SIEM_OPENTELEMETRY",
        "TRANSPORT_AND_ROUTE_DIAGNOSTICS",
        "WASM_PLUGIN_RUNTIME",
    ):
        assert not (Path("docs") / f"{old_doc_stem}_RESEARCH.md").exists()
