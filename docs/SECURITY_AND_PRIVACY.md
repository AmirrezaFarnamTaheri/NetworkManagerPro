# Security and Privacy

Lucid Net is a local Windows utility. It changes local network settings and stores user data on the current machine.

## Elevation

The app requests administrator rights on startup because DNS changes require elevation. Proxy, DDNS, diagnostics, monitoring, history, and plugins run in the same process after elevation.

This means the current GUI and every enabled plugin share one elevated process. A plugin can execute arbitrary Python code with the app's privileges, even though the PluginAPI gates official helper methods. Only enable plugins you fully trust.

Future privilege-separation work should move DNS, hosts, firewall, and other privileged mutations into a narrow elevated broker or Windows Service while the GUI runs as a standard user.

## Network Calls

The app makes these built-in outbound calls:

- Public IP lookup: `https://api.ipify.org?format=json`
- DDNS update: the URL stored in Windows Credential Manager for DDNS updates.
- Consent-gated diagnostics: optional user-started DNS-over-HTTPS comparison, TLS certificate checks, transparent DNS proxy evidence checks, and SNI/TLS failure classification for benign or user-owned endpoints.

Python HTTP requests may not automatically follow the Windows proxy setting managed by the app. Some networks may require separate app-level proxy support in a future release.

Advanced diagnostics report evidence and confidence only. Lucid Net may diagnose network behavior and recommend lawful, user-consented local configuration changes. Features involving policy bypass, traffic camouflage, identity rotation, or anti-censorship countermeasures require legal, ethical, safety, and feasibility review before implementation.

Unimplemented research and frontier capabilities are consolidated in `docs/RESEARCH_AND_FRONTIER_BACKLOG.md`.

## Local Data

Runtime data lives under:

```text
%LOCALAPPDATA%\LucidNet
```

This includes config, logs, history, diagnostics bundles, and user plugins.

DDNS update URLs are stored through the OS credential store for new saves. The config file keeps the DDNS URL field empty except for legacy fallback/import cases.

## Redaction

The app redacts:

- DDNS URL path segments;
- DDNS query values;
- keys containing token, key, secret, pass, auth, or credential;
- proxy credentials if encountered in external data;
- plugin event details before history writes.

Review diagnostics bundles before sharing them. Redaction is defensive, not a formal data-loss-prevention system.

## Windows Settings Touched

- DNS: `Set-DnsClientServerAddress`
- Proxy: `HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings`
- Startup: `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`

Proxy restore snapshots include `ProxyEnable`, `ProxyServer`, `ProxyOverride`, and `AutoConfigURL`.

## Plugins

Plugin API permissions are enforced as API gates, and missing permissions raise clear errors. They are not a sandbox. Plugins are still Python modules running in-process with the same OS privileges as Lucid Net.

Treat the current plugin system as trusted-only. Do not install plugins from unknown publishers, unsigned archives, or copied code you have not reviewed. For untrusted extensions, a future subprocess, signed bundle, WASM runtime, or service boundary would be required.

## Packet Capture

PCAP export remains sidecar-gated research. Packet captures can contain sensitive content, hostnames, addresses, credentials, and browsing metadata. Any future capture flow must be explicitly user-started, time-bounded, disabled for payload capture by default, and backed by a signed optional sidecar binary.
