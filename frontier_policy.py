from __future__ import annotations

import time

import branding


SCHEMA_VERSION = 1

BYPASS_OPERATION_TERMS = {
    "bypass",
    "circumvent",
    "domain_front",
    "domain_fronting",
    "evade",
    "evasion",
    "identity_rotate",
    "policy_bypass",
    "traffic_camouflage",
}

CORE_REVIEWS = ["legal", "ethical", "safety", "feasibility"]
EXTERNAL_REVIEWS = CORE_REVIEWS + ["provider_policy", "abuse_risk"]
DRIVER_REVIEWS = CORE_REVIEWS + ["driver_signing", "rollback", "performance"]

CAPABILITIES = [
    {
        "id": "etw_per_process_bandwidth",
        "name": "ETW Per-Process Bandwidth",
        "brand": "PhantomCore",
        "priority": "P5 Research",
        "maturity": "research",
        "safe_state": "Research and metadata-only planning.",
        "allowed_operations": ["inspect", "plan", "diagnose"],
        "review_required": ["privacy", "performance"],
        "warning": "ETW work must stay metadata-focused until collection scope and retention are approved.",
    },
    {
        "id": "plugin_sandboxing",
        "name": "Plugin Sandboxing",
        "brand": "ForgeHub",
        "priority": "P3 Advanced Architecture",
        "maturity": "implementation",
        "safe_state": "Subprocess and capability isolation may be implemented with explicit permissions.",
        "allowed_operations": ["inspect", "plan", "prototype", "implement"],
        "review_required": ["security"],
        "warning": "Plugin execution must remain permission-gated and auditable.",
    },
    {
        "id": "plugin_marketplace",
        "name": "Plugin Marketplace",
        "brand": "ForgeHub",
        "priority": "P5 Research",
        "maturity": "research",
        "safe_state": "Marketplace plans may be evaluated without installing untrusted code automatically.",
        "allowed_operations": ["inspect", "plan", "prototype"],
        "review_required": ["security", "signing", "abuse_risk"],
        "warning": "Marketplace installation must require signed bundles and clear user approval.",
    },
    {
        "id": "windows_service_architecture",
        "name": "Windows Service Architecture",
        "brand": "AtlasFleet",
        "priority": "P3 Advanced Architecture",
        "maturity": "research",
        "safe_state": "On-demand elevated broker is the first implementation path; persistent service remains deferred.",
        "allowed_operations": ["inspect", "plan", "prototype"],
        "review_required": ["security", "installer", "operations"],
        "warning": "A persistent service must have a narrow command surface, strict IPC ACLs, and audited failure behavior.",
    },
    {
        "id": "doh_dot_controls",
        "name": "DoH And DoT Controls",
        "brand": "OmniRoute",
        "priority": "P5 Research",
        "maturity": "research",
        "safe_state": "Detect and explain encrypted DNS posture before attempting OS-level changes.",
        "allowed_operations": ["inspect", "plan", "diagnose"],
        "review_required": ["os_support", "privacy"],
        "warning": "Encrypted DNS changes must be transparent, reversible, and compatible with local policy.",
    },
    {
        "id": "pcap_export",
        "name": "PCAP Export",
        "brand": "PhantomCore",
        "priority": "P5 Research",
        "maturity": "research",
        "safe_state": "Plan-only in Python; sidecar capture remains disabled until privacy and signing review.",
        "allowed_operations": ["inspect", "plan"],
        "review_required": ["legal", "privacy", "signing"],
        "warning": "Packet captures can expose sensitive content and must remain bounded and explicit.",
    },
    {
        "id": "forensics_sidecar",
        "name": "Forensics Sidecar",
        "brand": "PhantomCore",
        "priority": "P5 Research",
        "maturity": "prototype",
        "safe_state": "Signed JSON stdin/stdout sidecar status checks are allowed; raw capture is disabled.",
        "allowed_operations": ["inspect", "plan", "prototype"],
        "review_required": ["signing", "privacy"],
        "warning": "Sidecars must be signed, bounded, and non-invasive by default.",
    },
    {
        "id": "wfp_enforcement",
        "name": "WFP Enforcement",
        "brand": "PhantomCore",
        "priority": "P6 Frontier",
        "maturity": "frontier",
        "safe_state": "Lab-only design review; no shipping enforcement path.",
        "allowed_operations": ["inspect", "plan", "prototype"],
        "review_required": DRIVER_REVIEWS,
        "warning": "WFP changes can break connectivity and require signed, reversible, auditable design.",
    },
    {
        "id": "windivert_enforcement",
        "name": "WinDivert Enforcement",
        "brand": "PhantomCore",
        "priority": "P6 Frontier",
        "maturity": "frontier",
        "safe_state": "Lab-only design review; no shipping packet interception path.",
        "allowed_operations": ["inspect", "plan", "prototype"],
        "review_required": DRIVER_REVIEWS,
        "warning": "Packet interception requires legal, driver, rollback, and performance review.",
    },
    {
        "id": "per_app_routing",
        "name": "Per-App Routing",
        "brand": "OmniRoute",
        "priority": "P6 Frontier",
        "maturity": "frontier",
        "safe_state": "Start with auditable firewall-style recommendations and rollback plans.",
        "allowed_operations": ["inspect", "plan", "prototype"],
        "review_required": DRIVER_REVIEWS,
        "warning": "Per-app routing must not become hidden policy bypass or unlogged enforcement.",
    },
    {
        "id": "multi_wan_load_balancing",
        "name": "Multi-WAN And Load Balancing",
        "brand": "OmniRoute",
        "priority": "P6 Frontier",
        "maturity": "frontier",
        "safe_state": "Failover recommendations are safe; bonding/load balancing remains research.",
        "allowed_operations": ["inspect", "plan", "diagnose"],
        "review_required": ["feasibility", "rollback", "performance"],
        "warning": "Route changes must be reversible and must not hide the active network path.",
    },
    {
        "id": "ai_anomaly_detection",
        "name": "AI Anomaly Detection",
        "brand": "Synapse",
        "priority": "P5 Research",
        "maturity": "research",
        "safe_state": "Explainable statistical findings are allowed before any model-driven action.",
        "allowed_operations": ["inspect", "plan", "diagnose", "prototype"],
        "review_required": ["privacy", "explainability"],
        "warning": "Self-healing must remain opt-in, evidence-based, and reversible.",
    },
    {
        "id": "overlay_orchestration",
        "name": "Overlay Network Orchestration",
        "brand": "OmniRoute",
        "priority": "P6 Frontier",
        "maturity": "frontier",
        "safe_state": "Read-only Tailscale and ZeroTier status checks are allowed.",
        "allowed_operations": ["inspect", "plan", "diagnose"],
        "review_required": ["vendor_policy", "consent"],
        "warning": "Exit-node, route, and peer mutations require explicit approval and vendor API review.",
    },
    {
        "id": "domain_fronting_research",
        "name": "Domain-Fronting Research",
        "brand": "PhantomCore",
        "priority": "P6 Frontier",
        "maturity": "frontier",
        "safe_state": "Research question only; no operational implementation.",
        "allowed_operations": ["inspect", "plan"],
        "review_required": EXTERNAL_REVIEWS,
        "warning": "Do not provide provider-specific steps, targets, or operational bypass workflows.",
    },
    {
        "id": "traffic_camouflage_research",
        "name": "Traffic Camouflage Research",
        "brand": "PhantomCore",
        "priority": "P6 Frontier",
        "maturity": "frontier",
        "safe_state": "Research question only; no operational implementation.",
        "allowed_operations": ["inspect", "plan"],
        "review_required": EXTERNAL_REVIEWS,
        "warning": "Traffic camouflage cannot ship without external review and abuse-risk controls.",
    },
    {
        "id": "advanced_anti_censorship",
        "name": "Advanced Anti-Censorship Concepts",
        "brand": "PhantomCore",
        "priority": "P6 Frontier",
        "maturity": "frontier",
        "safe_state": "Diagnostics-only research using owned or benign infrastructure.",
        "allowed_operations": ["inspect", "plan", "diagnose"],
        "review_required": EXTERNAL_REVIEWS,
        "warning": "Diagnostics may explain observed restrictions but must not automate circumvention.",
    },
    {
        "id": "post_quantum_plugin_signing",
        "name": "Post-Quantum Plugin Signing",
        "brand": "ForgeHub",
        "priority": "P6 Frontier",
        "maturity": "frontier",
        "safe_state": "Algorithm-agility research only until standards and libraries stabilize.",
        "allowed_operations": ["inspect", "plan", "prototype"],
        "review_required": ["standards", "cryptography", "compatibility"],
        "warning": "Keep classical signing as the enforced production path until post-quantum choices mature.",
    },
    {
        "id": "siem_opentelemetry_export",
        "name": "SIEM And OpenTelemetry Export",
        "brand": "AtlasFleet",
        "priority": "P4 Enterprise",
        "maturity": "research",
        "safe_state": "Windows Event Log is the first export path; direct OTLP and vendor exporters are deferred.",
        "allowed_operations": ["inspect", "plan", "prototype"],
        "review_required": ["privacy", "operations", "credential_storage"],
        "warning": "Remote export must be opt-in or policy-managed and must not leak secrets or raw diagnostics.",
    },
    {
        "id": "transport_route_diagnostics",
        "name": "Transport And Route Diagnostics",
        "brand": "PhantomCore",
        "priority": "P5 Research",
        "maturity": "research",
        "safe_state": "DNS, TLS, SNI, and captive portal diagnostics exist; QUIC, PMTUD, and route anomaly work is deferred.",
        "allowed_operations": ["inspect", "plan", "diagnose", "prototype"],
        "review_required": ["privacy", "traffic_volume", "sidecar"],
        "warning": "Active transport diagnostics must be short, cancellable, low-volume, and evidence-only.",
    },
    {
        "id": "wasm_plugin_runtime",
        "name": "WASM Plugin Runtime",
        "brand": "ForgeHub",
        "priority": "P5 Research",
        "maturity": "research",
        "safe_state": "Deferred until subprocess plugin isolation is mature.",
        "allowed_operations": ["inspect", "plan", "prototype"],
        "review_required": ["security", "packaging", "developer_experience"],
        "warning": "WASM must improve plugin isolation without making packaging or authoring fragile.",
    },
]


