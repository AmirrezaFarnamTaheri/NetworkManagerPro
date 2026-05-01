# Research And Frontier Backlog

Status: single source of truth for research/frontier capabilities that are not fully shipped in Lucid Net.

Owner surface: `frontier_policy.py`, CLI `frontier` commands, diagnostics export `frontier_policy`, GUI Tools action `Review frontier gates`, and this document.

## Boundary

Lucid Net may diagnose network behavior and recommend lawful, user-consented local configuration changes. Features involving policy bypass, traffic camouflage, identity rotation, or anti-censorship countermeasures require legal, ethical, safety, and feasibility review before implementation.

This backlog preserves ambitious ideas without turning them into operational bypass or evasion tooling. The app does not implement hidden policy circumvention, provider-specific evasion steps, target lists, traffic camouflage recipes, or automatic identity-rotation workflows.

## What Is Implemented Now

- `frontier_policy.py` registers a capability catalog for research and frontier work.
- CLI commands expose the catalog and gate decisions:
  - `python nmp_cli.py frontier catalog --json`
  - `python nmp_cli.py frontier status --json`
  - `python nmp_cli.py frontier gate --capability wfp_enforcement --operation prototype --i-consent --lab-mode --review legal --review ethical --review safety --review feasibility --review driver_signing --review rollback --review performance --json`
- Diagnostics exports include frontier-policy counts and the safety boundary.
- GUI Tools includes `Review frontier gates`, which records a local event with the catalog summary.
- PCAP is plan-only in Python, bounded, explicit, and payload capture is disabled.
- The Rust forensics sidecar scaffold supports status/version checks and intentionally rejects packet capture until review.
- Overlay support is read-only status inspection for Tailscale and ZeroTier.
- AI/anomaly work is explainable statistical detection over local aggregate metrics.
- Plugin platform work includes subprocess host scaffolding, bundle digest checks, marketplace readiness planning, and signature metadata research.

## Capability Matrix

