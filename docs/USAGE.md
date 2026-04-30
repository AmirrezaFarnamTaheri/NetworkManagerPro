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

## Proxy

Use Proxy to manage simple current-user WinINet proxy endpoints.

- Profiles must be `host:port`.
- IPv6 proxy hosts must be `[address]:port`.
- Credentials, schemes, spaces, semicolons, and per-protocol rules are rejected.
- Existing proxy bypass and PAC settings are preserved in restore snapshots.

PAC and SOCKS5 support now exists in the core layer for validated profiles and future UI controls. PAC URLs are stored as `pac_profiles`, while SOCKS5 endpoints are stored as `socks5_profiles`. Until the UI controls are completed, keep normal proxy changes in the visible Proxy tab and treat PAC/SOCKS entries as advanced configuration.

## DDNS

Use DDNS to save a provider update URL and run manual sync. Auto-DDNS can be enabled in Settings after a URL is saved.

The monitor tracks the last successfully synced public IP separately from the last seen public IP. Failed updates are retried with backoff and are not marked complete.

Dual-stack DDNS scaffolding is available through `ddns_update_url_v4` and `ddns_update_url_v6`. The app can detect public IPv4 and IPv6 addresses separately and route each configured update URL to its matching address family. The current visible DDNS tab still uses the single legacy-compatible URL flow.

## Tools

Tools provides:

- DNS cache flush;
- DHCP renew;
- copy diagnostics;
- export diagnostics;
- restore previous settings.

Diagnostics are sanitized and exported under `%LOCALAPPDATA%\NetworkManagerPro`.

## History

History shows recent app events, settings changes, plugin events, DDNS activity, diagnostics exports, startup, and shutdown. Event details are recursively redacted before storage.

## Traffic

Traffic shows system byte totals and a best-effort per-process active connection inventory. It is not a firewall, packet capture, or per-process bandwidth accounting tool.

Each manual traffic refresh stores aggregate system counters in `%LOCALAPPDATA%\NetworkManagerPro\history\traffic_metrics.sqlite3`. The tab summarizes recent upload/download deltas from those saved samples so short-term trends are visible without claiming ETW-level attribution.

## Hosts File Safety

Hosts-file management is implemented as a safety-first core module. It previews managed groups, wraps app-owned blocks with `NetworkManagerPro` markers, and creates a backup before writing. Direct UI controls and elevated broker handoff are still roadmap work; do not edit the real Windows hosts file without administrator rights and a backup.

## Plugins

Plugins shows discovered manifests from:

- `%LOCALAPPDATA%\NetworkManagerPro\plugins`;
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
