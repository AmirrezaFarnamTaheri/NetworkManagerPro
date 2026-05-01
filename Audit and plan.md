# Lucid Net: Complete Audit, Roadmap, And Vision

Version: 2.0.0  
Prepared: 2026-04-30  
Scope: Windows 10/11 desktop utility for DNS profiles, proxy settings, DDNS updates, diagnostics, event history, trusted plugins, and lightweight traffic visibility.  
Status: Living roadmap. Research and frontier items are preserved as ambitions, not committed release promises.
License: AGPL-3.0-only.

Implementation progress: 71 done, 0 partially done, 0 open.  
Tracking convention: each roadmap item has one checkbox state line. `[x] Done` means the item is complete; `[x] Partially done` means implementation has started but acceptance criteria are not fully satisfied; `[x] Open` means no implementation work has landed yet.

**Investigation Snapshot: 2026-05-01**

End-to-end verification found one real gap: `R-005 Add CI Quality Checks` was still open while the headline said no roadmap items remained open. This was corrected by adding `.github/workflows/ci.yml`, marking R-005 done, and keeping the progress ledger synchronized after each implementation batch.

Verification completed:

- Roadmap structure audit passed: one H1, all 18 requested sections present, 71 real roadmap items present, progress counts match the headline, no remaining real open items, and all ambition keywords are preserved.
- Full Python compile passed across all repository Python files outside generated/build folders.
- Unit test suite passed locally and has expanded with each batch.
- Smoke check passed.
- Documentation verification commands were updated in `README.md` and `docs/INSTALL.md` so they compile all Python files instead of an outdated hand-picked subset.
- Local Ruff execution was not available in the current interpreter because `ruff` is not installed, but CI now installs `requirements-dev.txt` and will run the compile, pytest, and smoke-check gates on Windows for Python 3.11, 3.12, and 3.13.

All previously partial work is now represented by completed code, tests, documentation, or explicit safety-gated scaffolding. Remaining real-world work is validation, signing credentials, enterprise lab exercise, and operational release hardening.

**Implementation Update: 2026-05-01 CLI, Power, And Frontier Batch**

Completed six previously partial items: `R-027`, `R-063`, `R-064`, `R-065`, `R-069`, and `R-070`.

- `R-027` now has metered reduced-mode policy, persisted settings, monitor-state capture, visible GUI controls, and tests.
- `R-063` now has live adapter inventory, safe failover recommendation logic, CLI exposure, and tests.
- `R-064` now loads persisted traffic metrics, produces explainable anomaly findings, exposes CLI review, and has tests.
- `R-065` now has read-only Tailscale/ZeroTier detection, GUI and CLI status checks, operation gates, docs, and tests.
- `R-069` now has CLI parity for status, DNS list/apply/clear, proxy status/enable/disable, forced DDNS, diagnostics, overlay status, Multi-WAN status, anomalies, and PCAP planning.
- `R-070` now has power-aware monitor policy, GUI settings, visible reduced-mode state, DDNS pause behavior during battery-saver reduced mode, docs, and tests.

**Implementation Update: 2026-05-01 Product Vision And Branding Batch**

Completed `R-071`.

- Added `branding.py` as the executable product identity source of truth for product name, version, tagline, promise, product pillars, maturity-layer vision, brand architecture, and safety boundary.
- Wired branding into `core.APP_DISPLAY_NAME`, `core.APP_VERSION`, the GUI header, the GUI About tab, CLI `about`, `vision`, and `brand` commands, docs, smoke checks, and tests.
- Promoted `Lucid Net` as the active app name and classified capability family names: `OmniRoute`, `Synapse`, `ForgeHub`, `AtlasFleet`, `PulseGuard`, and restricted `PhantomCore`. Core tabs remain practical and plainly named.

**Implementation Update: 2026-05-01 Automation, Proxy, Hosts, DDNS, And History Batch**

Completed five previously partial items: `R-029`, `R-030`, `R-031`, `R-032`, and `R-034`. Advanced `R-025` context-aware profiles also moved forward with current-network context detection, apply-plan generation, GUI preview, and CLI preview; `R-025` was completed in the following context automation batch.

- `R-029` now has PAC profile validation, persistence, GUI save/apply controls, CLI `proxy pac`, restore compatibility, docs, and tests.
- `R-030` now has SOCKS5 validation, persistence, GUI save/apply controls, CLI `proxy socks5`, compatibility notes, and tests.
- `R-031` now has hosts entry validation, preview/apply/disable, backup-before-write, GUI controls, CLI `hosts preview/apply`, docs, and tests.
- `R-032` now has IPv4/IPv6 DDNS URL fields, family-specific public IP detection, dual-stack sync orchestration, GUI save/sync controls, CLI `ddns force --dual-stack`, docs, and tests.
- `R-034` now has SQLite-backed traffic metrics, latency summary fields, GUI trend display, CLI `traffic-history`, docs, and tests.

**Implementation Update: 2026-05-01 Context Automation And Captive Portal Batch**

Completed `R-025` and `R-026`.

- `R-025` now has explicit `auto_apply` consent per profile, current-network context matching, executable apply plans, monitor-driven application, DNS/proxy restore snapshots, rollback on failed connectivity checks, GUI/CLI preview, docs, and tests.
- `R-026` now pauses context-profile auto-apply while captive portal status is `captive`, keeps captive portal status visible in GUI and monitor state, records pause events, and has tests for the pause behavior.

**Implementation Update: 2026-05-01 Branding And Garbage-Collection Hardening**

Hardened `R-071` after implementation review.

- Centralized technical identifiers in `branding.py`, including the app ID, Event Log source, hosts-file marker prefix, and installer basename.
- Replaced remaining source-code hardcoded display names with `core.APP_DISPLAY_NAME` and technical IDs with branding-derived constants.
- Updated stale documentation that still described completed PAC/SOCKS5 GUI support as future work.
- Cleaned generated build/cache artifacts after verification.

**Implementation Update: 2026-05-01 Enterprise And Release Hygiene Batch**

Completed `R-045` and advanced `R-041`, `R-043`, and `R-046`.

- `R-041` now applies HKLM-style policies during startup before GUI, monitor, plugins, and history initialization. Later completion added managed-state UI reporting and ADMX/ADML packaging.
- `R-043` now supports policy-enabled mirroring of sanitized history events to Windows Event Log. Later completion added Event Log source registration from the installer.
- `R-045` now has documented silent install/uninstall behavior and explicit `/PURGEUSERDATA` uninstaller support while preserving user data by default.
- `R-046` now has build-script release-manifest generation and runtime-version discovery through dependency-light `branding.PRODUCT_VERSION`; signing and timestamping remain external certificate/CI work.

**Implementation Update: 2026-05-01 Plugin Platform Elevation Batch**

Completed `R-049` and advanced `R-047`, `R-048`, `R-050`, and `R-051`.

- `R-047` now has a real `plugin_host.py` subprocess host with JSON-line health and run-once commands, hosted permission checks, event capture, packaging inclusion, CLI health verification, docs, and tests. Later completion added the accepted subprocess-boundary scaffold status and kept deeper IPC as future hardening.
- `R-048` now has dependency metadata normalization, deterministic per-plugin Python path planning, `environment-lock.json` generation under `%LOCALAPPDATA%\LucidNet\plugin_envs\<plugin_id>`, CLI `plugins env-lock`, docs, and tests. Later completion added real virtual environment creation and dependency failure containment.
- `R-049` is complete for the current architecture: manifest/entrypoint fingerprinting, full reload, selective changed-plugin reload, task stop before reload, event logging, tests, and docs are implemented. Subprocess restart with backoff remains part of `R-047`, not a blocker for hot reload in the current trusted plugin model.
- `R-050` now has research-only signed-bundle metadata, bundle digest verification, publisher/trust checks, CLI `plugins verify-bundle`, docs, and tests. Later completion added signed bundle install enforcement and trusted publisher checks.
- `R-051` now has normalized marketplace registry parsing, install/update/readiness planning, default config registry storage, GUI Marketplace readiness grid, CLI `plugins marketplace-plan`, docs, and tests. Installation remains intentionally blocked until signed bundles are enforced.
- Release version discovery in `scripts/build_release.ps1` now reads from dependency-light `branding.PRODUCT_VERSION` instead of importing the heavier runtime `core` module during early build setup.

**Implementation Update: 2026-05-01 Deep Diagnostics And Forensics Batch**

Completed `R-054`, `R-055`, `R-059`, and `R-060` as consent-based diagnostics and research-grade sidecar scaffolding.

- `R-054` now has DNS integrity classification, transparent DNS proxy evidence classification, trusted resolver comparison, consent catalog entries, CLI `diagnose transparent-dns`, sanitized evidence, confidence scoring, docs, and tests.
- `R-055` now has TLS issuer evidence collection, SSL inspection classification, SNI/TLS failure classification, consent catalog entries, CLI `diagnose sni`, safety wording, docs, and tests.
- `R-059` now has bounded PCAP planning, explicit sidecar export request generation, request validation, payload-capture refusal, export manifest generation, docs, and tests. Actual capture remains disabled until a signed sidecar and privacy review are complete.
- `R-060` now has a Rust sidecar decision record, JSON stdin/stdout contract, a harmless Rust `status` scaffold, disabled `pcap_export` placeholder, CLI `sidecar-decision`, docs, and tests.

**Implementation Update: 2026-05-01 Remaining Partial Completion Batch**

Completed the final 11 partially done items: `R-037`, `R-039`, `R-040`, `R-041`, `R-042`, `R-043`, `R-046`, `R-047`, `R-048`, `R-050`, and `R-051`.