| Capability ID | Product Family | Current State | Remaining Frontier Work | Gate |
|---|---|---|---|---|
| `etw_per_process_bandwidth` | PhantomCore | Not implemented beyond research plan. | Build a read-only ETW sidecar or broker-owned collector for process/PID/endpoint byte metadata. | Privacy and performance review. |
| `plugin_sandboxing` | ForgeHub | Subprocess host scaffolding exists. | Move PluginAPI calls through IPC, isolate plugin lifetimes, restart with backoff, and route UI contributions safely. | Security review. |
| `plugin_marketplace` | ForgeHub | Registry parser and install-plan readiness exist. | Signed bundle installation, trust roots, revocation, and safe update UX. | Security, signing, abuse-risk review. |
| `windows_service_architecture` | AtlasFleet | On-demand elevated broker contract exists. | Persistent Windows Service architecture, installer lifecycle, recovery, and service ACLs. | Security, installer, operations review. |
| `doh_dot_controls` | OmniRoute | DoH helper exists for diagnostics. | Detect OS encrypted DNS posture and design reversible DoH/DoT configuration controls. | OS-support and privacy review. |
| `pcap_export` | PhantomCore | Plan-only request and manifest validation exist. | Implement signed sidecar capture for metadata-safe use cases, if approved. | Legal, privacy, signing review. |
| `forensics_sidecar` | PhantomCore | Rust scaffold supports status/version and rejects capture. | Add capability discovery, signed release verification, and approved bounded diagnostics. | Signing and privacy review. |
| `wfp_enforcement` | PhantomCore | Research gate only. | Lab prototype for reversible, auditable filtering if approved. | Legal, ethical, safety, feasibility, driver-signing, rollback, performance review. |
| `windivert_enforcement` | PhantomCore | Research gate only. | Lab prototype only; no shipping packet interception path. | Legal, ethical, safety, feasibility, driver-signing, rollback, performance review. |
| `per_app_routing` | OmniRoute | Planning only. | Start with auditable firewall-style recommendations before route mutation. | Driver-signing, rollback, and policy review. |
| `multi_wan_load_balancing` | OmniRoute | Adapter inventory and failover recommendation exist. | True bonding/load balancing research with reversible route policies. | Feasibility, rollback, performance review. |
| `ai_anomaly_detection` | Synapse | Statistical spike detection exists. | Model-backed local anomaly detection and opt-in self-healing recommendations. | Privacy and explainability review. |
| `overlay_orchestration` | OmniRoute | Read-only status inspection exists. | User-approved exit-node, route, or peer orchestration through vendor-stable APIs. | Vendor-policy and consent review. |
| `domain_fronting_research` | PhantomCore | Not implemented. | Research questions only; no operational product implementation. | Legal, ethical, safety, feasibility, provider-policy, abuse-risk review. |
| `traffic_camouflage_research` | PhantomCore | Not implemented. | Research questions only; no operational product implementation. | Legal, ethical, safety, feasibility, provider-policy, abuse-risk review. |
| `advanced_anti_censorship` | PhantomCore | Consent-based diagnostics only. | Owned-infrastructure diagnostic research that explains observations without evasion. | Legal, ethical, safety, feasibility, provider-policy, abuse-risk review. |
| `post_quantum_plugin_signing` | ForgeHub | Algorithm-agility metadata exists. | Track standards and libraries; keep production signing classical until mature. | Standards, cryptography, compatibility review. |
| `siem_opentelemetry_export` | AtlasFleet | Windows Event Log export path exists. | OTLP/vendor exporters after local event schema stabilizes. | Enterprise privacy and operations review. |
| `transport_route_diagnostics` | PhantomCore | DNS, TLS, SNI, captive portal diagnostics exist. | QUIC/UDP degradation, PMTUD, and route anomaly diagnostics with bounded tests. | Privacy, traffic-volume, and sidecar review. |
| `wasm_plugin_runtime` | ForgeHub | Not implemented. | WASI host experiments for small untrusted plugins after subprocess isolation matures. | Security, packaging, developer-experience review. |

## Item Details

### F-001: ETW Per-Process Bandwidth

Priority: P5 Research  
Family: PhantomCore  
Current state: The Traffic tab uses `psutil` connection inventory and aggregate counters. It cannot truthfully attribute byte totals to processes.  
Not implemented: A live ETW collector, provider binding, retention policy, and UI grid for per-process bandwidth.  
Why held: ETW can expose sensitive process and endpoint metadata; provider stability and required privileges must be proven on Windows 10/11.  
Safe implementation path:
- Build a read-only sidecar or broker-owned collector.
- Evaluate `Microsoft-Windows-Kernel-Network`, `Microsoft-Windows-TCPIP`, and `Microsoft-Windows-Winsock-AFD`.
- Export only process name, PID, endpoint, direction, bytes, timestamp, and provider metadata.
- Avoid payloads, URLs, request contents, and long-term sensitive retention.
Acceptance criteria:
- Controlled traffic from a known process is attributed within an acceptable tolerance.
- Ten-minute capture stays within documented CPU/memory limits.
- Diagnostics export redacts or summarizes sensitive endpoint metadata.
Tests:
- Provider parsing fixture tests.
- Controlled local transfer comparison.
- Retention and redaction tests.
Risk: Medium.

### F-002: WFP Enforcement

Priority: P6 Frontier  
Family: PhantomCore  
Current state: Research gate only through `frontier_policy.evaluate_capability("wfp_enforcement", ...)`.  
Not implemented: WFP filter installation, callout drivers, persistent enforcement, kill switch, or per-app blocking.  
Why held: Misconfigured WFP rules can break connectivity, require careful signing/installer design, and can become hidden enforcement if not auditable.  
Safe implementation path:
- First prototype in lab mode only.
- Prefer Windows Firewall and documented user-mode APIs before callout drivers.
- Require rollback design before any mutation.
- Record all rule proposals and results in local history.
Acceptance criteria:
- Prototype rules are reversible after process crash or power loss.
- User can see process identity, rule scope, and rollback state.
- No hidden enforcement path exists.
Tests:
- Rule serialization tests.
- Rollback-on-failure tests.
- Permission and audit-history tests.
Risk: High.

