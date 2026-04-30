# ETW Per-Process Bandwidth Research

Status: research note for R-036.

## Problem

The current Traffic tab uses `psutil` connection inventory and aggregate system counters. This is useful for daily troubleshooting, but it cannot truthfully attribute upload/download bytes to individual processes. Accurate per-process bandwidth on Windows requires Event Tracing for Windows (ETW), Windows Filtering Platform (WFP), packet capture drivers, or a native helper.

## Recommendation

Use ETW as the first research path before any packet driver or WFP enforcement work.

ETW is preferred because it is built into Windows, can be read without installing a packet driver, and is a better fit for passive observability than WinDivert or kernel-level routing. The first prototype should be read-only and should avoid packet payload capture.

## Candidate Providers

- Microsoft-Windows-Kernel-Network
- Microsoft-Windows-TCPIP
- Microsoft-Windows-Winsock-AFD

The prototype must verify which provider gives stable PID, direction, byte count, and endpoint metadata on Windows 10 and Windows 11.

## Prototype Options

- C# sidecar using TraceEvent.
- Rust sidecar using krabsetw or native TDH APIs.
- Python proof of concept only if a maintained ETW binding is available and packageable.

## Acceptance Path

1. Generate controlled traffic from a known process.
2. Collect ETW events for that PID.
3. Compare ETW byte totals against aggregate system counters and expected transfer size.
4. Measure CPU and memory overhead during a 10-minute capture.
5. Export only process, PID, endpoint, direction, byte count, timestamp, and provider metadata.

## Safety Boundary

This feature is observability only. It must not capture payloads, secrets, browser URLs, or packet contents. Any later WFP or WinDivert work belongs to frontier research and requires a separate legal, ethical, safety, and feasibility review.

## Open Questions

- Which provider remains stable across Windows 10 and Windows 11 builds?
- Does collection require administrator rights in the packaged app?
- Should ETW live in the elevated broker, a read-only sidecar, or a future service?
- What retention policy keeps metrics useful without creating sensitive long-term activity records?
