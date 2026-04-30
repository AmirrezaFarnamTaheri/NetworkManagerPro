# Product Vision And Branding

Status: implementation source for product identity, brand architecture, and user-facing positioning.

## Product Identity

Lucid Net remains the active product name for the app, installer, CLI, documentation, diagnostics bundles, release artifacts, and support material.

Tagline:

```text
Safe Windows network control, diagnostics, and automation.
```

Promise:

```text
A local-first Windows network operations console for DNS, proxy, DDNS, diagnostics, history, trusted plugins, and carefully gated automation.
```

## Product Vision

Near term:

- Safe local management for DNS, proxy, DDNS, diagnostics, traffic snapshots, history, and trusted plugins.
- Daily workflow polish through tray actions, persistent UI state, sortable views, clearer errors, and rollback.
- Reliable engineering foundations with tests, SQLite history, structured logs, and crash-safe migrations.

Mid term:

- Standard-user GUI backed by a narrow elevated broker or Windows Service.
- Context-aware profiles using SSID, BSSID, captive portal state, metered status, and connectivity recovery.
- Local observability through history, latency, traffic trends, diagnostics bundles, and ETW research.

Long term:

- Enterprise readiness through policy overrides, signed updates, event logs, SIEM/OpenTelemetry research, and silent deployment.
- A safer plugin platform with subprocess isolation, signed bundles, per-plugin environments, and marketplace governance.
- Consent-based diagnostics and forensics for DNS, TLS, routing, throttling, proxy, and OS-level network behavior.

## Product Pillars

- Local Control: Manage DNS, proxy, DDNS, diagnostics, and restore points from one Windows control plane.
- Trust And Recovery: Prefer validated inputs, redacted logs, rollback, diagnostics export, and explicit consent.
- Operator Workflow: Keep GUI, tray, and CLI surfaces aligned for daily users, power users, and administrators.
- Local Observability: Explain effective settings, traffic snapshots, history, captive portal state, and anomalies.
- Gated Ambition: Preserve enterprise, plugin, forensics, and frontier networking ideas behind maturity gates.

## Brand Architecture

| Name | Role | Status | Usage |
|---|---|---|---|
| Lucid Net | Active product name | Active | Use for the application, installer, CLI, docs, support, diagnostics, and release artifacts. |
| OmniRoute | Routing and profile automation panel family | Panel | Use for DNS, proxy, context-aware profiles, overlay status, and future route orchestration. |
| Synapse | Adaptive recommendations and self-healing panel family | Panel | Use only for explainable anomaly detection, recommendations, and opt-in self-healing. |
| ForgeHub | Plugin platform and marketplace panel family | Panel | Use for trusted plugins, signed bundles, per-plugin environments, and marketplace governance. |
| AtlasFleet | Enterprise deployment and fleet policy panel family | Panel | Use for HKLM policy, GPO, Intune, SIEM, Event Log, signing, and fleet-readiness material. |
| PulseGuard | Recovery, rollback, and power-efficiency panel family | Panel | Use for rollback, metered-network behavior, battery-aware background policy, and reliability health. |
| PhantomCore | Frontier forensics and restriction diagnostics panel family | Restricted | Do not use in user-facing product flows unless legal, ethical, safety, and feasibility review approves it. |

## Panel Branding Map

These labels are reserved capability names, not current replacement tab names. Core tabs such as Dashboard, Status, History, Traffic, and Diagnostics should stay practical and plainly named.

| Surface | Brand | Status | Rule |
|---|---|---|---|
| Application shell, installer, CLI, docs, diagnostics bundles, support | Lucid Net | Active | Use everywhere for the shipped product. |
| DNS, proxy, context profiles, overlay status, routing research | OmniRoute | Panel | Use for routing, profile matching, and network path automation. |
| Insights, anomaly detection, recommendations, opt-in self-healing | Synapse | Panel | Use only for explainable automation; never imply autonomous hidden changes. |
| Plugins, signed bundles, plugin marketplace, capability permissions | ForgeHub | Panel | Use for the trusted extension platform and marketplace governance. |
| Enterprise policy, GPO, Intune, Event Log, SIEM, signing | AtlasFleet | Panel | Use for managed deployment, audit, release trust, and fleet operations. |
| Rollback, restore points, metered mode, battery-aware background work | PulseGuard | Panel | Use for reliability, recovery, and efficiency controls. |
| Deep diagnostics, packet forensics, restriction diagnostics, enforcement research | PhantomCore | Restricted | Research-only until legal, ethical, safety, and feasibility review approves user-facing use. |

## Safety Boundary

Lucid Net may diagnose network behavior and recommend lawful, user-consented local configuration changes. Features involving policy bypass, traffic camouflage, identity rotation, or anti-censorship countermeasures require legal, ethical, safety, and feasibility review before implementation.

## Implementation Contract

- `branding.py` is the executable source of truth for product name, version, tagline, promise, product pillars, vision, brand architecture, panel branding, and safety boundary.
- `core.APP_DISPLAY_NAME`, `core.APP_VERSION`, `core.APP_NAME`, Event Log source, hosts-file markers, and release basename values derive from `branding.py`.
- The GUI About tab displays the product identity, pillars, brand architecture, and safety boundary.
- The CLI exposes `about`, `vision`, and `brand` commands with optional JSON output, including the panel branding map.
- Docs should use Lucid Net as the active product name until a future brand decision record explicitly changes it.