### F-003: WinDivert Enforcement

Priority: P6 Frontier  
Family: PhantomCore  
Current state: Research gate only.  
Not implemented: Packet interception, packet rewrite, traffic shaping, packet injection, or capture driver integration.  
Why held: Packet interception is high-risk, driver-dependent, and can create evasion capabilities if implemented without strict scope.  
Safe implementation path:
- Keep WinDivert as lab-only feasibility research.
- Prefer read-only diagnostics and ETW before packet interception.
- Require signed driver, rollback, cancellation, performance limits, and legal review before prototype.
Acceptance criteria:
- Lab prototype cannot run outside explicit lab mode.
- Prototype exits cleanly and restores network behavior.
- No packet rewrite or evasion workflow is exposed.
Tests:
- Gate tests for missing reviews.
- Lab-mode command validation tests.
- Driver absence and rollback tests.
Risk: High.

### F-004: Per-App Routing

Priority: P6 Frontier  
Family: OmniRoute  
Current state: Planning only; no per-process route mutation exists.  
Not implemented: Per-app route tables, app-specific tunnel selection, or process-bound enforcement.  
Why held: Windows routing is interface/route oriented, while per-app routing usually requires firewall, WFP, VPN, or driver support.  
Safe implementation path:
- Start with process identity display and recommendations.
- Add reversible firewall-style controls before route mutation.
- Require clear user confirmation and event history for every change.
Acceptance criteria:
- Users can see what would change before applying it.
- Rollback succeeds even after failed connectivity checks.
- CLI and GUI show the same plan.
Tests:
- Plan rendering tests.
- Process identity normalization tests.
- Rollback and audit tests.
Risk: High.

### F-005: Multi-WAN And Load Balancing

Priority: P6 Frontier  
Family: OmniRoute  
Current state: Adapter inventory and failover recommendation exist.  
Not implemented: True bonding, load balancing, route rewriting, or health-based active failover.  
Why held: True link aggregation usually needs network-side support, VPN overlay, drivers, or specialized routing.  
Safe implementation path:
- Keep current read-only adapter inventory.
- Add health scoring and failover recommendation first.
- Prototype reversible route metric changes only after rollback tests.
Acceptance criteria:
- App distinguishes failover, route preference, and bonding.
- No route change happens without preview and restore point.
- Metrics survive adapter down/up cycles.
Tests:
- Adapter inventory fixture tests.
- Recommendation ordering tests.
- Route-plan rollback tests.
Risk: Medium.

### F-006: DoH And DoT Controls

Priority: P5 Research  
Family: OmniRoute  
Current state: DoH JSON resolver helper exists for DNS integrity diagnostics.  
Not implemented: Windows DoH profile management, DoT support, policy detection, and UI controls.  
Why held: Encrypted DNS behavior depends on Windows build, network policy, browser behavior, and enterprise controls.  
Safe implementation path:
- Detect current OS encrypted-DNS capability and policy state.
- Explain browser-vs-OS resolver differences.
- Provide reversible profile plans before mutation.
Acceptance criteria:
- Diagnostics distinguish system DNS, browser DoH, and app-level DoH checks.
- Enterprise policy conflicts are explained.
- Restore returns the previous resolver behavior.
Tests:
- Policy-detection fixture tests.
- DoH result-classification tests.
- Restore-plan tests.
Risk: Medium.

### F-006A: Windows Service Architecture

