from __future__ import annotations

PRODUCT_NAME = "Lucid Net"
PRODUCT_VERSION = "1.0.0"
TECHNICAL_APP_ID = "LucidNet"
WINDOWS_EVENT_SOURCE = TECHNICAL_APP_ID
HOSTS_MARKER_PREFIX = TECHNICAL_APP_ID
INSTALLER_BASENAME = TECHNICAL_APP_ID
INSTALLER_APP_ID = "B8E4C9A1-6F2D-4E1B-9C0A-7D3E5F1A2B6C"
POLICY_REGISTRY_ROOT = rf"SOFTWARE\Policies\{TECHNICAL_APP_ID}"
BROKER_PIPE_NAME = rf"\\.\pipe\{TECHNICAL_APP_ID}.Broker"
PRODUCT_TAGLINE = "Safe Windows network control, diagnostics, and automation."
PRODUCT_PROMISE = (
    "A local-first Windows network operations console for DNS, proxy, DDNS, diagnostics, history, "
    "trusted plugins, and carefully gated automation."
)

SAFETY_BOUNDARY = (
    "Lucid Net may diagnose network behavior and recommend lawful, user-consented local "
    "configuration changes. Features involving policy bypass, traffic camouflage, identity rotation, "
    "or anti-censorship countermeasures require legal, ethical, safety, and feasibility review before "
    "implementation."
)

PRODUCT_PILLARS = [
    {
        "id": "local_control",
        "name": "Local Control",
        "summary": "Manage DNS, proxy, DDNS, diagnostics, and restore points from one Windows control plane.",
    },
    {
        "id": "trust_and_recovery",
        "name": "Trust And Recovery",
        "summary": "Prefer validated inputs, redacted logs, rollback, diagnostics export, and explicit consent.",
    },
    {
        "id": "operator_workflow",
        "name": "Operator Workflow",
        "summary": "Keep GUI, tray, and CLI surfaces aligned for daily users, power users, and administrators.",
    },
    {
        "id": "observability",
        "name": "Local Observability",
        "summary": "Explain effective settings, traffic snapshots, history, captive portal state, and anomalies.",
    },
    {
        "id": "gated_ambition",
        "name": "Gated Ambition",
        "summary": "Preserve enterprise, plugin, forensics, and frontier networking ideas behind maturity gates.",
    },
]

BRAND_ARCHITECTURE = [
    {
        "name": "Lucid Net",
        "role": "Active product name",
        "status": "active",
        "usage": "Use for the application, installer, CLI, docs, support, diagnostics, and release artifacts.",
    },
    {
        "name": "OmniRoute",
        "role": "Routing and profile automation panel family",
        "status": "panel",
        "usage": "Use for DNS, proxy, context-aware profiles, overlay status, and future route orchestration.",
    },
    {
        "name": "Synapse",
        "role": "Adaptive recommendations and self-healing panel family",
        "status": "panel",
        "usage": "Use only for explainable anomaly detection, recommendations, and opt-in self-healing.",
    },
    {
        "name": "ForgeHub",
        "role": "Plugin platform and marketplace panel family",
        "status": "panel",
        "usage": "Use for trusted plugins, signed bundles, per-plugin environments, and marketplace governance.",
    },
    {
        "name": "AtlasFleet",
        "role": "Enterprise deployment and fleet policy panel family",
        "status": "panel",
        "usage": "Use for HKLM policy, GPO, Intune, SIEM, Event Log, signing, and fleet-readiness material.",
    },
    {
        "name": "PulseGuard",
        "role": "Recovery, rollback, and power-efficiency panel family",
        "status": "panel",
        "usage": "Use for rollback, metered-network behavior, battery-aware background policy, and reliability health.",
    },
    {
        "name": "PhantomCore",
        "role": "Frontier forensics and restriction diagnostics panel family",
        "status": "restricted",
        "usage": "Do not use in user-facing product flows unless legal, ethical, safety, and feasibility review approves it.",
    },
]

