# Frontier Forensics And Enforcement Research

Status: research and safety note for R-059 through R-064.

## PCAP Export

Packet capture must be explicit, bounded, and user-started. Captures may contain hostnames, IP addresses, credentials, cookies, and application payloads. The product must warn users before capture and store output under `%LOCALAPPDATA%\NetworkManagerPro\forensics` unless the user chooses another folder.

Recommended path:

1. Start with a JSON summary export from existing diagnostics and ETW research.
2. Evaluate ETW-to-PCAP conversion only for metadata-safe use cases.
3. Move packet capture into a signed Go or Rust sidecar if raw capture is required.
4. Keep duration, interface, output format, and cancellation visible before start.

## Go Or Rust Forensics Sidecar

The sidecar should be optional, signed, and invoked with a JSON request over stdin/stdout. Python remains the orchestrator and UI layer.

Recommended first sidecar interface:

- Request: schema version, request ID, command, arguments, timeout.
- Response: schema version, OK flag, findings list, sanitized error.
- First harmless command: return version and environment capability summary.

Rust is preferred for a future packet/TLS sidecar if memory safety and static packaging are more important than developer speed. Go remains viable for fast iteration and simpler cross-compilation. The interface should be language-neutral so the first prototype can decide by evidence.

## WFP And WinDivert

WFP and WinDivert remain frontier research. They must not ship without:

- Legal, ethical, and safety review.
- Driver/signing feasibility review.
- Installer and rollback design.
- Performance testing.
- Clear user-visible audit history.

Research should first identify what can be achieved with Windows Firewall APIs and user-mode configuration before considering packet interception drivers.

## Per-App Routing And Kill Switch

Per-app routing and blocking should start with safe, reversible, auditable firewall-style controls. Any prototype must include:

- Visible process identity.
- Explicit user confirmation.
- Easy rollback.
- Event history entry.
- No hidden enforcement.

This work must not become an evasion or policy-bypass feature.

## Multi-WAN And Adapter Load Balancing

Network Manager Pro can research adapter priority and failover recommendations, but true bonding/load balancing should not be promised until technically proven.

Distinctions:

- Failover: choose a backup path when the primary path fails.
- Route preference: adjust metrics or recommend a preferred adapter.
- Bonding/load balancing: combine multiple links, which usually requires specialized drivers, VPNs, or network support.

The safe first prototype should recommend failover settings rather than automatically rewriting route tables.

## AI Anomaly Detection

Start with statistical baselines before machine learning. Candidate features:

- Aggregate bytes sent and received.
- Latency samples.
- DNS failure counts.
- Captive portal state changes.
- Future ETW per-process metrics.

Findings must include evidence and confidence. Self-healing actions must be opt-in and explainable; the app should ask before applying DNS, proxy, route, or firewall changes.