Priority: P3 Advanced Architecture  
Family: AtlasFleet  
Current state: The accepted architecture uses an on-demand elevated broker first. `broker_contract.py` and `broker_runtime.py` define the initial command and IPC policy shape.  
Not implemented: Persistent Windows Service installation, service lifecycle management, recovery policy, service-hosted telemetry, and service-owned privileged workers.  
Why held: A persistent service increases installer complexity, attack surface, update complexity, and operational responsibility.  
Safe implementation path:
- Keep the GUI standard-user capable.
- Keep the broker command surface narrow and auditable.
- Add a service only when enterprise policy, fleet telemetry, or persistent background work requires it.
- Require service ACL review and installer rollback before shipping.
Acceptance criteria:
- Service can be installed, upgraded, stopped, and removed cleanly.
- Unauthorized callers cannot reach privileged commands.
- Service logs sanitized results to Windows Event Log.
- App remains usable when the service is unavailable.
Tests:
- Service command contract tests.
- Installer lifecycle tests.
- IPC authorization tests.
- Failure and recovery tests.
Risk: High.

### F-007: PCAP Export

Priority: P5 Research  
Family: PhantomCore  
Current state: `pcap_capture_plan`, `pcap_export_request`, and manifest validation exist; payload capture is disabled.  
Not implemented: Live packet capture, capture file writing, payload capture, or automatic upload.  
Why held: PCAP can expose credentials, cookies, hostnames, IPs, internal services, and user activity.  
Safe implementation path:
- Keep Python as planner and UI.
- Move capture into a signed sidecar.
- Require explicit start, visible duration, cancellation, and local-only output.
- Keep payload capture disabled unless separately approved.
Acceptance criteria:
- Capture cannot start without warning acknowledgement.
- Duration and output folder are visible before start.
- Manifest records scope, outputs, and redaction warning.
Tests:
- Duration bounds.
- Payload disabled validation.
- Manifest and sidecar-result validation.
Risk: High.

### F-008: Forensics Sidecar Expansion

Priority: P5 Research  
Family: PhantomCore  
Current state: Rust scaffold accepts JSON requests and supports `status`/`version`; `pcap_export` is intentionally disabled.  
Not implemented: Capture engine, TLS parser, route probes, signed binary verification, or installer integration.  
Why held: Native sidecars expand supply-chain, signing, crash, and privacy risk.  
Safe implementation path:
- Add capability discovery first.
- Add signature verification and version pinning.
- Add metadata-only diagnostics before raw capture.
Acceptance criteria:
- Sidecar output validates against schema.
- Unsupported commands fail closed.
- Packaged build includes expected signed sidecar metadata.
Tests:
- Rust unit tests.
- Python sidecar contract tests.
- Packaging smoke tests.
Risk: Medium.

### F-009: AI Anomaly Detection And Self-Healing

Priority: P5 Research  
Family: Synapse  
Current state: Statistical spike detection over persisted aggregate metrics exists.  
Not implemented: Model training, model inference, automatic remediation, or policy learning.  
Why held: Network self-healing can make wrong changes unless findings are explainable, reversible, and user-approved.  
Safe implementation path:
- Expand explainable rules before ML.
- Add confidence, evidence, and recommendation fields to every finding.
- Keep remediation opt-in with restore points.
Acceptance criteria:
- Every finding includes evidence and confidence.
- User can decline every suggested remediation.
- No background mutation happens from model output alone.
Tests:
- Baseline/spike fixture tests.
- False-positive scenario tests.
- Remediation-plan rollback tests.
Risk: Medium.

### F-010: Overlay Orchestration

Priority: P6 Frontier  
Family: OmniRoute  
Current state: Read-only Tailscale and ZeroTier detection/status exists.  
Not implemented: Exit-node selection, route advertisement, peer changes, or tunnel policy changes.  
Why held: Overlay clients have vendor-specific APIs and can alter trust boundaries, routes, and identity.  
Safe implementation path:
- Keep read-only status as default.
- Add vendor CLI/API version checks.
- Require explicit consent and clear preview for any future mutation.
Acceptance criteria:
- Status reads do not change overlay state.
- Mutating plans identify exact vendor command/API and rollback.
- CLI and GUI show the same state.
Tests:
- Tool detection tests.
- Unsupported tool tests.
- Operation-gate tests.
Risk: Medium.

