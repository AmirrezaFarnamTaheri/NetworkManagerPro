# Usage

## Dashboard

Dashboard is the operational landing page. It shows monitor state and exposes quick actions:

- Apply DNS: applies the DNS profile selected in the DNS panel.
- DNS Auto: resets DNS on the selected/active interface.
- Disable Proxy: turns off the current-user Windows proxy.
- Force DDNS: runs a manual DDNS update after URL validation.
- Restore: restores the most recent successful app-captured DNS/proxy snapshot.

## DNS

Use DNS to choose the target interface, apply predefined profiles, and manage custom profiles.

- Predefined profiles ship from built-in defaults.
- Custom profiles can be added by name.
- Existing profile names can be overwritten.
- Selected profiles can be deleted.
- IPv4 and IPv6 DNS addresses are accepted and validated.

## Context-Aware Profiles

Network profiles can match SSID, BSSID, interface alias, and gateway. The Tools tab previews the currently matched profile, and the monitor can auto-apply profiles only when the profile has `auto_apply` enabled.

Auto-apply rules:

- Unknown networks do not change settings.
- Profiles with `auto_apply` disabled only produce previews.
- Captive portal detection pauses auto-apply while login is required.
- DNS and proxy changes use restore snapshots and dead-man rollback.
- Every auto-apply attempt is recorded in local history.

## Proxy

Use Proxy to manage simple current-user WinINet proxy endpoints.

- Profiles must be `host:port`.
- IPv6 proxy hosts must be `[address]:port`.
- Credentials, schemes, spaces, semicolons, and per-protocol rules are rejected.
- Existing proxy bypass and PAC settings are preserved in restore snapshots.

PAC and SOCKS5 controls are available in the Proxy tab:

- PAC URLs are stored as `pac_profiles` and must point to `.pac` or `.dat` files.
- SOCKS5 endpoints are stored as `socks5_profiles` and accept `host:port`, `socks://host:port`, or `socks5://host:port`.
- PAC and SOCKS5 apply actions capture restore points and use the same rollback policy as normal proxy changes.

## DDNS

Use DDNS to save a provider update URL and run manual sync. Auto-DDNS can be enabled in Settings after a URL is saved.

The monitor tracks the last successfully synced public IP separately from the last seen public IP. Failed updates are retried with backoff and are not marked complete.

Dual-stack DDNS controls are available through `ddns_update_url_v4` and `ddns_update_url_v6`. The app can detect public IPv4 and IPv6 addresses separately and route each configured update URL to its matching address family.

## Tools

Tools provides:

- DNS cache flush;
- DHCP renew;
- copy diagnostics;
- export diagnostics;
- restore previous settings;
- preview context-aware network profile plans;
- run captive portal, overlay, and power-policy checks;
- preview, apply, and disable one managed hosts-file group with backup.

Diagnostics are sanitized and exported under `%LOCALAPPDATA%\LucidNet`.

Advanced diagnostic CLI commands are also available:

```powershell
python nmp_cli.py diagnose transparent-dns --domain example.com --i-consent --json
python nmp_cli.py diagnose sni --host example.com --i-consent --json
python nmp_cli.py pcap-plan --duration 30 --interface "Wi-Fi" --request --json
python nmp_cli.py sidecar-decision --json
python nmp_cli.py frontier status --json
python nmp_cli.py frontier gate --capability advanced_anti_censorship --operation diagnose --i-consent --json
```

These commands report evidence and confidence only. They do not attempt bypass, evasion, identity rotation, or destructive network changes.

Unimplemented research and frontier work is tracked in `docs/RESEARCH_AND_FRONTIER_BACKLOG.md`.

## History

History shows recent app events, settings changes, plugin events, DDNS activity, diagnostics exports, startup, and shutdown. Event details are recursively redacted before storage.

## Traffic

Traffic shows system byte totals and a best-effort per-process active connection inventory. It is not a firewall, packet capture, or per-process bandwidth accounting tool.

Each manual traffic refresh stores aggregate system counters in `%LOCALAPPDATA%\LucidNet\history\traffic_metrics.sqlite3`. The tab summarizes recent upload/download deltas from those saved samples so short-term trends are visible without claiming ETW-level attribution.

## Hosts File Safety

Hosts-file management is implemented as a safety-first workflow. It previews managed groups, wraps app-owned blocks with `LucidNet` markers, validates entries, and creates a backup before writing. Editing the real Windows hosts file requires administrator rights; future broker routing will move privileged writes out of the GUI process.

## Plugins

Plugins shows discovered manifests from:

- `%LOCALAPPDATA%\LucidNet\plugins`;
- bundled read-only plugin examples inside the app.

Only IDs listed in `plugins.enabled` load. Manifest permissions gate access to the v1 plugin API.

## Settings Monitor

Settings Monitor shows effective DNS and proxy state and records detected changes. Attribution is best-effort and may be unknown.

## Settings

Settings controls:

- Run at Windows logon;
- Minimize to tray on close;
- Auto-update DDNS;
- Monitor interval.

Auto-DDNS is automatically disabled if no DDNS URL is configured.

## Help and About

Help links to bundled documentation and opens runtime folders. About shows the app version and runtime paths.

## Keyboard Access

- `Ctrl+R`: refresh the current tab or monitor state.
- `Ctrl+D`: apply the selected DNS profile.
- `Ctrl+P`: disable the proxy.
- `Ctrl+E`: export diagnostics.
- `Alt+1` through `Alt+5`: jump to Dashboard, DNS, Proxy, DDNS, and History.

History, Traffic, and Plugins use sortable grids. Activate a column header to sort rows for faster keyboard and mouse review.
