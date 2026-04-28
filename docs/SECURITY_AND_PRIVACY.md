# Security and Privacy

Network Manager Pro is a local Windows utility. It changes local network settings and stores user data on the current machine.

## Elevation

The app requests administrator rights on startup because DNS changes require elevation. Proxy, DDNS, diagnostics, monitoring, history, and plugins run in the same process after elevation.

Only enable plugins you trust.

## Network Calls

The app makes these built-in outbound calls:

- Public IP lookup: `https://api.ipify.org?format=json`
- DDNS update: your configured `ddns_update_url`

Python HTTP requests may not automatically follow the Windows proxy setting managed by the app. Some networks may require separate app-level proxy support in a future release.

## Local Data

Runtime data lives under:

```text
%LOCALAPPDATA%\NetworkManagerPro
```

This includes config, logs, history, diagnostics bundles, and user plugins.

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

Plugin API permissions are enforced, but plugins are still Python modules running in-process. Do not install untrusted plugins. For untrusted extensions, a future subprocess or service boundary would be required.
