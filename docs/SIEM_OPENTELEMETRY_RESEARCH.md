# SIEM And OpenTelemetry Research

Status: research note for R-044.

## Recommendation

Use Windows Event Log plus Windows Event Forwarding as the first enterprise export path. Defer direct vendor exporters until the local event schema is stable.

This path fits the current roadmap because it keeps sensitive transport decisions in existing enterprise tooling, avoids embedding SIEM credentials in the desktop app, and builds on the Windows Event Log work.

## Compared Options

| Option | Strength | Concern | Recommendation |
|---|---|---|---|
| Windows Event Forwarding | Native Windows fleet path | Requires domain or collector setup | First supported path |
| OpenTelemetry OTLP | Vendor-neutral | Requires endpoint, auth, batching, retry, privacy model | Research after Event Log |
| Syslog | Broad SIEM support | Windows desktop sender needed | Later optional bridge |
| Splunk HEC | Mature ingestion | Vendor-specific token handling | Defer |
| Datadog intake | Mature ingestion | Vendor-specific agent/keys | Defer |
| Microsoft Sentinel | Strong Windows alignment | Usually best through Event Log/WEF/AMA | Use Event Log first |

## Event Schema

Exported events should contain only:

- App name and version.
- Event type.
- Timestamp.
- Success/failure.
- Sanitized summary.
- Redacted details.
- Command/request ID when available.
- Managed policy state when relevant.

Events must not contain DDNS secrets, proxy credentials, raw plugin settings, packet payloads, browsing history, or target lists.

## Prototype Path

1. Write sanitized test events to Windows Event Log.
2. Configure Windows Event Forwarding in a lab.
3. Confirm event payloads appear in the collector.
4. Document filtering by event source `NetworkManagerPro`.
5. Reassess whether OTLP adds value after local audit events stabilize.

## Safety Boundary

Remote export must be opt-in for organizations and must remain transparent to the local user where policy allows. Personal-use installations should keep diagnostics local by default.