def safety_boundary():
    return {
        "schema_version": SCHEMA_VERSION,
        "boundary": branding.SAFETY_BOUNDARY,
        "blocked_operation_terms": sorted(BYPASS_OPERATION_TERMS),
    }


def capability_catalog():
    return [dict(item) for item in CAPABILITIES]


def capability_by_id(capability_id):
    normalized = str(capability_id or "").strip().lower().replace("-", "_")
    for item in CAPABILITIES:
        if item["id"] == normalized:
            return dict(item)
    return None


def evaluate_capability(capability_id, operation="inspect", consent=False, reviews=None, lab_mode=False):
    capability = capability_by_id(capability_id)
    operation = str(operation or "inspect").strip().lower().replace("-", "_")
    reviews = {str(item).strip().lower().replace("-", "_") for item in (reviews or []) if str(item).strip()}
    blockers = []
    decision = "blocked"

    if not capability:
        return _decision(
            capability_id,
            operation,
            decision,
            False,
            ["unknown capability"],
            "Capability is not registered in the Lucid Net frontier catalog.",
            reviews,
            lab_mode,
        )

    if operation in BYPASS_OPERATION_TERMS:
        return _decision(
            capability["id"],
            operation,
            "blocked_operational_bypass",
            False,
            ["operational bypass/evasion is not implemented"],
            capability["warning"],
            reviews,
            lab_mode,
            capability,
        )

    if operation not in capability["allowed_operations"]:
        blockers.append("operation is outside the approved safe scope")
    if operation in ("diagnose", "prototype", "implement") and not consent:
        blockers.append("explicit user consent")
    if operation in ("prototype", "implement") and capability["maturity"] in ("research", "frontier") and not lab_mode:
        blockers.append("lab mode")
    missing_reviews = [item for item in capability["review_required"] if item not in reviews]
    if operation in ("prototype", "implement") and missing_reviews:
        blockers.append("reviews missing: " + ", ".join(missing_reviews))
    if operation == "implement" and capability["maturity"] in ("research", "frontier"):
        blockers.append("implementation is not approved for research/frontier capability")

    if blockers:
        decision = "research_only" if capability["maturity"] in ("research", "frontier") else "review_required"
        allowed = False
    else:
        decision = "allowed"
        allowed = True

    return _decision(capability["id"], operation, decision, allowed, blockers, capability["warning"], reviews, lab_mode, capability)


def frontier_status_summary():
    catalog = capability_catalog()
    blocked = [
        evaluate_capability(item["id"], "prototype" if item["maturity"] in ("research", "frontier") else "inspect")
        for item in catalog
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": time.time(),
        "safety_boundary": branding.SAFETY_BOUNDARY,
        "capability_count": len(catalog),
        "research_or_frontier_count": sum(1 for item in catalog if item["maturity"] in ("research", "frontier")),
        "implementation_count": sum(1 for item in catalog if item["maturity"] == "implementation"),
        "blocked_or_review_gated_count": sum(1 for item in blocked if not item["allowed"]),
        "capabilities": catalog,
    }


def _decision(capability_id, operation, decision, allowed, blockers, warning, reviews, lab_mode, capability=None):
    return {
        "schema_version": SCHEMA_VERSION,
        "capability_id": str(capability_id or ""),
        "capability": capability or {},
        "operation": operation,
        "allowed": bool(allowed),
        "decision": decision,
        "blockers": list(blockers),
        "reviews_present": sorted(reviews),
        "lab_mode": bool(lab_mode),
        "warning": warning,
        "safety_boundary": branding.SAFETY_BOUNDARY,
    }