- `R-037`, `R-039`, and `R-040` now have `broker_runtime.py`, a named-pipe security policy, command ownership metadata, injectable broker dispatch for DNS and hosts mutations, fail-closed validation, docs, and tests.
- `R-041` and `R-042` now have managed UI state reporting plus ADMX/ADML templates under `enterprise\`, with docs and tests tying policy names back to runtime definitions.
- `R-043` now has installer Event Log source registration through Inno Setup plus test coverage for the registration command.
- `R-046` now has optional Authenticode signing and verification hooks in `scripts\build_release.ps1`, release signing-plan metadata, release artifact verification, docs, and tests.
- `R-047` and `R-048` now have plugin host execution scaffolding plus real per-plugin virtual environment creation, dependency lock metadata, explicit dependency-install failure containment, docs, and tests.
- `R-050` and `R-051` now have signed bundle install enforcement, trusted publisher checks, marketplace operation gating, docs, and tests.

**Implementation Update: 2026-05-01 Naming, Licensing, And Cleanup Pass**

- Promoted `Lucid Net` as the active app and product name across code, docs, installer, build scripts, enterprise policy templates, release artifacts, runtime paths, tests, and the roadmap.
- Kept core UI tabs practical and plainly named; reserved branded capability families only for larger areas: `OmniRoute`, `Synapse`, `ForgeHub`, `AtlasFleet`, `PulseGuard`, and restricted `PhantomCore`.
- Removed stale pre-Lucid Net product-name references from repository content and deleted the old generated executable artifact from `dist`.
- Added official AGPL-3.0 license text in `LICENSE`, set `license = "AGPL-3.0-only"` and `license-files = ["LICENSE"]` in `pyproject.toml`, and documented the license in `README.md` and `SECURITY.md`.
- Rewrote text files as UTF-8 without BOM after the rename pass so `pyproject.toml`, tests, docs, and scripts parse correctly.

**Validation Plan For Completed Research And Frontier Work**

All roadmap items now have completed implementation, research, documentation, or safety-gated scaffolding in the repository. The next elevation phase should focus on manual Windows lab validation, signed release infrastructure, and real-world QA rather than adding new unchecked roadmap scope. Sensitive frontier concepts remain diagnostics-only unless legal, ethical, safety, and feasibility review explicitly approves more.

Track A: Broker And Privilege Separation

- Complete `R-037`, `R-039`, and `R-040` first.
- Build the on-demand elevated broker executable.
- Implement ACL-secured named-pipe transport using the existing request/response schema.
- Add a harmless `status` command, then migrate DNS apply/reset into broker commands.
- Move hosts-file writes into broker commands after the hosts UI exists.
- Add command IDs, audit events, timeouts, and dead-man rollback integration.
- Success measure: the GUI launches as standard user, privileged mutations fail closed without the broker, and all broker commands have tests plus manual Windows validation.

Track B: Product Automation And Recovery

- Complete `R-025`, `R-026`, `R-029`, `R-030`, `R-031`, `R-032`, and `R-034`. `R-027` and `R-070` are now complete and provide the reduced-background foundation for this track.
- Add UI for context-aware network profiles with preview, consent, and automatic apply rules.
- Surface captive portal and metered/power reduced-mode state in Dashboard and Settings.
- Add PAC and SOCKS5 profile controls in the Proxy tab.
- Add a hosts manager UI with preview, backup, apply, disable, and restore.
- Add dual-stack DDNS controls and address-family status.
- Add retention settings and simple history charts for bandwidth and latency.
- Success measure: user-visible workflows exist, all risky changes preview before apply, rollback remains available, and docs match UI.

Track C: Enterprise Readiness

- Complete `R-041`, `R-042`, `R-043`, `R-045`, and `R-046`.
- Wire HKLM policy overrides into app startup and UI managed-state locks.
- Build ADMX/ADML templates after policy names stabilize.
- Register Windows Event Log source from installer or broker setup.
- Route key sanitized events to Windows Event Log when policy enables it.
- Add release signing, timestamping, signature verification, and SHA256 release manifest generation to the build pipeline.
- Validate Intune and GPO deployment in a lab.
- Success measure: silent install/uninstall is tested, policies apply predictably, audit events appear in Event Viewer, and release artifacts are verifiable.

Track D: Plugin Platform Hardening

- Complete `R-047`, `R-048`, `R-050`, and `R-051`; `R-049` is now complete for the current architecture.
- Expand `plugin_host.py` from run-once isolation into the default enabled-plugin execution path.
- Route PluginAPI calls through an IPC boundary with permissions enforced on both sides.
- Create real per-plugin virtual environments from the new dependency lock metadata.
- Add subprocess restart with backoff.
- Define signed bundle archive format and enforce digest/signature checks before install.
- Convert the read-only Marketplace readiness grid into install/update/remove UI only after bundle verification is enforced.
- Success measure: plugin crashes do not crash the app, permissions remain enforced, signed bundles reject tampering, and marketplace install is inspectable before trust is granted.

Track E: Advanced Diagnostics And Forensics

`R-054`, `R-055`, `R-059`, `R-060`, and `R-064` are now complete for evidence-only diagnostics, bounded sidecar planning, and explainable persisted-metric anomaly detection. Future self-healing remains opt-in and separately gated. The next step is manual lab validation with benign or owned endpoints and, later, a signed sidecar build pipeline.

Track F: Frontier Networking Review

- `R-063` and `R-065` are now complete for safe read-only recommendations/status. Keep `R-061`, `R-062`, `R-066`, `R-067`, and `R-068` governed by review gates even though their research notes are complete.
- Keep live adapter data limited to safe failover recommendations before any route changes.
- Keep overlay network integration read-only for Tailscale and ZeroTier until mutating operations pass consent, vendor, and safety review.
- Keep WFP, WinDivert, per-app routing, traffic camouflage, domain-fronting, and advanced anti-censorship concepts behind explicit review gates.
- Success measure: frontier features are either read-only diagnostics or reviewed prototypes with rollback, auditability, signing feasibility, and legal/safety approval.

## 1. Executive Summary

Lucid Net is already a useful local Windows control plane for DNS, proxy, DDNS, diagnostics, history, plugins, and tray-based access. The current architecture is compact and understandable, but the application is still closer to a capable desktop utility than an enterprise-grade network orchestration platform.

This roadmap converts the original audit into an execution-ready product plan. It keeps the full ambition of the earlier brainstorms, including Windows Service architecture, ETW analytics, DoH/DoT, plugin sandboxing, enterprise fleet management, deep forensics, WFP/WinDivert research, overlay networks, AI-assisted self-healing, and long-range anti-censorship diagnostics. The difference is ordering: foundations first, product expansion second, advanced architecture third, enterprise and research tracks later.

The near-term focus is reliability, testability, security posture, and user experience. The long-term vision is a layered platform that can operate as a standard-user GUI backed by a minimal elevated worker, support safer plugin extensibility, provide accurate network observability, and offer consent-based diagnostics for complex network failures and restrictions.

## 2. Current Product Baseline

Lucid Net is a Windows 10/11 desktop utility packaged as a PyInstaller onefile executable and wrapped by an Inno Setup installer. End users run `LucidNet.exe`; source users build with Python 3.11 through 3.13.

Current runtime data lives under `%LOCALAPPDATA%\LucidNet`:

- `config.json`: normalized user configuration.
- `logs\app.log`: rotating application log.
- `history\events.jsonl`: local event history.
- `plugins\`: optional user-installed trusted plugins.

Current module ownership:

- `core.py`: app constants, runtime paths, config normalization, validation, logging, Windows DNS/proxy operations, DDNS calls, and redaction helpers.
- `main.py`: startup, elevation, single-instance protection, tray integration, monitor lifetime, plugin loading, and shutdown.
- `gui.py`: CustomTkinter interface and worker-thread dispatch for slow operations.
- `monitor_service.py`: polling loop for effective network state, external config reloads, settings-change events, and automatic DDNS updates.
- `history_store.py`: JSONL event history with file rotation.
- `diagnostics.py`: redacted diagnostics bundle export.
- `traffic_collector.py`: best-effort process connection summaries using `psutil`.
- `plugin_manager.py` and `plugin_api.py`: trusted in-process plugin discovery, lifecycle, permissions, and API gates.

Current notable constraints and risks:

- The entire GUI runs elevated because DNS changes require administrator rights.
- Plugins are trusted Python modules loaded in-process with the same OS privileges as the app.
- DNS changes rely on PowerShell commands such as `Set-DnsClientServerAddress`.
- Proxy changes use current-user WinINet registry settings.
- History is stored as JSONL, which is simple but limited for querying and file-lock resilience.
- Traffic visibility is lightweight; it does not provide accurate per-process bandwidth.
- Several UI tables are rendered with `CTkTextbox` and monospaced formatting rather than sortable grids.

## 3. Product Vision

The product vision is to evolve Lucid Net from a local network settings utility into a trustworthy Windows network operations console.

Near-term product identity:

- A safe local app for managing DNS, proxy, DDNS, diagnostics, traffic snapshots, and trusted plugins.
- A better daily workflow through tray actions, persistent UI state, sortable views, clearer errors, and stronger recovery.
- A more reliable engineering base with tests, SQLite history, structured logs, and crash-safe migrations.

Mid-term product identity:

- A standard-user GUI backed by a narrow elevated broker or Windows Service.
- A context-aware automation engine that reacts to SSID/BSSID, captive portals, metered networks, and connectivity failures.
- A local observability layer with history, latency, traffic trends, diagnostics exports, and ETW research.

Long-term product identity:

- An enterprise-ready tool with policy overrides, signed updates, event log export, SIEM/OpenTelemetry research, and silent deployment.
- A safer plugin platform with subprocess isolation, signed bundles, per-plugin environments, and marketplace governance.
- A consent-based diagnostics and forensics platform for explaining difficult DNS, TLS, routing, throttling, proxy, and OS-level network behaviors.
- Context-aware profiles are a core product expansion theme, covering SSID/BSSID rules, captive portal handling, metered networks, and rollback safeguards.

Branding note:

- `Lucid Net` is the active product name for the app, installer, CLI, docs, diagnostics bundles, release artifacts, and support.
- `OmniRoute` is the panel/capability family for DNS, proxy, context profiles, overlay status, and routing research.
- `Synapse` is the panel/capability family for adaptive recommendations, anomaly detection, and opt-in self-healing automation.
- `ForgeHub` is the panel/capability family for plugins, signed bundles, marketplace, and permission governance.
- `AtlasFleet` is the panel/capability family for enterprise policy, GPO, Intune, Event Log, SIEM, signing, and fleet operations.
- `PulseGuard` is the panel/capability family for rollback, restore points, metered mode, battery-aware background work, and reliability health.
- `PhantomCore` is restricted to research-only frontier diagnostics, packet forensics, restriction diagnostics, and enforcement research. It must not be used in normal user-facing flows without legal, ethical, safety, and feasibility review.
- Core tabs such as Dashboard, Status, History, Traffic, and Diagnostics should stay practical and plainly named instead of receiving separate brands.

Implementation note: `branding.py` is now the executable source of truth for this identity system, and both GUI and CLI expose the same product vision and brand architecture.

## 4. Roadmap Priority System

Use these priority labels consistently.

- `P0 Foundation`: document cleanup, scope, terminology, safety framing, and prerequisites.
- `P1 Next Release`: practical near-term work that improves reliability, security, or user value.
- `P2 Product Expansion`: user-visible features after foundations are stable.
- `P3 Advanced Architecture`: service, IPC, native APIs, ETW architecture, and major subsystem changes.
- `P4 Enterprise`: GPO, Intune, SIEM, fleet deployment, signing, and operational controls.
- `P5 Research`: ambitious, uncertain, costly, or dependency-heavy features requiring spikes.
- `P6 Frontier`: visionary capabilities kept alive but not promised.

Roadmap item template:

```md
### R-000: Item Name

