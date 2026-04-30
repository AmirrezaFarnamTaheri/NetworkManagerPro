# Configuration

Network Manager Pro stores user configuration at:

```text
%LOCALAPPDATA%\NetworkManagerPro\config.json
```

The file is created automatically from built-in defaults. The installed executable does not require any loose config file.

## Schema

```json
{
  "config_version": 1,
  "ddns_update_url": "",
  "settings": {
    "auto_update_ddns": false,
    "check_interval_seconds": 60,
    "minimize_to_tray_on_close": true,
    "pause_background_on_metered": true,
    "rollback_on_connectivity_loss": true
  },
  "plugins": {
    "enabled": [],
    "settings": {}
  },
  "dns_profiles": {
    "Cloudflare": ["1.1.1.1", "1.0.0.1"],
    "Google": ["8.8.8.8", "8.8.4.4"]
  },
  "proxy_profiles": [
    "127.0.0.1:8080",
    "127.0.0.1:10809"
  ],
  "pac_profiles": [
    "https://proxy.example/wpad.pac"
  ],
  "socks5_profiles": [
    "127.0.0.1:1080"
  ],
  "ddns_update_url_v4": "",
  "ddns_update_url_v6": "",
  "network_profiles": [
    {
      "name": "Office",
      "enabled": true,
      "ssid": "CorpWifi",
      "bssid": "aa:bb:cc:dd:ee:ff",
      "interface": "",
      "gateway": "",
      "dns_profile": "Cloudflare",
      "proxy_profile": "127.0.0.1:8080",
      "auto_apply": false
    }
  ]
}
```

## Keys

- `config_version`: current config schema version.
- `ddns_update_url`: reserved for legacy import fallback only. New saves store the DDNS URL in Windows Credential Manager and keep this config value empty.
- `settings.auto_update_ddns`: sync DDNS when the public IP differs from the last successful synced IP.
- `settings.check_interval_seconds`: monitor interval, clamped from 15 to 86400 seconds.
- `settings.minimize_to_tray_on_close`: close button hides the window instead of exiting.
- `settings.pause_background_on_metered`: reduce polling and pause automatic DDNS when the current connection is known to be metered.
- `settings.rollback_on_connectivity_loss`: run a post-change connectivity check after DNS/proxy changes and restore the captured snapshot if the check fails.
- `plugins.enabled`: plugin IDs to load.
- `plugins.settings`: plugin-owned settings by plugin ID.
- `dns_profiles`: named DNS server lists. Users can add, overwrite, and delete profiles in the UI.
- `proxy_profiles`: saved simple proxy endpoints. Users can add and delete profiles in the UI.
- `pac_profiles`: validated PAC URLs for future UI selection and current core-level PAC application.
- `socks5_profiles`: validated SOCKS5 endpoints for future UI selection and current core-level SOCKS5 application.
- `ddns_update_url_v4`: optional provider update URL for A-record/IPv4 DDNS updates.
- `ddns_update_url_v6`: optional provider update URL for AAAA-record/IPv6 DDNS updates.
- `network_profiles`: context-aware profile rules keyed by SSID, BSSID, interface alias, or default gateway. These rules currently provide normalized matching and preview data for automation; automatic mutation remains gated by explicit consent and future UI controls.

## Validation

- DNS entries must be valid IPv4 or IPv6 addresses.
- Proxy profiles must be simple `host:port` values.
- IPv6 proxy hosts must use `[address]:port`.
- Proxy profiles cannot contain URL schemes, credentials, whitespace, semicolons, or per-protocol WinINet rules.
- PAC profile URLs must be HTTP or HTTPS and should point to `.pac` or `.dat` files.
- SOCKS5 profile values may use `host:port` or `socks5://host:port`; credentials are not accepted.
- DDNS URLs must use `http://` or `https://`, include a valid host, and have a valid port if one is specified.
- Placeholder `example.com` DDNS URLs are rejected.
- Network profile rules must include a name and at least one context matcher: `ssid`, `bssid`, `interface`, or `gateway`.
- BSSID values are normalized to lowercase colon-separated form.
- Unknown top-level config keys are dropped during normalization.

## Custom Profiles

Use the DNS and Proxy panels to add custom entries. Saving a profile with an existing DNS name overwrites that profile after validation. Deleting a profile removes it from future dropdowns; the app keeps at least one DNS and one proxy profile so the UI always has a valid selection.

## Automation Safety

Network profile matching is intentionally non-mutating unless `auto_apply` is enabled by a future consent flow. Captive portal detection is diagnostic only: it checks whether a safe connectivity endpoint behaves normally, redirects to a login page, or appears modified. Dead-man rollback applies to app-driven DNS/proxy changes and uses the last captured restore snapshot when the post-change connectivity check fails.

## Privacy

Do not commit `config.json`. It can contain local network details and DDNS tokens. The repository ignores user config, invalid-config backups, logs, diagnostics bundles, virtual environments, and build output.
