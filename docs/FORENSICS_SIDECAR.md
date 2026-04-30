# Forensics Sidecar

Status: implementation note for R-059 and R-060.

Lucid Net keeps packet capture and advanced TLS/packet diagnostics outside the GUI process. The optional sidecar contract uses JSON stdin/stdout, bounded timeouts, sanitized findings, and explicit user consent.

## Language Decision

Rust is the recommended first sidecar language. It gives static-binary distribution, strong memory safety, and explicit dependency review for packet and TLS parsing. Go remains a fallback if Windows capture library support or build ergonomics are stronger in practice.

The scaffold lives at:

```text
sidecars\forensics-sidecar-rust
```

The first supported command is `status`. The `pcap_export` command is intentionally disabled in the scaffold until packet capture, signing, privacy review, and manual validation are complete.

## PCAP Safety Rules

- Captures must be explicitly user-started.
- Duration is bounded from 5 to 300 seconds.
- Payload capture is disabled by default.
- Results must include a manifest that records duration, output paths, sidecar findings, and the warning that PCAP files are not redacted.
- The app must not include target lists, bypass instructions, or destructive workflows.