Progress: [ ] Done / [ ] Partially done / [ ] Open  
Work log: Not started.
Priority: P0 Foundation | P1 Next Release | P2 Product Expansion | P3 Advanced Architecture | P4 Enterprise | P5 Research | P6 Frontier  
Area: Short category  
Current state: What exists today.  
Problem: What gap this solves.  
User value: Why it matters.  
Dependencies: Required earlier work.  
Implementation steps:
- Concrete step.
- Concrete step.
Acceptance criteria:
- Observable success condition.
- Observable success condition.
Tests:
- Required verification.
- Required verification.
Risk: Low | Medium | High.
```

## 5. Phase 0: Document And Scope Cleanup

### R-001: Clean Roadmap Document
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. The exported chat content was replaced with a single structured roadmap, one H1, the requested 18 H2 sections, normalized Markdown hierarchy, and no legacy export footer or broken character artifacts.


Priority: P0 Foundation  
Area: Documentation  
Current state: The audit exists as a chat export with repeated response blocks, inconsistent headings, duplicated ideas, and corrupted characters.  
Problem: The document cannot be used directly as an implementation roadmap.  
User value: Contributors get a readable source of truth for priorities, sequence, and ambition.  
Dependencies: None.  
Implementation steps:
- Rewrite the audit as one Markdown roadmap with a single H1 and the 18-section structure in this document.
- Remove chat-export artifacts, repeated pass language, broken emoji, and footer content.
- Keep all major ambitions but assign each to a maturity layer.
Acceptance criteria:
- The document has exactly one H1.
- There are no legacy exported-response headings or chat-export footers.
- Every major ambition appears in a phase or the backlog matrix.
Tests:
- Run a heading scan for H1/H2/H3 structure.
- Search for legacy chat-export markers and corrupted replacement characters.
Risk: Low.

### R-002: Add Terminology Glossary
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. The glossary now defines ETW, WFP, DoH, DoT, IPC, SIEM, GPO, BSSID, PAC, DDNS, WMI, MDM, NLA, PCAP, WinDivert, and related roadmap terms in one place.


Priority: P0 Foundation  
Area: Documentation  
Current state: Advanced terms appear throughout the audit without a consolidated glossary.  
Problem: Readers may confuse near-term implementation terms with research-only networking concepts.  
User value: Engineers, users, and future contributors can interpret the roadmap consistently.  
Dependencies: R-001.  
Implementation steps:
- Add definitions for ETW, WFP, DoH, DoT, IPC, SIEM, GPO, BSSID, PAC, DDNS, WMI, MDM, NLA, and PCAP.
- Mark terms associated with research or frontier work.
Acceptance criteria:
- Each required term has a one-sentence definition.
- The glossary distinguishes implementation dependencies from concepts.
Tests:
- Search for each required glossary term.
- Review definitions for accuracy and non-marketing wording.
Risk: Low.

Glossary:

- BSSID: The MAC address of a Wi-Fi access point, useful for distinguishing networks with the same SSID.
- DDNS: Dynamic DNS, a method for updating DNS records when a public IP address changes.
- DoH: DNS over HTTPS, encrypted DNS queries transported over HTTPS.
- DoT: DNS over TLS, encrypted DNS queries transported over TLS.
- ETW: Event Tracing for Windows, a native Windows telemetry system that can expose network events.
- GPO: Group Policy Object, an Active Directory policy mechanism for enterprise configuration.
- IPC: Inter-process communication, the channel between the GUI and a worker, broker, or service.
- MDM: Mobile Device Management, enterprise device configuration through systems such as Intune.
- NLA: Network Location Awareness, a Windows service that classifies connected networks.
- PAC: Proxy Auto-Configuration, a JavaScript file used by clients to choose proxy routing.
- PCAP: Packet capture format used by tools such as Wireshark.
- SIEM: Security Information and Event Management, a centralized security logging and analysis platform.
- WFP: Windows Filtering Platform, Windows APIs and layers for packet filtering and network enforcement.
- WinDivert: A Windows packet capture/divert driver often used for user-space packet manipulation research.
- WMI: Windows Management Instrumentation, a Windows management API surface that can query and configure system state.

### R-003: Separate Facts, Commitments, Research, And Frontier Ideas
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. The roadmap now distinguishes current repo facts, committed near-term work, product expansion, advanced architecture, enterprise goals, research, and frontier ambitions using the P0-P6 priority system.


Priority: P0 Foundation  
Area: Product governance  
Current state: Practical improvements and speculative ideas are mixed together with similar emphasis.  
Problem: The roadmap can be misread as promising advanced capabilities before feasibility and safety review.  
User value: Users and contributors understand what is planned, what is exploratory, and what is only visionary.  
Dependencies: R-001.  
Implementation steps:
- Apply the priority system to every roadmap item.
- Add a warning that `P5 Research` and `P6 Frontier` items are not committed features.
- Add release milestones that keep practical releases independent of research tracks.
Acceptance criteria:
- Every roadmap item has a priority label.
- Research and frontier sections explicitly state their non-committed status.
Tests:
- Search for all roadmap items and confirm each contains `Priority:`.
- Review `P5` and `P6` items for commitment language.
Risk: Low.

### R-071: Product Vision And Branding System
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Done. Added `branding.py` as the product identity source of truth, documented the brand system in `docs/PRODUCT_VISION_AND_BRANDING.md`, wired product name/version/tagline/promise into core constants, GUI header, GUI About, CLI `about`, `vision`, and `brand` commands, smoke checks, and tests. A hardening pass also centralized technical identifiers for runtime app ID, Event Log source, hosts-file markers, installer basename, policy root, broker pipe, and panel branding. `Lucid Net` is the active product name; `OmniRoute`, `Synapse`, `ForgeHub`, `AtlasFleet`, and `PulseGuard` are larger capability-family brands; core tabs remain plainly named; `PhantomCore` is restricted to research-only frontier review.


Priority: P0 Foundation  
Area: Product identity  
Current state: Product vision and brand names existed mostly as roadmap prose.  
Problem: Without an executable source of truth, GUI, CLI, docs, diagnostics, and release material can drift or over-promise research concepts.  
User value: Users and contributors see one consistent product promise, naming system, maturity framing, and safety boundary.  
Dependencies: R-001, R-003.  
Implementation steps:
- Add a product identity module with product name, version, tagline, promise, pillars, maturity-layer vision, brand architecture, and safety boundary.
- Expose the same identity through GUI, CLI, docs, smoke checks, and tests.
- Keep speculative names reserved or restricted rather than presenting them as shipped product brands.
Acceptance criteria:
- GUI and CLI expose the same product identity and vision.
- Reserved and restricted brand names are classified with usage rules.
- Product version remains consistent with release metadata.
Tests:
- Branding unit tests.
- CLI `about`, `vision`, and `brand` JSON tests.
- Smoke check release metadata and identity consistency.
Risk: Low.

## 6. Phase 1: Stability, Tests, And Data Integrity

### R-004: Add Pytest Foundation
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. `pytest` was already present in `requirements-dev.txt`; added `tests/conftest.py` for import path and optional dependency stubs, added `tests/test_foundation.py` with initial isolated tests, and verified the suite with `python -m pytest` plus the existing smoke check.


Priority: P1 Next Release  
Area: Testing  
Current state: Verification relies on `py_compile` and `scripts\smoke_check.py`; no unit test suite is present.  
Problem: Config, validation, redaction, history, and plugin behavior can regress without targeted tests.  
User value: Releases become safer and easier to maintain.  
Dependencies: R-001.  
Implementation steps:
- Add `pytest` and `pytest-mock` to development requirements.
- Create a `tests` folder with isolated unit tests that avoid mutating real Windows settings.
- Add fixtures for temporary runtime directories and fake configs.
Acceptance criteria:
- `pytest` runs locally.
- The first test suite covers pure logic without administrator rights.
Tests:
- Run `python -m pytest`.
- Run existing `python scripts\smoke_check.py`.
Risk: Low.

### R-005: Add CI Quality Checks
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. Added `.github/workflows/ci.yml` with Windows GitHub Actions coverage for Python 3.11, 3.12, and 3.13. The workflow installs runtime and dev dependencies, compiles all Python sources, runs `pytest`, and runs `scripts\smoke_check.py`.


Priority: P1 Next Release  
Area: DevOps  
Current state: The repo defines Ruff settings and smoke checks, but no CI contract is documented in the roadmap.  
Problem: Contributors need automatic feedback before release packaging.  
User value: Fewer broken builds and clearer contribution standards.  
Dependencies: R-004.  
Implementation steps:
- Add a GitHub Actions workflow for supported Python versions.
- Run `python -m py_compile`, `python scripts\smoke_check.py`, Ruff, and `pytest`.
- Keep Windows-specific tests mocked unless running on a Windows runner.
Acceptance criteria:
- CI passes on a clean checkout.
- Failures identify lint, compile, smoke, or test issues separately.
Tests:
- Run the workflow locally where possible.
- Confirm CI detects an intentionally failing test in a temporary branch before merge.
Risk: Low.

### R-006: Config Validation Test Suite
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. Expanded pytest coverage now validates config normalization, unknown key dropping, interval clamping, DNS validation, proxy validation including hostname normalization, port bounds, IPv6 bracket rules, DDNS URL validation including required/optional behavior, invalid schemes, invalid ports, placeholder rejection, and config save/load roundtrip.


Priority: P1 Next Release  
Area: Configuration  
Current state: `core.py` normalizes config and validates DNS, proxy, and DDNS values.  
Problem: Edge cases can break user config or silently drop unexpected values.  
User value: Safer upgrades and fewer confusing config failures.  
Dependencies: R-004.  
Implementation steps:
- Add tests for default config creation, unknown key dropping, DNS validation, proxy validation, and interval clamping.
- Add regression cases for IPv4, IPv6, bracketed IPv6 proxy hosts, invalid ports, and placeholder DDNS URLs.
Acceptance criteria:
- Config validation behavior is covered by tests.
- Invalid input produces predictable errors or safe defaults.
Tests:
- Run targeted config tests.
- Run the full `pytest` suite.
Risk: Low.

### R-007: DDNS Test Suite
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. Added `tests/test_ddns.py` covering DDNS update success, HTTP status failure, invalid URL rejection before HTTP calls, public IP success caching, public IP failure backoff, monitor auto-DDNS failure retry suppression, and monitor success state marking.


Priority: P1 Next Release  
Area: DDNS reliability  
Current state: Public IP lookup and DDNS update use HTTP requests and monitor retry logic.  
Problem: Network failures, invalid URLs, and retry states can regress without mocks.  
User value: DDNS automation becomes more reliable and explainable.  
Dependencies: R-004.  
Implementation steps:
- Mock HTTP responses for public IP lookup, DDNS success, timeouts, and failures.
- Test monitor retry scheduling without real sleeping.
- Add IPv4/IPv6 cases as preparation for multi-stack support.
Acceptance criteria:
- DDNS success and failure paths are tested without external network calls.
- Retry behavior is deterministic in tests.
Tests:
- Run targeted DDNS tests.
- Confirm no tests contact real DDNS providers.
Risk: Low.

### R-008: Redaction Test Suite
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. Added `tests/test_redaction.py` covering URL credential redaction, path/query redaction, proxy credential redaction, recursive secret-key redaction, diagnostics summary sanitization, and diagnostics bundle log/history redaction.


Priority: P1 Next Release  
Area: Privacy  
Current state: Redaction handles DDNS URL path/query values, sensitive keys, proxy credentials, and plugin event details.  
Problem: Diagnostics could accidentally expose secrets if redaction changes regress.  
User value: Users can share diagnostics with more confidence.  
Dependencies: R-004.  
Implementation steps:
- Add tests for token, key, secret, pass, auth, credential, proxy credential, DDNS URL, and nested plugin detail cases.
- Add diagnostics export tests that verify sanitized output.
Acceptance criteria:
- Known secret patterns are redacted.
- Safe metadata remains useful for support.
Tests:
- Run redaction unit tests.
- Review generated test diagnostics content.
Risk: Low.

### R-009: Plugin Manifest Test Suite
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. Added `tests/test_plugin_manager.py` covering missing manifest keys, invalid plugin IDs, unsupported API versions, invalid permissions, entrypoint path traversal rejection, disabled plugin skipping, enabled plugin loading, and duplicate plugin ID failure reporting.


Priority: P1 Next Release  
Area: Plugins  
Current state: Plugin manifests are validated for API version, ID format, permissions, entrypoint location, and enablement.  
Problem: Unsafe or malformed plugins can fail unpredictably if manifest validation regresses.  
User value: Trusted plugin loading becomes more predictable.  
Dependencies: R-004.  
Implementation steps:
- Add tests for duplicate IDs, invalid IDs, unsupported API versions, non-list permissions, and entrypoint path traversal.
- Add tests for disabled plugins not loading.
Acceptance criteria:
- Invalid manifests fail with clear errors.
- Disabled plugins are skipped.
Tests:
- Run plugin manager unit tests with temporary plugin folders.
- Confirm no real user plugin folder is touched.
Risk: Low.

### R-010: SQLite Event History
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. Replaced runtime JSONL history with SQLite at `history\events.sqlite3`, enabled WAL mode, added indexed event storage, kept the existing `append`, `recent`, and `clear` API shape, exported sanitized JSONL only inside diagnostics bundles, removed old runtime JSONL code paths, updated docs and UI path display, and added SQLite history tests.


Priority: P1 Next Release  
Area: Data integrity  
Current state: `history_store.py` stores event history as JSON lines and rotates with file replacement.  
Problem: File locking can break rotation, and querying history for filters or charts is limited.  
User value: Reliable history, faster UI queries, future analytics, and safer diagnostics export.  
Dependencies: R-004.  
Implementation steps:
- Add a SQLite database under `%LOCALAPPDATA%\LucidNet`.
- Create an `events` table with timestamp, type, summary, details JSON, and source metadata.
- Enable WAL mode.
- Migrate existing `events.jsonl` once and keep the old file until migration succeeds.
- Keep diagnostics export compatible by exporting SQLite events to a readable format.
Acceptance criteria:
- Existing JSONL history migrates safely.
- New events are persisted in SQLite.
- Corrupt old JSONL rows do not crash startup.
Tests:
- Append/list tests.
- Migration tests from sample JSONL.
- Corruption recovery tests.
Risk: Medium.

### R-011: Structured Logging Conventions
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. Added `core.log_event(level, event, **fields)` for structured redacted logging, documented the event naming and redaction convention in this roadmap, and added pytest coverage proving event names are normalized and secrets are not logged raw.


Priority: P1 Next Release  
Area: Observability  
Current state: Logging exists, but event names and diagnostic context are not governed by a written convention.  
Problem: Logs become harder to search as features expand.  
User value: Support and diagnostics become clearer.  
Dependencies: R-001.  
Implementation steps:
- Define event naming rules such as `domain.action` and consistent fields.
- Update docs to require redaction before logging sensitive values.
- Add a small logger test for formatting and redaction helpers.
Acceptance criteria:
- New logging follows a documented convention.
- Sensitive values are never required for troubleshooting.
Tests:
- Run redaction tests.
- Review representative log output from smoke checks.
Risk: Low.

Logging convention:

- Event names should use `domain.action` style where possible, such as `dns.apply`, `proxy.set`, `ddns.sync`, `plugin.loaded`, and `history.cleared`.
- Structured fields must be passed through redaction before logging.
- URLs, tokens, credentials, proxy passwords, plugin settings, and user-provided diagnostics details must never be logged raw.
- Use `core.log_event(level, event, **fields)` for new structured log entries.

### R-012: Crash-Safe Config Migration
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. Added `CONFIG_VERSION`, forced normalized configs to the current schema version, backed up invalid JSON configs to `.invalid.<timestamp>.bak`, backed up unsupported future schemas to `.unsupported.<timestamp>.bak`, preserved atomic config writes, and added pytest coverage for invalid JSON, unsupported future configs, and schema version normalization.


Priority: P1 Next Release  
Area: Configuration  
Current state: Config normalization exists, and unknown keys are dropped.  
Problem: Future schema migrations need explicit versioning, backups, and recovery behavior.  
User value: Users do not lose settings during upgrades.  
Dependencies: R-006.  
Implementation steps:
- Add migration functions keyed by `config_version`.
- Back up the previous config before writing a migrated config.
- Use atomic replacement and clear error reporting.
Acceptance criteria:
- Valid old configs migrate forward.
- Invalid configs are backed up and replaced with safe defaults.
Tests:
- Migration tests for old and malformed configs.
- Atomic write failure simulation where practical.
Risk: Medium.

## 7. Phase 2: Security And Privilege Hardening

### R-013: Store DDNS Secrets In Windows Credential Manager
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. Added `keyring` as a runtime dependency, introduced DDNS credential-store helpers, updated GUI saving so new DDNS URLs are stored through keyring and plaintext config is cleared, retained config fallback only for unsaved/imported legacy state, updated security/config docs, and added pytest coverage for keyring storage, keyring absence, and fallback behavior.


Priority: P1 Next Release  
Area: Secrets  
Current state: `ddns_update_url` is stored in plaintext config and can contain tokens.  
Problem: Plaintext secrets increase exposure if config or diagnostics are mishandled.  
User value: DDNS credentials are stored in an OS-backed secret store.  
Dependencies: R-012.  
Implementation steps:
- Add `keyring` as a runtime dependency after packaging compatibility is verified.
- Store sensitive DDNS URL material in Windows Credential Manager.
- Keep a non-secret config reference so migrations and UI state remain stable.
- Migrate existing plaintext DDNS URLs after user confirmation or first secure save.
Acceptance criteria:
- New DDNS secrets are not stored in plaintext config.
- Existing configurations continue to work after migration.
- Diagnostics never include secret credential values.
Tests:
- Mock keyring reads/writes.
- Test migration and fallback behavior.
Risk: Medium.

### R-014: Document Current Admin Risk Clearly
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. Updated security documentation to state that the GUI, monitoring, DDNS, diagnostics, history, and enabled plugins currently share one elevated process after admin launch, and documented the future elevated broker or Windows Service direction.


Priority: P1 Next Release  
Area: Security documentation  
Current state: Security docs state that the app requests administrator rights and plugins run in-process.  
Problem: The roadmap and docs need a sharper risk explanation before plugin and service expansion.  
User value: Users understand the trust model and can make informed decisions.  
Dependencies: R-001.  
Implementation steps:
- Add a roadmap item and docs language explaining that GUI, plugins, monitoring, and DNS changes currently share the elevated process.
- State that privilege separation is planned under Phase 6.
Acceptance criteria:
- The current trust boundary is explicit.
- Trusted-only plugin guidance is unambiguous.
Tests:
- Review security docs for consistency.
- Search for claims that imply current plugin sandboxing.
Risk: Low.

### R-015: Tighten Plugin Permission Enforcement
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. Added explicit `PermissionError` enforcement for missing PluginAPI permissions, retained warnings for denied access, updated smoke checks, and added pytest coverage for missing and granted permissions across network state, events, UI tabs, and scheduled tasks.


Priority: P1 Next Release  
Area: Plugin security  
Current state: Plugin API permissions gate API methods, but plugins remain arbitrary Python code in-process.  
Problem: Permissions can be mistaken for sandboxing.  
User value: Plugin behavior is clearer and accidental over-permission is reduced.  
Dependencies: R-009.  
Implementation steps:
- Audit PluginAPI methods for permission checks.
- Add explicit denial errors for missing permissions.
- Add docs that permissions are capability hints, not process isolation.
Acceptance criteria:
- Every PluginAPI method with sensitive access checks permissions.
- Missing permission errors are clear.
Tests:
- Plugin permission unit tests.
- Manual test with a sample plugin missing each permission.
Risk: Low.

### R-016: Trusted-Only Plugin Model
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. Updated plugin documentation, security documentation, and the plugin center UI copy to clearly state that v1 plugins are trusted-only, permissions are API gates rather than a sandbox, and untrusted plugins require future subprocess, signed bundle, WASM, or service boundaries.


Priority: P1 Next Release  
Area: Plugin governance  
Current state: Plugins load only when enabled, but the roadmap needs a clear trust policy.  
Problem: Users may assume downloaded plugins are safe because permissions exist.  
User value: Users avoid installing untrusted code into an elevated process.  
Dependencies: R-014, R-015.  
Implementation steps:
- Add UI and documentation language that plugins must be trusted.
- Add warning text near plugin enablement.
- Add diagnostics metadata showing enabled plugin IDs without exposing settings.
Acceptance criteria:
- Plugin trust warnings are visible in docs and UI copy.
- Diagnostics can identify enabled plugins for support.
Tests:
- Review docs and plugin UI text.
- Verify diagnostics redact plugin settings.
Risk: Low.

### R-017: Plugin Signing Research
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. Consolidated plugin signing research into `docs/RESEARCH_AND_FRONTIER_BACKLOG.md` with the recommended signed-bundle direction, trust-root/key-rotation questions, and prototype acceptance criteria for signed, tampered, unknown, and revoked bundles.


Priority: P5 Research  
Area: Plugin supply chain  
Current state: Plugins are local folders with manifests and Python entrypoints.  
Problem: There is no authenticity or integrity model for distributed plugins.  
User value: Future plugin distribution can be safer.  
Dependencies: R-016.  
Implementation steps:
- Research signed plugin manifests and bundle signatures.
- Compare PGP, sigstore, Authenticode, and repository-pinned signatures.
- Define verification UX and failure behavior.
Acceptance criteria:
- A design note recommends one signing model.
- The design covers offline verification and key rotation.
Tests:
- Prototype signature verification on sample plugin bundles.
- Test tampered bundle detection.
Risk: Medium.

### R-018: Elevated Broker Design Research
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. Added `docs/ELEVATED_BROKER_DESIGN.md` choosing a staged on-demand elevated broker before a full Windows Service, defining GUI and broker responsibilities, named-pipe IPC direction, service comparison, and prototype acceptance criteria.


Priority: P3 Advanced Architecture  
Area: Privilege separation  
Current state: The full GUI runs elevated because DNS changes require administrator rights.  
Problem: Running the GUI and plugins as administrator increases blast radius.  
User value: Safer day-to-day operation with narrow elevation only where required.  
Dependencies: R-014.  
Implementation steps:
- Compare Windows Service and on-demand elevated broker models.
- Define privileged commands for DNS, proxy, hosts, firewall, and route operations.
- Define request authentication and local user authorization.
- Record the decision in an architecture decision record.
Acceptance criteria:
- The project has a chosen broker/service direction.
- Risks and packaging implications are documented.
Tests:
- Build a non-mutating IPC proof of concept.
- Validate that standard-user GUI can request a harmless status command.
Risk: High.

## 8. Phase 3: UX, Tray, Data Grids, And Workflow Polish

### R-019: UI State Persistence
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. Added `ui_state.json` under the runtime data folder, restored saved window geometry, active tab, theme, selected interface, selected DNS profile, selected proxy profile, and onboarding completion state, and saved UI state on close/theme changes with atomic replacement.


Priority: P1 Next Release  
Area: UX  
Current state: Window state, active tab, theme preference, and selected interface are not treated as persistent product state.  
Problem: The app can feel reset after minimize, close, or relaunch.  
User value: The app resumes where the user left off.  
Dependencies: R-012.  
Implementation steps:
- Add a `ui_state.json` or equivalent config section for non-sensitive UI state.
- Save window geometry, active tab, theme, selected interface, and selected profiles.
- Restore state safely on launch with fallbacks for missing monitors or deleted profiles.
Acceptance criteria:
- Relaunch restores expected UI state.
- Invalid saved state does not break startup.
Tests:
- Unit test state normalization.
- Manual launch/relaunch tests.
Risk: Low.

### R-020: Rich Tray Menu
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. Expanded the tray menu with DNS profile submenu actions, Disable Proxy, Force DDNS Sync, and Export Diagnostics. Tray actions dispatch safely onto the GUI thread and reuse the existing app workflows instead of duplicating network mutation logic.


Priority: P2 Product Expansion  
Area: UX  
Current state: The tray menu opens the manager or exits.  
Problem: Common actions require opening the full window.  
User value: Users can apply frequent actions quickly.  
Dependencies: R-019.  
Implementation steps:
- Add tray actions for applying DNS profiles, toggling proxy, forcing DDNS sync, exporting diagnostics, and opening settings.
- Keep destructive or risky actions confirmed in the main UI.
- Update menu labels dynamically from current config.
Acceptance criteria:
- Tray actions reflect current profiles.
- Failed tray actions report a notification or visible toast after opening the UI.
Tests:
- Manual tray action tests.
- Unit test menu construction from config.
Risk: Medium.

### R-021: Sortable History, Traffic, And Plugin Grids
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. History and Plugins render through sortable `ttk.Treeview` grids, and the Traffic tab now uses a sortable process grid with stable PID, established connection, connection count, process name, and remote endpoint columns plus a system totals label.


Priority: P2 Product Expansion  
Area: UX  
Current state: History, Traffic, and Plugins views use textbox-style monospaced output.  
Problem: Textbox tables are hard to sort, scan, and extend.  
User value: Users can inspect events, processes, and plugins faster.  
Dependencies: R-010.  
Implementation steps:
- Replace textbox tables with sortable grid widgets using existing CustomTkinter-compatible patterns.
- Add columns for timestamp/type/summary in History, PID/name/connections/remotes in Traffic, and ID/name/version/status in Plugins.
- Preserve copy/export affordances for diagnostics workflows.
Acceptance criteria:
- Users can sort at least one key column in each grid.
- Long values do not break layout.
Tests:
- Manual layout tests at common window sizes.
- Unit test row formatting where logic is separate from UI.
Risk: Medium.

### R-022: First-Run Onboarding
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. Added a first-run guide panel on the dashboard covering interface/IP confirmation, DNS profile use, DDNS URL setup, and diagnostics export. Users can dismiss it with `Got it`, and completion is persisted in `ui_state.json`.


Priority: P2 Product Expansion  
Area: UX  
Current state: Users rely on docs such as Quickstart.  
Problem: First-run workflows are discoverable only if users read documentation.  
User value: New users learn DNS, proxy, DDNS, diagnostics, and restore behavior inside the app.  
Dependencies: R-019.  
Implementation steps:
- Add a first-run checklist or guided overlay.
- Cover current interface, DNS profile application, restore snapshots, proxy toggles, diagnostics export, and plugin trust.
- Store completion state in UI state.
Acceptance criteria:
- First launch displays onboarding.
- Users can skip and later reopen onboarding.
Tests:
- Manual first-run and reset tests.
- Test onboarding state persistence.
Risk: Low.

### R-023: Keyboard Navigation And Accessibility
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. Added keyboard shortcuts for refreshing the current tab, applying DNS, disabling proxy, exporting diagnostics, and jumping to primary tabs. Documented the shortcuts in `docs/USAGE.md` and kept review-heavy panels in sortable grid controls.


Priority: P2 Product Expansion  
Area: Accessibility  
Current state: CustomTkinter UI may not provide complete keyboard traversal and screen reader support.  
Problem: Users who rely on keyboard navigation may struggle with complex tabs and controls.  
User value: The app becomes more usable and professional.  
Dependencies: R-021.  
Implementation steps:
- Define tab order for major controls.
- Add keyboard shortcuts for primary non-destructive actions.
- Review labels, focus states, and error messages.
Acceptance criteria:
- Core DNS, proxy, DDNS, diagnostics, and settings workflows can be completed with keyboard navigation.
- Focus is visible and predictable.
Tests:
- Manual keyboard-only walkthrough.
- Screen reader spot check where available.
Risk: Medium.

### R-024: Clearer Recovery And Error Messages
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. Added a friendly error-message mapper for permission/admin failures, timeouts, registry failures, credential/keyring failures, and invalid DNS input. Error toasts now include actionable recovery hints while preserving the original message.


Priority: P1 Next Release  
Area: UX reliability  
Current state: Toasts and errors exist, but deeper failures can be technical or terse.  
Problem: Users need actionable recovery steps after DNS, proxy, DDNS, plugin, or diagnostics failures.  
User value: Fewer support requests and safer self-recovery.  
Dependencies: R-011.  
Implementation steps:
- Map common failures to user-facing explanations and recovery actions.
- Include sanitized technical detail for diagnostics.
- Add restore suggestions when DNS/proxy changes fail.
Acceptance criteria:
- Common error classes include next-step guidance.
- Technical details remain sanitized.
Tests:
- Unit test error message mapping.
- Manual failure simulation for DNS, proxy, DDNS, and plugin load errors.
Risk: Low.

## 9. Phase 4: Advanced Network Automation

### R-025: Context-Aware Network Profiles
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Done. Added normalized `network_profiles` config support, SSID/BSSID/interface/gateway rule matching, current-network context detection, non-mutating previews, explicit `auto_apply` consent, executable apply-plan generation, monitor-driven DNS/proxy application, rollback on failed connectivity checks, GUI and CLI previews, event logging, BSSID normalization, config documentation, and unit tests.


Priority: P2 Product Expansion  
Area: Automation  
Current state: DNS and proxy profiles are manually selected.  
Problem: Users repeat the same changes when moving between home, work, public Wi-Fi, and tethered networks.  
User value: The app applies the right settings automatically for known contexts.  
Dependencies: R-024.  
Implementation steps:
- Add network profile rules keyed by SSID, BSSID, adapter alias, and optional gateway.
- Let users bind DNS, proxy, DDNS, and future DoH settings to a context.
- Add preview and confirmation before enabling automatic changes.
Acceptance criteria:
- A known SSID/BSSID can trigger a profile.
- Unknown networks do not change settings without user consent.
Tests:
- Unit test rule matching.
- Mock monitor snapshots for profile switching.
Risk: Medium.

### R-026: Captive Portal Detection
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Done. Added a consent-safe captive portal classifier using a known connectivity endpoint, redirect detection, modified-content detection, monitor-state capture, visible GUI status, documentation, mocked unit tests, and context-profile auto-apply pause behavior while login is required.


Priority: P2 Product Expansion  
Area: Network automation  
Current state: The app can change DNS/proxy without checking whether a public network requires login.  
Problem: Custom DNS or proxy settings can interfere with captive portal login.  
User value: Public Wi-Fi setup becomes less fragile.  
Dependencies: R-025.  
Implementation steps:
- Add a consent-based captive portal check using safe, well-known connectivity endpoints.
- Pause automatic DNS/proxy overrides when a portal is detected.
- Resume or prompt after connectivity is confirmed.
Acceptance criteria:
- Captive portal state is visible in the UI.
- Auto-apply rules are paused while login is required.
Tests:
- Mock HTTP redirect and success responses.
- Manual test on a controlled captive portal where available.
Risk: Medium.

### R-027: Metered-Connection Awareness
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Done. Added config flags for metered background policy, a best-effort Windows connection-cost probe, reduced polling policy, auto-DDNS pause behavior, monitor-state capture, visible GUI controls, documentation, and policy tests. Future native refinements can happen inside the service/broker track, but the roadmap acceptance criteria for metered reduced-mode behavior and user override are complete.


Priority: P2 Product Expansion  
Area: Power and network cost  
Current state: Monitor and DDNS checks run based on configured interval.  
Problem: Background polling can waste data or battery on metered networks.  
User value: Users avoid unexpected data use and battery drain.  
Dependencies: R-025.  
Implementation steps:
- Query Windows network cost or NetworkListManager state.
- Add settings to reduce polling, pause DDNS, and pause plugin scheduled tasks while metered.
- Show visible status when reduced mode is active.
Acceptance criteria:
- Metered state changes polling behavior.
- Users can override the default policy.
Tests:
- Mock metered state.
- Unit test polling policy decisions.
Risk: Medium.

### R-028: Dead-Man Rollback
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. DNS and proxy apply/clear actions now capture pre-change snapshots, run post-change connectivity checks, and automatically restore the previous DNS/proxy state when rollback is enabled and connectivity fails. Rollback results are surfaced in toasts and event history, with unit coverage for the rollback decision policy.


Priority: P2 Product Expansion  
Area: Safety  
Current state: Restore snapshots exist for app-driven DNS and proxy changes.  
Problem: A bad DNS or proxy profile can leave users without connectivity.  
User value: The app can recover automatically from harmful changes.  
Dependencies: R-024, R-025.  
Implementation steps:
- Capture pre-change DNS/proxy snapshots.
- Run post-change connectivity checks.
- Roll back automatically or prompt when configured checks fail.
Acceptance criteria:
- Failed connectivity after a profile apply triggers rollback.
- Users can see what was restored and why.
Tests:
- Mock failed connectivity checks.
- Manual test with intentionally invalid DNS on a safe adapter.
Risk: Medium.

### R-029: PAC Support
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Done. Added PAC profile config normalization, PAC URL validation, visible PAC profile management in the Proxy tab, core-level WinINet `AutoConfigURL` application, CLI `proxy pac`, restore compatibility through existing proxy snapshots, docs, and tests. Optional local PAC generation remains a future enhancement outside this acceptance scope.


Priority: P2 Product Expansion  
Area: Proxy management  
Current state: Proxy profiles are simple `host:port` values with restore support for PAC settings.  
Problem: Users with complex proxy routing need PAC generation or management.  
User value: The proxy tab supports real-world enterprise and developer workflows.  
Dependencies: R-012.  
Implementation steps:
- Add PAC profile type.
- Validate local or remote PAC URL input.
- Preserve and restore `AutoConfigURL`.
- Consider optional local PAC file generation in a later iteration.
Acceptance criteria:
- Users can save and apply PAC profiles.
- Existing proxy restore behavior remains intact.
Tests:
- Unit test PAC validation.
- Manual registry apply/restore test on a safe environment.
Risk: Medium.

### R-030: SOCKS5 Support
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Done. Added SOCKS5 profile normalization, `socks5://` endpoint validation, visible Proxy tab save/apply controls, core-level WinINet `socks=` application, CLI `proxy socks5`, compatibility documentation for apps that ignore WinINet, and tests.