PANEL_BRANDING = [
    {
        "panel": "Application shell, installer, CLI, docs, diagnostics bundles, support",
        "brand": "Lucid Net",
        "status": "active",
        "rule": "Use everywhere for the shipped product.",
    },
    {
        "panel": "DNS, proxy, context profiles, overlay status, routing research",
        "brand": "OmniRoute",
        "status": "panel",
        "rule": "Use for routing, profile matching, and network path automation.",
    },
    {
        "panel": "Insights, anomaly detection, recommendations, opt-in self-healing",
        "brand": "Synapse",
        "status": "panel",
        "rule": "Reserved for explainable automation only; never imply autonomous hidden changes.",
    },
    {
        "panel": "Plugins, signed bundles, plugin marketplace, capability permissions",
        "brand": "ForgeHub",
        "status": "panel",
        "rule": "Use for the trusted extension platform and marketplace governance.",
    },
    {
        "panel": "Enterprise policy, GPO, Intune, Event Log, SIEM, signing",
        "brand": "AtlasFleet",
        "status": "panel",
        "rule": "Use for managed deployment, audit, release trust, and fleet operations.",
    },
    {
        "panel": "Rollback, restore points, metered mode, battery-aware background work",
        "brand": "PulseGuard",
        "status": "panel",
        "rule": "Use for reliability, recovery, and efficiency controls.",
    },
    {
        "panel": "Deep diagnostics, packet forensics, restriction diagnostics, enforcement research",
        "brand": "PhantomCore",
        "status": "restricted",
        "rule": "Research-only label requiring legal, ethical, safety, and feasibility review before user-facing use.",
    },
]


def product_identity():
    return {
        "name": PRODUCT_NAME,
        "version": PRODUCT_VERSION,
        "technical_app_id": TECHNICAL_APP_ID,
        "event_source": WINDOWS_EVENT_SOURCE,
        "installer_basename": INSTALLER_BASENAME,
        "installer_app_id": INSTALLER_APP_ID,
        "policy_registry_root": POLICY_REGISTRY_ROOT,
        "broker_pipe_name": BROKER_PIPE_NAME,
        "tagline": PRODUCT_TAGLINE,
        "promise": PRODUCT_PROMISE,
    }


def product_vision():
    return {
        "near_term": [
            "Safe local management for DNS, proxy, DDNS, diagnostics, traffic snapshots, history, and trusted plugins.",
            "Daily workflow polish through tray actions, persistent UI state, sortable views, clearer errors, and rollback.",
            "Reliable engineering foundations with tests, SQLite history, structured logs, and crash-safe migrations.",
        ],
        "mid_term": [
            "Standard-user GUI backed by a narrow elevated broker or Windows Service.",
            "Context-aware profiles using SSID, BSSID, captive portal state, metered status, and connectivity recovery.",
            "Local observability through history, latency, traffic trends, diagnostics bundles, and ETW research.",
        ],
        "long_term": [
            "Enterprise readiness through policy overrides, signed updates, event logs, SIEM/OpenTelemetry research, and silent deployment.",
            "A safer plugin platform with subprocess isolation, signed bundles, per-plugin environments, and marketplace governance.",
            "Consent-based diagnostics and forensics for DNS, TLS, routing, throttling, proxy, and OS-level network behavior.",
        ],
    }


def brand_architecture():
    return [dict(item) for item in BRAND_ARCHITECTURE]


def panel_branding():
    return [dict(item) for item in PANEL_BRANDING]


def product_pillars():
    return [dict(item) for item in PRODUCT_PILLARS]


def about_payload():
    return {
        "identity": product_identity(),
        "pillars": product_pillars(),
        "vision": product_vision(),
        "brand_architecture": brand_architecture(),
        "panel_branding": panel_branding(),
        "safety_boundary": SAFETY_BOUNDARY,
    }
