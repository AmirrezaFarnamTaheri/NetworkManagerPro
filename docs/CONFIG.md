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
    "minimize_to_tray_on_close": true
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
  ]
}
```

## Keys

- `config_version`: current config schema version.
- `ddns_update_url`: optional HTTP(S) GET URL for your DDNS provider. Leave empty until configured.
- `settings.auto_update_ddns`: sync DDNS when the public IP differs from the last successful synced IP.
- `settings.check_interval_seconds`: monitor interval, clamped from 15 to 86400 seconds.
- `settings.minimize_to_tray_on_close`: close button hides the window instead of exiting.
- `plugins.enabled`: plugin IDs to load.
- `plugins.settings`: plugin-owned settings by plugin ID.
- `dns_profiles`: named DNS server lists. Users can add, overwrite, and delete profiles in the UI.
- `proxy_profiles`: saved simple proxy endpoints. Users can add and delete profiles in the UI.

## Validation

- DNS entries must be valid IPv4 or IPv6 addresses.
- Proxy profiles must be simple `host:port` values.
- IPv6 proxy hosts must use `[address]:port`.
- Proxy profiles cannot contain URL schemes, credentials, whitespace, semicolons, or per-protocol WinINet rules.
- DDNS URLs must use `http://` or `https://`, include a valid host, and have a valid port if one is specified.
- Placeholder `example.com` DDNS URLs are rejected.
- Unknown top-level config keys are dropped during normalization.

## Custom Profiles

Use the DNS and Proxy panels to add custom entries. Saving a profile with an existing DNS name overwrites that profile after validation. Deleting a profile removes it from future dropdowns; the app keeps at least one DNS and one proxy profile so the UI always has a valid selection.

## Privacy

Do not commit `config.json`. It can contain local network details and DDNS tokens. The repository ignores user config, invalid-config backups, logs, diagnostics bundles, virtual environments, and build output.