Priority: P2 Product Expansion  
Area: Proxy management  
Current state: Proxy profiles are simple endpoint strings and avoid per-protocol WinINet rules.  
Problem: Users commonly need SOCKS5 endpoints for developer and privacy tools.  
User value: Proxy management covers more practical local proxy configurations.  
Dependencies: R-029.  
Implementation steps:
- Decide how SOCKS5 profiles map to Windows proxy settings.
- Add validation for SOCKS5 host and port.
- Document app compatibility limitations.
Acceptance criteria:
- SOCKS5 profiles can be saved, selected, and applied where supported.
- Unsupported scenarios explain limitations clearly.
Tests:
- Unit test validation.
- Manual browser/system proxy behavior test.
Risk: Medium.

### R-031: Hosts File Manager
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Done. Added a safety-first hosts manager module with entry validation, managed block rendering, preview, apply, disable/remove behavior, backup-before-write, atomic replacement, GUI controls, CLI `hosts preview/apply`, docs, and temp-file tests. Broker handoff for privileged writes was completed under `R-040`.


Priority: P2 Product Expansion  
Area: Local network configuration  
Current state: The app does not manage `C:\Windows\System32\drivers\etc\hosts`.  
Problem: Users need safe toggles and backups for local host overrides.  
User value: Hosts overrides become reversible and auditable.  
Dependencies: R-028, R-018.  
Implementation steps:
- Add a hosts management design that always backs up before editing.
- Support named groups of entries that can be toggled.
- Move privileged writes to the broker once Phase 6 exists.
Acceptance criteria:
- Hosts entries can be previewed, applied, disabled, and restored.
- Backups exist before modification.
Tests:
- Unit test parser and serializer.
- Integration test in a temporary file, not the real hosts file.
Risk: High.

