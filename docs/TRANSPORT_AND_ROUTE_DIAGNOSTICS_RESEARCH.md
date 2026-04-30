# Transport And Route Diagnostics Research

Status: research note for R-057 and R-058.

## QUIC, UDP, And PMTUD

The first transport diagnostics should be explanatory and low risk:

- Compare TCP HTTPS reachability with a safe UDP/QUIC-capable endpoint only when the user consents.
- Prefer library-level HTTP/3 capability checks over raw packet crafting.
- Keep PMTUD research outside the main GUI until a sidecar can safely run bounded tests.
- Avoid payload capture and avoid generating high-volume traffic.

Prototype limits:

- Short duration.
- Small packet counts.
- User-visible cancellation.
- No forged packets.
- No bypass or evasion instructions.

Expected findings:

- UDP likely blocked or degraded.
- HTTP/3 unavailable while HTTPS works.
- PMTUD inconclusive.
- Possible MTU blackhole under controlled lab conditions.

## Route And BGP Anomaly Research

Route diagnostics should start with sanitized local evidence:

- Local route table summary.
- Default gateway.
- Traceroute hop count and timeout pattern.
- Optional ASN/Geo-IP lookup for public IPs if the user consents.
- Optional public looking-glass comparison only after privacy review.

Do not claim attribution without strong evidence. Findings should use confidence levels and explain limits.

Recommended confidence model:

- Low: local route or traceroute suggests a pattern but has no external corroboration.
- Medium: local trace plus public ASN metadata supports a likely path change.
- High: multiple independent sources corroborate a route leak or provider incident.

## Sidecar Direction

If PMTUD, QUIC, or route diagnostics require raw sockets, packet options, or platform-specific APIs, move them to the future Go/Rust forensics sidecar. The main GUI should orchestrate consent, display results, and export sanitized evidence.