### F-011: Plugin Marketplace And Signed Bundles

Priority: P5 Research  
Family: ForgeHub  
Current state: Registry parsing, marketplace readiness plans, bundle manifests, and signature metadata exist.  
Not implemented: Production marketplace, publisher trust store, revocation, automatic updates, and signed install UX.  
Why held: A marketplace can become a supply-chain risk without signature enforcement and clear trust roots.  
Safe implementation path:
- Require signed bundles before install.
- Pin first-party publisher identities.
- Add enterprise publisher policy.
- Reject unsigned, tampered, revoked, expired, or unknown bundles by default.
Acceptance criteria:
- Tampered bundle is rejected before extraction.
- Unknown publisher is blocked.
- UI explains signature and publisher status.
Tests:
- Bundle digest tests.
- Signature metadata tests.
- Trust store and revocation tests.
Risk: High.

### F-012: WASM Plugin Runtime

Priority: P5 Research  
Family: ForgeHub  
Current state: Not implemented.  
Not implemented: WASM runtime, WASI host functions, plugin packaging, or PyInstaller integration.  
Why held: Subprocess Python isolation better fits the current plugin model and UI integration.  
Safe implementation path:
- Finish subprocess isolation first.
- Evaluate WASM only for small non-UI policy or diagnostics plugins.
- Deny filesystem and network access by default.
Acceptance criteria:
- Signed or digest-verified WASM module loads.
- Host exposes only minimal sanitized event function.
- Packaging does not introduce fragile native dependencies.
Tests:
- WASI permission tests.
- Startup/memory benchmark.
- Packaged smoke test.
Risk: Medium.

### F-013: SIEM And OpenTelemetry Export

Priority: P4 Enterprise  
Family: AtlasFleet  
Current state: Windows Event Log export exists; Windows Event Forwarding is the recommended first fleet path.  
Not implemented: Direct OTLP exporter, vendor-specific SIEM senders, batching, retry, and credential storage.  
Why held: Direct remote export needs privacy, authentication, and operational ownership decisions.  
Safe implementation path:
- Stabilize local event schema first.
- Use Event Log and WEF for managed fleets.
- Add OTLP only after endpoint/auth/redaction policy is defined.
Acceptance criteria:
- Event schema is stable and redacted.
- Direct export can be disabled by policy.
- Export failures do not block local app use.
Tests:
- Event schema tests.
- Redaction tests.
- Retry and backoff tests.
Risk: Medium.

### F-014: Transport And Route Diagnostics

Priority: P5 Research  
Family: PhantomCore  
Current state: Captive portal, DNS integrity, transparent DNS proxy, TLS inspection, and SNI failure diagnostics exist.  
Not implemented: QUIC/UDP degradation, PMTUD blackhole, traceroute correlation, public looking-glass comparison, or BGP anomaly scoring.  
Why held: Active network tests can generate traffic, reveal sensitive endpoints, and produce misleading attribution if overclaimed.  
Safe implementation path:
- Use user-approved benign endpoints.
- Keep tests short, cancellable, and low-volume.
- Move raw-socket or packet-option tests into the sidecar.
Acceptance criteria:
- Findings separate evidence, confidence, and recommendation.
- Tests do not embed restricted target lists.
- No attribution claim is made without corroboration.
Tests:
- Classifier fixture tests.
- Timeout and cancellation tests.
- Redaction tests.
Risk: Medium.

### F-015: Domain-Fronting Research