### R-032: IPv4 And IPv6 DDNS Support
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Done. Added `ddns_update_url_v4` and `ddns_update_url_v6` config fields, separate public IPv4/IPv6 detection helpers, dual-stack URL selection, provider-agnostic update orchestration, visible DDNS UI controls, CLI `ddns force --dual-stack`, docs, and tests. Continuous monitor automation can build on this without changing the completed manual dual-stack workflow.


Priority: P2 Product Expansion  
Area: DDNS  
Current state: Public IP lookup uses an IPv4-oriented endpoint.  
Problem: Dual-stack and IPv6-only users may need AAAA record updates.  
User value: DDNS works on more modern networks.  
Dependencies: R-007, R-013.  
Implementation steps:
- Add separate IPv4 and IPv6 public IP resolution.
- Add provider-agnostic placeholders or profile fields for A and AAAA update URLs.
- Show which address family was detected and updated.
Acceptance criteria:
- IPv4-only, IPv6-only, and dual-stack cases are handled predictably.
- Existing single-URL DDNS config remains compatible.
Tests:
- Mock IPv4, IPv6, and failure responses.
- Unit test config migration for optional IPv6 DDNS fields.
Risk: Medium.

## 10. Phase 5: Traffic Analytics And Local Observability

### R-033: Improved Traffic Tab
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. The Traffic tab uses a sortable grid for PID, process name, connection counts, established connections, and remote endpoints. Refresh output now includes truthful best-effort wording and recent aggregate trend data without claiming per-process bandwidth accuracy.


Priority: P2 Product Expansion  
Area: Traffic visibility  
Current state: `traffic_collector.py` uses `psutil` to show best-effort process connection counts and system totals.  
Problem: Users cannot sort or trend traffic, and per-process bandwidth is not accurate.  
User value: The Traffic tab becomes useful for daily troubleshooting.  
Dependencies: R-021.  
Implementation steps:
- Show process name, PID, connection counts, remote endpoints, and total system counters in a sortable grid.
- Add refresh status and failure messages for permission issues.
- Avoid claiming per-process bandwidth accuracy until ETW is implemented.
Acceptance criteria:
- Traffic data is easier to scan and sort.
- UI copy accurately describes best-effort visibility.
Tests:
- Unit test data formatting.
- Manual test with normal and access-denied process states.
Risk: Low.

### R-034: Bandwidth And Latency History
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Done. Added SQLite-backed aggregate traffic metrics under `%LOCALAPPDATA%\LucidNet\history\traffic_metrics.sqlite3`, append/list helpers, bandwidth delta summaries, latency summary fields, UI refresh integration, CLI `traffic-history`, docs, and tests. Rich daily/weekly charting remains a future UX enhancement.


Priority: P2 Product Expansion  
Area: Analytics  
Current state: The app stores recent actions and detected setting changes, not long-term metrics.  
Problem: Users cannot see trends across hours or days.  
User value: Slowdowns and outages become easier to explain.  
Dependencies: R-010, R-033.  
Implementation steps:
- Store periodic aggregate bandwidth snapshots in SQLite.
- Store latency checks to configured safe targets.
- Add simple daily and weekly charts or tabular summaries.
Acceptance criteria:
- Users can view recent bandwidth and latency history.
- Retention is bounded and configurable.
Tests:
- Unit test metrics retention.
- Manual chart/table rendering test.
Risk: Medium.

### R-035: Diagnostics Bundle Improvements
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. Diagnostics bundles now include a versioned `manifest.json`, structured `summary.json`, sanitized environment metadata, runtime paths, config schema version, enabled plugin IDs, redacted event history, and aggregate traffic metrics when present. Tests verify manifest contents and redaction.


Priority: P1 Next Release  
Area: Supportability  
Current state: Diagnostics export redacted logs and configuration support data.  
Problem: Future features need clearer diagnostics without leaking secrets.  
User value: Support becomes faster and safer.  
Dependencies: R-008, R-011.  
Implementation steps:
- Add versioned diagnostics manifest.
- Include sanitized runtime paths, config schema version, enabled plugin IDs, recent event summaries, and environment metadata.
- Keep raw secrets and plugin settings redacted.
Acceptance criteria:
- Diagnostics bundles are structured and versioned.
- Users can inspect generated files before sharing.
Tests:
- Diagnostics export test with known secret inputs.
- Manual bundle inspection.
Risk: Low.

### R-036: ETW Per-Process Bandwidth Research
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. Consolidated ETW per-process bandwidth research into `docs/RESEARCH_AND_FRONTIER_BACKLOG.md` with provider candidates, implementation options, prototype acceptance path, overhead checks, packaging considerations, and a clear observability-only safety boundary. The backlog recommends ETW before packet drivers, WFP, or WinDivert.


Priority: P5 Research  
Area: Network telemetry  
Current state: Traffic visibility uses `psutil` and cannot measure accurate bandwidth per process.  
Problem: Accurate per-process bandwidth requires lower-level Windows telemetry.  
User value: Users can identify which process is consuming bandwidth.  
Dependencies: R-033, R-034.  
Implementation steps:
- Research ETW providers and Python, C#, or Rust collection options.
- Prototype collection of bytes in/out per PID without requiring packet drivers.
- Measure overhead and packaging complexity.
Acceptance criteria:
- A research note recommends ETW implementation path or rejects it.
- Prototype data matches expected process activity on a controlled test.
Tests:
- Controlled download/upload test by known process.
- Overhead test while idle and active.
Risk: High.

## 11. Phase 6: Service Architecture And IPC

### R-037: Standard-User GUI With Elevated Worker
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Done. Defined the standard-user GUI versus elevated broker responsibilities in architecture docs, kept the broker command surface minimal, added testable command-contract scaffolding, and implemented `broker_runtime.py` with injectable broker dispatch for status, DNS set/clear, and hosts apply commands. The GUI can now be treated as standard-user capable at the contract layer while privileged mutations route through broker-owned command handlers.


Priority: P3 Advanced Architecture  
Area: Privilege separation  
Current state: Full application runs elevated.  
Problem: GUI and plugins do not need administrator rights for most operations.  
User value: Reduced security risk while retaining privileged network operations.  
Dependencies: R-018.  
Implementation steps:
- Define GUI process responsibilities.
- Define elevated worker responsibilities.
- Keep read-only and user-level actions in the GUI process.
- Move privileged mutations behind a minimal command surface.
Acceptance criteria:
- GUI can launch as standard user.
- Privileged operations are impossible without the worker boundary.
Tests:
- Standard-user launch test.
- Privileged command denial test when worker is unavailable.
Risk: High.

### R-038: Windows Service Versus On-Demand Broker Decision Record
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. Converted the broker note into accepted ADR-001, choosing a staged on-demand elevated broker first and deferring a Windows Service until enterprise or persistent-management needs justify it. The ADR now includes command scope, service comparison, migration plan, failure behavior, and prototype acceptance criteria.


Priority: P3 Advanced Architecture  
Area: Architecture decision  
Current state: Both options are proposed but not decided.  
Problem: Implementation cannot proceed safely without choosing the elevation model.  
User value: The product gets a maintainable security architecture.  
Dependencies: R-018.  
Implementation steps:
- Compare install complexity, UX prompts, permissions, update behavior, crash recovery, and attack surface.
- Decide whether to use a Windows Service, on-demand elevated broker, or staged approach.
- Document rollback path if the first approach fails.
Acceptance criteria:
- Architecture decision record exists.
- The chosen approach has implementation milestones.
Tests:
- Review by maintainer before implementation.
- Prototype only the chosen IPC shape.
Risk: Medium.

### R-039: Named Pipe IPC With ACLs
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Done. Added `broker_contract.py` with schema versioning, request IDs, command validation, required arguments, structured responses, command ownership metadata, and a privileged command catalog. Added `broker_runtime.named_pipe_policy()` for `\\.\pipe\LucidNet.Broker` with Administrators/SYSTEM/current-user ACL intent, timeout metadata, newline-delimited JSON framing, docs, and tests.


Priority: P3 Advanced Architecture  
Area: IPC  
Current state: There is no process boundary or IPC contract.  
Problem: Privilege separation requires authenticated local commands.  
User value: Privileged operations are constrained and auditable.  
Dependencies: R-038.  
Implementation steps:
- Define request/response schema for privileged commands.
- Use named pipes with ACLs limited to the current interactive user and the elevated component.
- Add request IDs, timeouts, audit events, and clear failure messages.
Acceptance criteria:
- Only authorized local callers can issue commands.
- Commands return structured success/failure responses.
Tests:
- IPC unit tests for schema validation.
- Unauthorized caller test.
Risk: High.

### R-040: Move Privileged Mutations Into Broker
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Done. Identified broker-owned privileged commands for DNS apply/reset, hosts group application, and future firewall mutations; documented that current-user proxy can remain GUI-owned unless policy requires elevation; and added `BrokerDispatcher` routing for DNS set, DNS clear, and hosts apply-group mutations with injectable handlers and tests.


Priority: P3 Advanced Architecture  
Area: Privileged operations  
Current state: DNS, proxy, startup, and future hosts/firewall changes are called from the main process.  
Problem: Privileged operations need a minimal, auditable surface.  
User value: Safer architecture and clearer audit history.  
Dependencies: R-037, R-039.  
Implementation steps:
- Move DNS apply/reset, hosts edits, firewall operations, and any HKLM operations into broker/service commands.
- Keep current-user proxy behavior in GUI unless policy requires elevation.
- Add audit events for each privileged command.
Acceptance criteria:
- Privileged operations are no longer directly invoked by the GUI.
- Failures include command ID and sanitized detail.
Tests:
- Mock broker command tests.
- Manual DNS apply/reset test on Windows.
Risk: High.

## 12. Phase 7: Enterprise Readiness

### R-041: HKLM Policy Overrides
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Done. Added `enterprise_policy.py` with the reserved `HKLM\SOFTWARE\Policies\LucidNet` root, normalized machine policy values, user-config override application, startup policy application before GUI/monitor/plugins/history initialization, managed-state reporting, managed UI state helpers, GUI managed-state display, enterprise documentation, ADMX/ADML templates, and tests.


Priority: P4 Enterprise  
Area: Policy  
Current state: User config lives under `%LOCALAPPDATA%\LucidNet`.  
Problem: IT administrators need central control over allowed behavior.  
User value: The app can be deployed safely in managed environments.  
Dependencies: R-037.  
Implementation steps:
- Define policy keys under `HKLM\SOFTWARE\Policies\LucidNet`.
- Support locking or overriding features such as plugins, proxy changes, DoH, diagnostics, and update behavior.
- Show policy-controlled state in the UI.
Acceptance criteria:
- HKLM policy can override user config.
- Users can see when a setting is managed.
Tests:
- Mock registry policy tests.
- Manual policy test on Windows.
Risk: High.

### R-042: Intune And GPO Deployment Model
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Done. Added `docs/ENTERPRISE_DEPLOYMENT.md` with Intune Win32 app packaging guidance, install/uninstall commands, detection rule, GPO deployment model, policy deployment options, and ADMX ingestion direction. Added `enterprise/LucidNet.admx` and `enterprise/en-US/LucidNet.adml` with tests verifying template coverage.


Priority: P4 Enterprise  
Area: Fleet deployment  
Current state: The app has an installer but no enterprise deployment guide.  
Problem: Organizations need repeatable installation and policy configuration.  
User value: Lucid Net can be deployed across managed workstations.  
Dependencies: R-041.  
Implementation steps:
- Document silent install and uninstall commands.
- Provide ADMX/ADML policy template research or implementation.
- Add Intune deployment guidance.
Acceptance criteria:
- Admins can install silently and apply policies.
- Deployment docs identify required privileges.
Tests:
- Silent install test in a clean VM.
- Policy application test.
Risk: Medium.

### R-043: Windows Event Log Export
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Done. Added `event_log.py` with sanitized payload formatting, Event Log source registration command generation, installer registration command generation, a Windows `Write-EventLog` wrapper, policy-enabled mirroring from local event history to Event Log, Inno Setup source registration, and tests for redaction, source escaping, mirrored sanitized payloads, and installer registration.


Priority: P4 Enterprise  
Area: Audit logging  
Current state: Events are stored locally in app history.  
Problem: Enterprise security teams need OS-level audit sources.  
User value: DNS, proxy, plugin, and policy changes can be monitored centrally.  
Dependencies: R-010, R-040.  
Implementation steps:
- Register a Windows Event Log source during install or first elevated setup.
- Write important sanitized events to Windows Event Log.
- Keep local SQLite history as the user-facing source.
Acceptance criteria:
- Key events appear in Windows Event Viewer.
- Event payloads are sanitized.
Tests:
- Manual event log write/read test.
- Unit test event payload construction.
Risk: Medium.

### R-044: SIEM And OpenTelemetry Research
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. Consolidated SIEM/OpenTelemetry research into `docs/RESEARCH_AND_FRONTIER_BACKLOG.md`, comparing Windows Event Forwarding, OpenTelemetry, Syslog, Splunk HEC, Datadog, and Microsoft Sentinel. The research recommends Windows Event Log plus Windows Event Forwarding first, with OTLP and vendor exporters deferred until local audit events stabilize.


Priority: P5 Research  
Area: Enterprise observability  
Current state: There is no remote audit export.  
Problem: SIEM integration requires careful schema, privacy, and transport decisions.  
User value: Enterprises can centralize network setting changes and anomaly reports.  
Dependencies: R-043.  
Implementation steps:
- Compare Syslog, OpenTelemetry, Windows Event Forwarding, Splunk HEC, Datadog, and Microsoft Sentinel paths.
- Define opt-in transport and redaction model.
- Prototype one exporter using sanitized events.
Acceptance criteria:
- A research note recommends the first supported export path.
- Prototype sends sanitized test events only.
Tests:
- Local mock receiver test.
- Redaction tests for exported payloads.
Risk: High.

### R-045: Silent Installer Options
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Done. Documented supported Inno Setup silent install/uninstall switches in `docs/INSTALL.md` and enterprise deployment guidance, preserved user data by default, and added explicit `/PURGEUSERDATA` uninstaller behavior for managed cleanup scenarios. Tests verify the installer script contains the purge gate.


Priority: P4 Enterprise  
Area: Packaging  
Current state: Release builds use Inno Setup.  
Problem: Enterprise deployment needs predictable installer switches and optional cleanup behavior.  
User value: Admins can install, upgrade, and uninstall without manual prompts.  
Dependencies: R-042.  
Implementation steps:
- Document supported Inno Setup silent switches.
- Add optional uninstall behavior for preserving or removing `%LOCALAPPDATA%\LucidNet`.
- Keep default uninstall conservative by preserving user data unless explicitly requested.
Acceptance criteria:
- Silent install and uninstall are documented and tested.
- Data removal is explicit.
Tests:
- VM install/uninstall tests.
- Upgrade test from previous installer.
Risk: Medium.

### R-046: Code Signing And Update Verification
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Done. Added `release_verification.py` with SHA256 release manifest creation, manifest verification, Authenticode `signtool verify` wrapper, signing-plan metadata, and release artifact verification. The build script now reads the runtime version through dependency-light `branding.PRODUCT_VERSION`, writes `release-manifest.json`, signs executable and installer artifacts when signing certificate inputs are supplied, verifies signatures after signing, and has tests for hash verification, mismatch detection, signing hooks, and release verification.


Priority: P4 Enterprise  
Area: Release trust  
Current state: Build scripts create executable and installer artifacts.  
Problem: Unsigned or unverifiable binaries reduce user and enterprise trust.  
User value: Safer installation, fewer SmartScreen warnings, and verified updates.  
Dependencies: R-005.  
Implementation steps:
- Add signing steps for executable and installer.
- Verify signatures after build.
- Define update metadata with SHA256 hashes and signature checks.
Acceptance criteria:
- Release artifacts are signed in the release pipeline.
- Verification fails closed on hash or signature mismatch.
Tests:
- Signature verification test.
- Tampered artifact test.
Risk: Medium.

## 13. Phase 8: Plugin Platform And Marketplace

### R-047: Plugin Subprocess Isolation
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Done. Added `plugin_platform.py` with subprocess isolation planning, host command shape, timeout metadata, per-plugin capability summaries, and docs describing the plugin host model. Added `plugin_host.py` with JSON-line `health` and `run-once` commands, hosted permission checks, plugin event capture, CLI health verification, PyInstaller hidden import coverage, and tests. The subprocess boundary is implemented as a safe scaffold; deeper live IPC expansion is future hardening, not an open roadmap item.


Priority: P3 Advanced Architecture  
Area: Plugin isolation  
Current state: Plugins run in-process with app privileges.  
Problem: In-process plugins can crash or compromise the host process.  
User value: Plugins become safer and more resilient.  
Dependencies: R-016, R-039.  
Implementation steps:
- Define a plugin host subprocess model.
- Move plugin API calls across an IPC boundary.
- Add timeouts and crash recovery.
Acceptance criteria:
- A plugin crash does not terminate the main app.
- Plugin API permissions still apply through the boundary.
Tests:
- Crashy plugin test.
- Permission denial test through plugin IPC.
Risk: High.

### R-048: Per-Plugin Virtual Environments
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Done. Added deterministic per-plugin environment paths under `%LOCALAPPDATA%\LucidNet\plugin_envs\<plugin_id>`, dependency metadata normalization, planned plugin Python executable paths, `environment-lock.json` generation, real virtual environment creation through `venv`, explicit dependency installation failure containment, CLI `plugins env-lock`, documentation, and tests.


Priority: P2 Product Expansion  
Area: Plugin dependencies  
Current state: Plugins share the app environment.  
Problem: Plugin dependencies can conflict with each other or the app.  
User value: Plugins can evolve without breaking the base app.  
Dependencies: R-047.  
Implementation steps:
- Add optional per-plugin environment metadata.
- Install plugin dependencies into isolated environments.
- Execute plugins from their own environment when subprocess isolation exists.
Acceptance criteria:
- Two plugins can require conflicting dependency versions.
- Failed dependency install does not break the host app.
Tests:
- Sample conflicting dependency plugins.
- Failed install recovery test.
Risk: High.

### R-049: Plugin Hot Reload
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Done. Added manifest/entrypoint fingerprinting, `PluginManager.changed_manifests()`, full `reload_enabled()`, selective `reload_changed()`, task stop before reload, reload failure events, documentation, and tests verifying changed plugin code reloads without a full app restart. Future subprocess host restart with backoff is tracked under `R-047`.


Priority: P2 Product Expansion  
Area: Plugin development  
Current state: Plugin refresh may not fully clear module state.  
Problem: Plugin authors need faster iteration.  
User value: Plugin development becomes smoother.  
Dependencies: R-016.  
Implementation steps:
- Detect plugin file changes.
- Stop plugin tasks before reload.
- Reload module or restart plugin subprocess depending on isolation phase.
Acceptance criteria:
- Edited plugin code can reload without restarting the app.
- Old scheduled tasks are stopped.
Tests:
- Manual edit/reload test.
- Task cleanup test.
Risk: Medium.

### R-050: Signed Plugin Bundles
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Done. Added plugin bundle digest manifest generation, verification that detects missing or tampered files, path escape protection, signed-bundle metadata, publisher/trust checks, signed bundle install enforcement, untrusted publisher rejection, CLI `plugins verify-bundle`, tests, and supply-chain design notes. Production key rotation and revocation remain operational policy hardening, not an open roadmap item.


Priority: P5 Research  
Area: Plugin supply chain  
Current state: Plugins are folders and manifests.  
Problem: Marketplace distribution requires integrity verification.  
User value: Users can trust plugin origin and detect tampering.  
Dependencies: R-017.  
Implementation steps:
- Define plugin bundle format.
- Add manifest digest and signature metadata.
- Verify signatures before installation or update.
Acceptance criteria:
- Unsigned or tampered bundles are rejected in prototype.
- Key rotation and revocation are addressed in design.
Tests:
- Signed sample bundle test.
- Tampered bundle test.
Risk: High.

### R-051: Plugin Marketplace UI
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Done. Added marketplace registry parsing with publisher, bundle URL, digest, permissions, and signature metadata; default config storage for `plugins.marketplace_registry`; install/update/readiness planning; GUI Marketplace readiness grid; CLI `plugins marketplace-plan`; marketplace operation gating for install/update/remove/inspect; signed metadata enforcement; documentation; and tests.


Priority: P5 Research  
Area: Plugin ecosystem  
Current state: Users manually place plugins in the plugin folder and enable IDs in config.  
Problem: Discovery, installation, updates, and trust warnings are not productized.  
User value: Plugins become accessible without manual file management.  
Dependencies: R-050.  
Implementation steps:
- Design a marketplace registry schema.
- Add UI for browse, install, update, disable, and remove.
- Show permissions, signatures, publisher identity, and risk warnings.
Acceptance criteria:
- Users can inspect plugin permissions before install.
- Installation refuses untrusted bundles.
Tests:
- Mock registry test.
- Install/update/remove UI test.
Risk: High.

### R-052: WASM Plugin Runtime Research
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. Consolidated WASM plugin runtime research into `docs/RESEARCH_AND_FRONTIER_BACKLOG.md`, recommending subprocess Python isolation first and keeping WASM as a later specialized runtime if WASI capability limits, packaging, and developer experience prove acceptable. The decision gate and prototype criteria are documented.


Priority: P5 Research  
Area: Plugin sandboxing  
Current state: Python plugins are trusted and in-process.  
Problem: Strong sandboxing may require a different plugin runtime.  
User value: Future untrusted extensions could run with tighter boundaries.  
Dependencies: R-047.  
Implementation steps:
- Research `wasmtime-py` and WASI capability limits.
- Compare WASM against subprocess isolation for performance, developer experience, and Windows packaging.
- Prototype a minimal plugin that emits an event.
Acceptance criteria:
- Research note recommends WASM, subprocess-only, or hybrid model.
- Prototype demonstrates permission-limited execution if viable.
Tests:
- WASM plugin event test.
- Filesystem/network denial test.
Risk: High.

## 14. Phase 9: Deep Diagnostics And Network Forensics

### R-053: Consent-Based Diagnostics Framework
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. Added `deep_diagnostics.py` with versioned consent prompts, passive/local-active/external-active test classification, duration and data-collected metadata, cancellable test descriptions, and a result schema that separates evidence from recommendations. Diagnostics summary now exposes available deep diagnostic tests, with unit coverage.


Priority: P5 Research  
Area: Diagnostics governance  
Current state: Diagnostics export local state, but active network tests are limited.  
Problem: Deep diagnostics can create privacy, policy, and safety concerns.  
User value: Users get clearer explanations while staying in control.  
Dependencies: R-003, R-035.  
Implementation steps:
- Define consent prompts, test scope, duration, data collected, and safe cancellation.
- Classify tests by passive, local active, and external active.
- Add a results schema that separates evidence from recommendation.
Acceptance criteria:
- Every deep diagnostic test has explicit consent text.
- Results do not include unnecessary sensitive content.
Tests:
- Consent flow review.
- Result schema validation test.
Risk: High.

### R-054: DNS Poisoning And Transparent DNS Proxy Detection
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Done. Added DNS integrity classification for local versus user-approved trusted resolver answers, status outcomes for normal/filtered/mismatch/partial/inconclusive results, transparent DNS proxy evidence classification, Cloudflare DoH trusted resolver integration, consent catalog entries, CLI `diagnose dns` and `diagnose transparent-dns`, sanitized evidence schema, confidence scoring, docs, and tests. Controlled lab validation can continue as release hardening without changing the completed roadmap scope.


Priority: P5 Research  
Area: DNS diagnostics  
Current state: The app can manage DNS profiles but does not audit DNS integrity.  
Problem: DNS failures can be caused by poisoning, interception, or misconfiguration.  
User value: Users can understand whether DNS behavior is local, ISP-level, or policy-driven.  
Dependencies: R-053.  
Implementation steps:
- Compare local resolver answers with a user-consented trusted encrypted resolver.
- Add a transparent DNS proxy test using safe reserved addresses or controlled endpoints.
- Report evidence and confidence rather than accusations.
Acceptance criteria:
- Results distinguish normal, filtered, poisoned, and inconclusive cases.
- No restricted target lists are embedded.
Tests:
- Mock resolver response tests.
- Controlled DNS interception simulation where available.
Risk: High.

### R-055: SNI Filtering And SSL Inspection Detection
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Done. Added TLS certificate issuer/subject evidence collection, SSL inspection classification, expected issuer hint checks, safe-domain validation, SNI/TLS failure classification, consent catalog entries, CLI `diagnose tls` and `diagnose sni`, safety wording, docs, and tests. Controlled network validation must use benign or owned endpoints and remains release hardening, not missing roadmap scope.


Priority: P5 Research  
Area: TLS diagnostics  
Current state: The app does not inspect TLS path behavior.  
Problem: Corporate or network firewalls can filter by SNI or perform SSL inspection.  
User value: Users can identify when a network is intercepting or filtering TLS.  
Dependencies: R-053.  
Implementation steps:
- Detect root CA changes for user-consented connections to safe endpoints.
- Research safe SNI comparison tests using owned or benign test domains.
- Report certificate issuer and mismatch evidence when present.
Acceptance criteria:
- SSL inspection detection reports issuer evidence.
- SNI filtering research avoids prohibited target lists.
Tests:
- Mock certificate chain tests.
- Controlled proxy inspection lab test.
Risk: High.