Priority: P6 Frontier  
Family: PhantomCore  
Current state: Not implemented.  
Not implemented: Domain-fronting configuration, target/provider lists, transport recipes, or bypass workflows.  
Why held: Operational domain-fronting can violate provider policies and enable policy circumvention.  
Allowed research questions:
- What can be detected safely?
- What can be explained to users?
- What requires provider-policy or legal review?
Acceptance criteria:
- Research remains non-operational.
- No target lists or provider-specific bypass instructions appear in product docs.
- Any future work stays behind `frontier_policy`.
Tests:
- Documentation scan for disallowed operational language.
- Gate tests for blocked bypass operations.
Risk: High.

### F-016: Traffic Camouflage Research

Priority: P6 Frontier  
Family: PhantomCore  
Current state: Not implemented.  
Not implemented: Protocol shaping, traffic mimicry, evasion templates, or automatic countermeasures.  
Why held: Camouflage can be used to evade network policy and detection systems.  
Allowed research questions:
- Which restrictions can be diagnosed without circumvention?
- Which metadata can be explained safely?
- Which ideas require external review and should remain out of product scope?
Acceptance criteria:
- Product remains diagnostics-only in this area.
- No operational camouflage workflows are implemented.
- Any future proposal includes abuse-risk review.
Tests:
- Gate tests for `traffic_camouflage` operations.
- Documentation safety scans.
Risk: High.

### F-017: Advanced Anti-Censorship Concepts

Priority: P6 Frontier  
Family: PhantomCore  
Current state: Consent-based diagnostics exist for DNS, transparent DNS proxy, TLS/SNI evidence, and captive portal state.  
Not implemented: Circumvention, evasion, identity rotation, destination recommendations, or automatic countermeasures.  
Why held: Diagnostics can help users understand their network; operational evasion can cross legal, policy, and safety boundaries.  
Safe implementation path:
- Keep work diagnostics-only.
- Use owned, benign, or user-approved infrastructure.
- Explain observations without telling users how to bypass restrictions.
Acceptance criteria:
- Every active test requires consent.
- Evidence and recommendation are separate.
- No bypass instructions or target lists ship in docs, GUI, or CLI.
Tests:
- Consent-gate tests.
- Classifier tests.
- Documentation safety scans.
Risk: High.

### F-018: Post-Quantum Plugin Signing

Priority: P6 Frontier  
Family: ForgeHub  
Current state: Algorithm-agility metadata exists; post-quantum algorithms are research-only.  
Not implemented: Runtime post-quantum verification, key management, bundle format, or production dependency.  
Why held: Standards, libraries, ecosystem support, and package size are still moving.  
Safe implementation path:
- Keep Ed25519/ECDSA as near-term production candidates.
- Track ML-DSA and SLH-DSA as research-only.
- Avoid adding immature crypto dependencies for future-proofing alone.
Acceptance criteria:
- Signature metadata remains algorithm-agile.
- Research algorithms do not pass production verification by default.
- Migration path is documented before runtime dependency is added.
Tests:
- Metadata validation tests.
- Research-allowed flag tests.
- Compatibility tests.
Risk: Medium.

## Required Governance Before Any Frontier Prototype

Every prototype for a `P5 Research` or `P6 Frontier` capability must provide:

- Problem statement and user value.
- Explicit non-goals.
- Legal, ethical, safety, feasibility, and privacy review where applicable.
- Threat model and abuse-risk analysis.
- User-visible consent flow.
- Rollback plan for any mutation.
- Redaction and retention policy.
- CLI and GUI parity plan.
- Tests for validation, failure behavior, and cleanup.
- Documentation update in this file and roadmap status update in `Audit and plan.md`.

## Disallowed Product Workflows

The following are not implemented as Lucid Net product capabilities:

- Operational bypass instructions.
- Provider-specific evasion steps.
- Hidden policy circumvention.
- Target lists for restricted services.
- Traffic camouflage recipes.
- Automatic identity rotation for avoiding restrictions.
- Packet rewriting or interception outside reviewed lab prototypes.
- Destructive or stealthy network workflows.

These ideas can remain as non-operational research questions only when they are framed around safe detection, explanation, feasibility, and review requirements.