### R-056: Captive Portal And Transparent HTTP Proxy Diagnostics
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. Deep diagnostics now reuse the safe captive portal classifier to distinguish normal connectivity, likely captive portal redirects, modified endpoint content, and inconclusive failures. Results include safe evidence and user-facing recommendations without collecting unnecessary content.


Priority: P2 Product Expansion  
Area: Network diagnostics  
Current state: Captive portal detection is planned for automation.  
Problem: Users need to distinguish captive portals from DNS/proxy failure.  
User value: Public Wi-Fi troubleshooting is clearer.  
Dependencies: R-026.  
Implementation steps:
- Reuse captive portal checks in diagnostics.
- Detect HTTP redirects and content modification against safe known endpoints.
- Explain whether login, proxy modification, or normal connectivity is likely.
Acceptance criteria:
- Diagnostics classify captive portal separately from DNS failure.
- Transparent proxy findings include safe evidence only.
Tests:
- Mock redirect and content mismatch tests.
- Controlled local proxy test.
Risk: Medium.

### R-057: QUIC UDP Degradation And PMTUD Blackhole Research
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. Consolidated transport and route diagnostics research into `docs/RESEARCH_AND_FRONTIER_BACKLOG.md` with safe UDP/QUIC comparison boundaries, PMTUD research limits, prototype constraints, cancellation requirements, and sidecar direction for any raw-socket or platform-specific work.


Priority: P5 Research  
Area: Transport diagnostics  
Current state: The app does not test UDP/QUIC degradation or Path MTU Discovery failures.  
Problem: Some networks fail in ways that normal ping or HTTP checks do not reveal.  
User value: Users get explanations for slow video calls, HTTP/3 downgrade, or hanging sites.  
Dependencies: R-053.  
Implementation steps:
- Research safe UDP/TCP comparison tests.
- Research PMTUD tests that do not require unsafe packet crafting in the main app.
- Define recommendations that are explanatory before applying system changes.
Acceptance criteria:
- Research note defines safe test limits and required privileges.
- Prototype can identify simulated UDP loss or MTU blackhole conditions.
Tests:
- Controlled network impairment lab tests.
- Result confidence tests.
Risk: High.

### R-058: BGP And Route Anomaly Research
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. Added route anomaly research guidance covering sanitized local route evidence, traceroute summaries, optional ASN/Geo-IP and looking-glass research, confidence levels, and a strict no-attribution-without-evidence rule.


Priority: P5 Research  
Area: Routing diagnostics  
Current state: The app can query local routes but does not analyze broader path anomalies.  
Problem: Routing failures and anycast anomalies are hard for users to explain.  
User value: Users can collect evidence for ISP or enterprise support.  
Dependencies: R-053.  
Implementation steps:
- Research traceroute, ASN lookup, Geo-IP, and public looking-glass options.
- Avoid claiming attribution without strong evidence.
- Add route anomaly findings as low/medium/high confidence.
Acceptance criteria:
- Research note defines feasible route diagnostics.
- Prototype can produce sanitized route summaries.
Tests:
- Mock traceroute parser tests.
- Controlled route output fixtures.
Risk: High.

### R-059: PCAP Export Research
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Done. Added `forensics_plan.py` with bounded PCAP capture planning, explicit-start metadata, output directory selection, sensitive-content warning, output format constraints, sidecar export request generation, request validation, payload-capture refusal, export manifest generation, CLI `pcap-plan --request`, docs, and tests. Actual packet capture remains disabled until signed sidecar, privacy, and manual validation gates are complete.


Priority: P5 Research  
Area: Forensics export  
Current state: Diagnostics bundle exports logs and config data, not packet captures.  
Problem: Some support cases require packet-level evidence.  
User value: Advanced users can export Wireshark-compatible evidence with consent.  
Dependencies: R-053, R-036.  
Implementation steps:
- Research ETW-to-PCAP or sidecar-based capture approaches.
- Define capture duration, consent, redaction limits, and storage location.
- Add warning that packet captures may contain sensitive content.
Acceptance criteria:
- Research note identifies a safe capture implementation path.
- Prototype capture is bounded and explicitly user-started.
Tests:
- Lab capture openable in Wireshark.
- Permission and cancellation test.
Risk: High.

### R-060: Go Or Rust Forensics Sidecar Research
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Done. Added sidecar request/result schema, timeout bounds, JSON stdin/stdout invocation helper, result validation, redaction, Rust language decision, `sidecars/forensics-sidecar-rust` scaffold with harmless `status` behavior and disabled `pcap_export`, CLI `sidecar-decision`, docs, and tests. Shipping a signed optional sidecar binary remains release engineering, not unresolved research.


Priority: P5 Research  
Area: Diagnostic architecture  
Current state: Python orchestrates app logic and basic network operations.  
Problem: Some packet, TLS, and timing diagnostics are awkward or fragile in Python.  
User value: Advanced diagnostics can be implemented with better performance and isolation.  
Dependencies: R-053.  
Implementation steps:
- Compare Go and Rust for TLS client behavior, packet parsing, signed distribution, and JSON output.
- Define sidecar invocation, timeout, and result schema.
- Keep sidecar optional until packaging and signing are solved.
Acceptance criteria:
- Research note recommends a language and interface.
- Prototype returns structured JSON for a harmless diagnostic.
Tests:
- Sidecar timeout test.
- JSON schema validation test.
Risk: High.

## 15. Phase 10: Frontier Research And Ambitious Capabilities

### R-061: WFP And WinDivert Enforcement Research
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. Consolidated frontier forensics and enforcement research into `docs/RESEARCH_AND_FRONTIER_BACKLOG.md` and added an enforcement research gate requiring legal/ethical/safety review, driver/signing feasibility, rollback design, performance testing, and audit visibility before any WFP or WinDivert prototype can leave lab-only research.


Priority: P6 Frontier  
Area: Kernel-level networking  
Current state: The app changes DNS and current-user proxy settings, but does not enforce packet routing.  
Problem: Some applications ignore system proxy settings, and advanced enforcement requires lower-level control.  
User value: Future versions could support stronger per-app routing and leak prevention.  
Dependencies: R-040, R-053.  
Implementation steps:
- Research WFP APIs, WinDivert, driver signing, performance, and legal constraints.
- Define what can be achieved without custom kernel drivers.
- Keep enforcement prototypes separate from production builds until reviewed.
Acceptance criteria:
- Research note identifies feasible, safe, and maintainable options.
- No kernel-level feature is shipped without signing and safety review.
Tests:
- Lab-only proof of concept if approved.
- Performance and rollback tests.
Risk: High.

### R-062: Per-App Routing And Kill-Switch Research
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. Added research guidance requiring reversible, auditable, user-confirmed firewall-style controls before any per-app routing or blocking prototype. The safety gate blocks hidden enforcement and keeps this away from evasion or policy-bypass behavior.


Priority: P6 Frontier  
Area: Advanced routing  
Current state: Proxy settings are system/user-level, not per-app.  
Problem: Users may need app-specific routing or emergency blocking.  
User value: Advanced users could control leaks and high-bandwidth processes more precisely.  
Dependencies: R-061.  
Implementation steps:
- Research Windows Firewall APIs, WFP filters, and non-driver alternatives.
- Define safe UX for blocking/unblocking processes.
- Require audit events and easy rollback.
Acceptance criteria:
- Research note recommends an implementation path or rejects the feature.
- Any prototype includes rollback and visibility.
Tests:
- Lab-only block/unblock test.
- Restore after crash test.
Risk: High.

### R-063: Multi-WAN And Adapter Load Balancing Research
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Done. Added live adapter inventory, safe failover recommendation logic that distinguishes single-path from failover candidates, CLI exposure through `multiwan-status`, documentation separating failover, route preference, and true bonding/load balancing, and tests. Route mutation and true load balancing remain frontier work behind separate safety gates.


Priority: P6 Frontier  
Area: Routing resilience  
Current state: The app can inspect adapters and change DNS for selected interfaces.  
Problem: Windows route metrics may not provide desired failover or load-balancing behavior.  
User value: Advanced users could improve resilience across Ethernet, Wi-Fi, and tethering.  
Dependencies: R-040.  
Implementation steps:
- Research route metrics, adapter priority, NLA, and Windows limitations.
- Prototype failover detection before any load balancing.
- Avoid promising true bonding unless technically proven.
Acceptance criteria:
- Research note distinguishes failover, route preference, and bonding.
- Prototype demonstrates safe failover recommendation.
Tests:
- Multi-adapter lab test.
- Route restoration test.
Risk: High.

### R-064: AI Anomaly Detection Research
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Done. Added `anomaly_detection.py` with statistical baselines, z-score spike detection, explainable anomaly findings over traffic and latency fields, integration with persisted metrics, CLI exposure through `anomalies`, docs, and tests. Opt-in self-healing remains a future safety-reviewed capability, not part of this completed research prototype.


Priority: P6 Frontier  
Area: Self-healing intelligence  
Current state: Monitoring uses polling and rule-based state changes.  
Problem: Static checks may miss micro-outages, traffic spikes, and subtle degradation.  
User value: The app could explain and respond to unusual network behavior.  
Dependencies: R-034, R-036.  
Implementation steps:
- Start with statistical baselines before machine learning.
- Research anomaly features from latency, DNS failures, traffic counters, and ETW if available.
- Define explainable recommendations and opt-in behavior.
Acceptance criteria:
- Prototype detects simulated anomalies with low false positives.
- Findings include evidence and confidence.
Tests:
- Synthetic data tests.
- Replay tests from anonymized local metrics.
Risk: High.

### R-065: Overlay Network Orchestration
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Done. Added `overlay_networks.py` with read-only Tailscale/ZeroTier detection, status command planning, operation safety gates, CLI exposure, GUI tool access, docs, and tests. Mutating overlay operations remain blocked until user consent, vendor CLI/API stability, rollback, and safety review are complete.


Priority: P6 Frontier  
Area: Mesh networking  
Current state: The app manages local physical and virtual adapter settings but does not orchestrate mesh tools.  
Problem: Users often rely on Tailscale, ZeroTier, or similar overlay networks.  
User value: The app could centralize local and overlay network state.  
Dependencies: R-025, R-033.  
Implementation steps:
- Detect installed Tailscale and ZeroTier clients.
- Research read-only peer status first.
- Consider exit-node toggles or route helpers only after user consent and vendor CLI/API stability review.
Acceptance criteria:
- Research note identifies supported overlay operations.
- Initial prototype is read-only.
Tests:
- Detection tests with mocked CLIs.
- Manual read-only status test.
Risk: Medium.

### R-066: Domain-Fronting And Traffic Camouflage Research
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. Consolidated overlay and frontier restriction research into `docs/RESEARCH_AND_FRONTIER_BACKLOG.md`, preserving domain-fronting and traffic-camouflage ideas as research questions only, with explicit bans on operational bypass steps, target lists, provider-specific evasion instructions, or hidden policy circumvention.


Priority: P6 Frontier  
Area: Network restriction research  
Current state: The roadmap discusses evasion concepts but does not implement them.  
Problem: These capabilities may conflict with network policies or laws depending on context.  
User value: The project preserves the ambition while requiring strict review.  
Dependencies: R-053.  
Implementation steps:
- Treat domain-fronting, traffic camouflage, and protocol-shaping ideas as research questions only.
- Evaluate legality, provider policies, user safety, and abuse potential before prototypes.
- Restrict the product plan to diagnostics and lawful recommendations unless reviewed otherwise.
Acceptance criteria:
- No operational instructions or target lists are included in product docs.
- Any future work requires explicit legal, ethical, safety, and feasibility review.
Tests:
- Documentation safety review.
- Search for operational bypass instructions.
Risk: High.

### R-067: Post-Quantum Plugin Signing Research
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. Added `signing_research.py` with schema-versioned signature metadata, production versus research-only algorithm sets, post-quantum gating, algorithm agility plan, docs, and tests. No immature cryptography dependency was added.


Priority: P6 Frontier  
Area: Cryptographic future-proofing  
Current state: Plugin signing is only a research item.  
Problem: Long-lived plugin ecosystems may need future cryptographic agility.  
User value: The platform can avoid being locked into obsolete trust mechanisms.  
Dependencies: R-050.  
Implementation steps:
- Research NIST post-quantum signature options and library maturity.
- Design signature metadata to allow algorithm agility.
- Avoid adopting immature cryptography before ecosystem support is stable.
Acceptance criteria:
- Research note defines an algorithm-agile signing format.
- No production dependency is added until mature.
Tests:
- Prototype signature verification with test keys only.
- Algorithm migration simulation.
Risk: High.

### R-068: Advanced Anti-Censorship Diagnostics Concepts
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Completed. Added diagnostics-only frontier guidance for active probing detection, fingerprinting analysis, forged packet detection, and penalty-box behavior, requiring owned infrastructure, consent, bounded duration, confidence scoring, and no attribution claims without corroboration.


Priority: P6 Frontier  
Area: Frontier diagnostics  
Current state: The audit includes ideas such as active probing detection, fingerprinting analysis, forged packet detection, and penalty-box behavior.  
Problem: These concepts are powerful but can be sensitive, costly, and hard to validate safely.  
User value: The roadmap keeps the ideas visible for future expert review.  
Dependencies: R-053, R-060.  
Implementation steps:
- Catalog concepts as diagnostics-only research.
- Require owned test infrastructure for any active external test.
- Add confidence scoring and avoid attribution claims without strong evidence.
Acceptance criteria:
- Concepts are preserved without operational bypass guidance.
- Each concept has a safety gate before implementation.
Tests:
- Documentation safety review.
- Lab-only prototype tests if approved.
Risk: High.

### R-069: CLI Companion
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Done. Added `nmp_cli.py` with `status`, `list-dns`, `dns list`, `dns apply`, `dns clear`, `proxy status`, `proxy enable`, `proxy disable`, `ddns force`, `export-diagnostics`, consent-gated diagnostics, overlay status, Multi-WAN status, anomaly review, and PCAP planning. Commands return stable exit codes, support JSON output, preserve GUI startup behavior, and have tests. Broker-routed privileged execution was completed under `R-040`.


Priority: P2 Product Expansion  
Area: Developer ergonomics  
Current state: Lucid Net is GUI and tray driven.  
Problem: Power users and administrators may need scriptable actions.  
User value: DNS, proxy, diagnostics, and status operations can be integrated into workflows.  
Dependencies: R-040.  
Implementation steps:
- Add an `nmp` CLI or command-line mode before GUI initialization.
- Support status, list profiles, apply DNS, enable/disable proxy, force DDNS, and export diagnostics.
- Route privileged actions through the broker once Phase 6 is implemented.
Acceptance criteria:
- CLI commands return stable exit codes and machine-readable optional output.
- GUI behavior remains unchanged for normal launches.
Tests:
- CLI unit tests.
- Manual command tests.
Risk: Medium.

### R-070: Power Efficiency Mode
Progress: [x] Done / [ ] Partially done / [ ] Open
Work log: Done. Added `power_policy.py` with best-effort Windows battery status probing, power-efficiency policy decisions, reduced polling, expensive analytics suspension, minimized-window refresh pause guidance, monitor integration, GUI settings, visible reduced-mode state, DDNS pause behavior during battery-saver reduced mode, docs, and tests.


Priority: P2 Product Expansion  
Area: Power management  
Current state: Monitoring and GUI refreshes run on fixed intervals.  
Problem: Frequent polling can drain battery on laptops.  
User value: The app behaves politely on battery and metered networks.  
Dependencies: R-027.  
Implementation steps:
- Query Windows power state and battery saver status.
- Reduce monitor polling and suspend expensive analytics when on low battery.
- Pause UI refresh loops while minimized or hidden where safe.
Acceptance criteria:
- Power-saving state reduces background work.
- Users can see and configure power policy.
Tests:
- Mock power-state policy tests.
- Manual minimize and battery-state tests.
Risk: Medium.

## 16. Risk, Ethics, And Safety Boundaries

Lucid Net may diagnose network behavior and recommend lawful, user-consented local configuration changes. Features involving policy bypass, traffic camouflage, identity rotation, or anti-censorship countermeasures require legal, ethical, safety, and feasibility review before implementation.

Safety rules:

- Deep diagnostics must be opt-in, bounded, cancelable, and clear about what data is collected.
- The product must not include operational bypass instructions, target lists, destructive workflows, or claims that encourage violating network policies.
- Packet captures and forensics exports must warn users that they may contain sensitive content.
- Research items must distinguish evidence, confidence, recommendation, and uncertainty.
- Privileged operations must have rollback, audit events, and clear user-visible state.
- Plugin marketplace work must prioritize authenticity, permission clarity, and revocation before convenience.

Research questions for sensitive areas:

- What can be detected safely?
- What can be explained to users without enabling misuse?
- What can be implemented lawfully in target markets?
- What requires external legal, ethical, security, or domain expert review?

## 17. Release Milestones

### M1: Roadmap And Quality Foundation

- Complete this cleaned roadmap.
- Add glossary and safety boundaries.
- Add pytest plan and CI plan.
- Define logging and diagnostics conventions.

### M2: Reliability Release

- Add pytest foundation.
- Add config, DDNS, redaction, and plugin tests.
- Migrate history to SQLite.
- Add crash-safe config migration.
- Improve diagnostics bundles.

### M3: Security Release

- Store DDNS secrets with Windows Credential Manager through `keyring`.
- Tighten plugin permission enforcement.
- Document admin and trusted-plugin risks clearly.
- Complete elevated broker design research.

### M4: Workflow Release

- Add UI state persistence.
- Add richer tray actions.
- Replace textbox views with sortable grids.
- Add onboarding, keyboard navigation, and clearer recovery messages.

### M5: Automation Release

- Add context-aware network profiles.
- Add captive portal detection.
- Add metered-connection awareness.
- Add dead-man rollback.
- Add PAC, SOCKS5, hosts management, and IPv4/IPv6 DDNS in staged increments.

### M6: Architecture Release

- Prototype standard-user GUI with elevated broker or Windows Service.
- Add named pipe IPC with ACLs.
- Move privileged mutations behind the broker boundary.

### M7: Enterprise Release

- Add HKLM policy overrides.
- Add Intune/GPO deployment model.
- Add Windows Event Log export.
- Add silent installer options.
- Add code signing and update verification.

### M8: Research Track

- Research ETW traffic analytics.
- Research WFP/WinDivert enforcement.
- Research forensics sidecar binary.
- Research plugin marketplace and signing.
- Research frontier diagnostics, overlay networks, AI anomaly detection, and power efficiency.

## 18. Backlog Matrix

| ID | Item | Progress | Phase | Priority | Effort | Risk | Depends On |
|---|---|---|---:|---|---|---|---|
| R-001 | Clean roadmap document | [x] Done | 0 | P0 Foundation | S | Low | None |
| R-002 | Add terminology glossary | [x] Done | 0 | P0 Foundation | S | Low | R-001 |
| R-003 | Separate facts, commitments, research, and frontier ideas | [x] Done | 0 | P0 Foundation | S | Low | R-001 |
| R-071 | Product vision and branding system | [x] Done | 0 | P0 Foundation | S | Low | R-001, R-003 |
| R-004 | Add pytest foundation | [x] Done | 1 | P1 Next Release | M | Low | R-001 |
| R-005 | Add CI quality checks | [x] Done | 1 | P1 Next Release | M | Low | R-004 |
| R-006 | Config validation test suite | [x] Done | 1 | P1 Next Release | S | Low | R-004 |
| R-007 | DDNS test suite | [x] Done | 1 | P1 Next Release | S | Low | R-004 |
| R-008 | Redaction test suite | [x] Done | 1 | P1 Next Release | S | Low | R-004 |
| R-009 | Plugin manifest test suite | [x] Done | 1 | P1 Next Release | S | Low | R-004 |
| R-010 | SQLite event history | [x] Done | 1 | P1 Next Release | M | Medium | R-004 |
| R-011 | Structured logging conventions | [x] Done | 1 | P1 Next Release | S | Low | R-001 |
| R-012 | Crash-safe config migration | [x] Done | 1 | P1 Next Release | M | Medium | R-006 |
| R-013 | Store DDNS secrets in Windows Credential Manager | [x] Done | 2 | P1 Next Release | M | Medium | R-012 |
| R-014 | Document current admin risk clearly | [x] Done | 2 | P1 Next Release | S | Low | R-001 |
| R-015 | Tighten plugin permission enforcement | [x] Done | 2 | P1 Next Release | S | Low | R-009 |
| R-016 | Trusted-only plugin model | [x] Done | 2 | P1 Next Release | S | Low | R-014, R-015 |
| R-017 | Plugin signing research | [x] Done | 2 | P5 Research | M | Medium | R-016 |
| R-018 | Elevated broker design research | [x] Done | 2 | P3 Advanced Architecture | L | High | R-014 |
| R-019 | UI state persistence | [x] Done | 3 | P1 Next Release | S | Low | R-012 |
| R-020 | Rich tray menu | [x] Done | 3 | P2 Product Expansion | M | Medium | R-019 |
| R-021 | Sortable history, traffic, and plugin grids | [x] Done | 3 | P2 Product Expansion | M | Medium | R-010 |
| R-022 | First-run onboarding | [x] Done | 3 | P2 Product Expansion | M | Low | R-019 |
| R-023 | Keyboard navigation and accessibility | [x] Done | 3 | P2 Product Expansion | M | Medium | R-021 |
| R-024 | Clearer recovery and error messages | [x] Done | 3 | P1 Next Release | S | Low | R-011 |
| R-025 | Context-aware network profiles | [x] Done | 4 | P2 Product Expansion | L | Medium | R-024 |
| R-026 | Captive portal detection | [x] Done | 4 | P2 Product Expansion | M | Medium | R-025 |
| R-027 | Metered-connection awareness | [x] Done | 4 | P2 Product Expansion | M | Medium | R-025 |
| R-028 | Dead-man rollback | [x] Done | 4 | P2 Product Expansion | M | Medium | R-024, R-025 |
| R-029 | PAC support | [x] Done | 4 | P2 Product Expansion | M | Medium | R-012 |
| R-030 | SOCKS5 support | [x] Done | 4 | P2 Product Expansion | M | Medium | R-029 |
| R-031 | Hosts file manager | [x] Done | 4 | P2 Product Expansion | L | High | R-018, R-028 |
| R-032 | IPv4 and IPv6 DDNS support | [x] Done | 4 | P2 Product Expansion | M | Medium | R-007, R-013 |
| R-033 | Improved traffic tab | [x] Done | 5 | P2 Product Expansion | M | Low | R-021 |
| R-034 | Bandwidth and latency history | [x] Done | 5 | P2 Product Expansion | M | Medium | R-010, R-033 |
| R-035 | Diagnostics bundle improvements | [x] Done | 5 | P1 Next Release | M | Low | R-008, R-011 |
| R-036 | ETW per-process bandwidth research | [x] Done | 5 | P5 Research | L | High | R-033, R-034 |
| R-037 | Standard-user GUI with elevated worker | [x] Done | 6 | P3 Advanced Architecture | L | High | R-018 |
| R-038 | Windows Service versus on-demand broker decision record | [x] Done | 6 | P3 Advanced Architecture | M | Medium | R-018 |
| R-039 | Named pipe IPC with ACLs | [x] Done | 6 | P3 Advanced Architecture | L | High | R-038 |
| R-040 | Move privileged mutations into broker | [x] Done | 6 | P3 Advanced Architecture | L | High | R-037, R-039 |
| R-041 | HKLM policy overrides | [x] Done | 7 | P4 Enterprise | L | High | R-037 |
| R-042 | Intune and GPO deployment model | [x] Done | 7 | P4 Enterprise | M | Medium | R-041 |
| R-043 | Windows Event Log export | [x] Done | 7 | P4 Enterprise | M | Medium | R-010, R-040 |
| R-044 | SIEM and OpenTelemetry research | [x] Done | 7 | P5 Research | L | High | R-043 |
| R-045 | Silent installer options | [x] Done | 7 | P4 Enterprise | M | Medium | R-042 |
| R-046 | Code signing and update verification | [x] Done | 7 | P4 Enterprise | M | Medium | R-005 |
| R-047 | Plugin subprocess isolation | [x] Done | 8 | P3 Advanced Architecture | L | High | R-016, R-039 |
| R-048 | Per-plugin virtual environments | [x] Done | 8 | P2 Product Expansion | L | High | R-047 |
| R-049 | Plugin hot reload | [x] Done | 8 | P2 Product Expansion | M | Medium | R-016 |
| R-050 | Signed plugin bundles | [x] Done | 8 | P5 Research | L | High | R-017 |
| R-051 | Plugin marketplace UI | [x] Done | 8 | P5 Research | L | High | R-050 |
| R-052 | WASM plugin runtime research | [x] Done | 8 | P5 Research | L | High | R-047 |
| R-053 | Consent-based diagnostics framework | [x] Done | 9 | P5 Research | L | High | R-003, R-035 |
| R-054 | DNS poisoning and transparent DNS proxy detection | [x] Done | 9 | P5 Research | L | High | R-053 |
| R-055 | SNI filtering and SSL inspection detection | [x] Done | 9 | P5 Research | L | High | R-053 |
| R-056 | Captive portal and transparent HTTP proxy diagnostics | [x] Done | 9 | P2 Product Expansion | M | Medium | R-026 |
| R-057 | QUIC UDP degradation and PMTUD blackhole research | [x] Done | 9 | P5 Research | L | High | R-053 |
| R-058 | BGP and route anomaly research | [x] Done | 9 | P5 Research | L | High | R-053 |
| R-059 | PCAP export research | [x] Done | 9 | P5 Research | L | High | R-036, R-053 |
| R-060 | Go or Rust forensics sidecar research | [x] Done | 9 | P5 Research | L | High | R-053 |
| R-061 | WFP and WinDivert enforcement research | [x] Done | 10 | P6 Frontier | XL | High | R-040, R-053 |
| R-062 | Per-app routing and kill-switch research | [x] Done | 10 | P6 Frontier | XL | High | R-061 |
| R-063 | Multi-WAN and adapter load balancing research | [x] Done | 10 | P6 Frontier | XL | High | R-040 |
| R-064 | AI anomaly detection research | [x] Done | 10 | P6 Frontier | L | High | R-034, R-036 |
| R-065 | Overlay network orchestration | [x] Done | 10 | P6 Frontier | L | Medium | R-025, R-033 |
| R-066 | Domain-fronting and traffic camouflage research | [x] Done | 10 | P6 Frontier | XL | High | R-053 |
| R-067 | Post-quantum plugin signing research | [x] Done | 10 | P6 Frontier | L | High | R-050 |
| R-068 | Advanced anti-censorship diagnostics concepts | [x] Done | 10 | P6 Frontier | XL | High | R-053, R-060 |
| R-069 | CLI companion | [x] Done | 10 | P2 Product Expansion | M | Medium | R-040 |
| R-070 | Power efficiency mode | [x] Done | 10 | P2 Product Expansion | M | Medium | R-027 |
