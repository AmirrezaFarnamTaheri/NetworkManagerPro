# Troubleshooting

## The App Does Not Start

Check whether another instance is already running in the tray. Lucid Net uses a single-instance guard.

If config is unreadable, the app backs it up as `config.json.<timestamp>.invalid` and creates a fresh default config.

## DNS Does Not Change

Likely causes:

- the app is not elevated;
- the wrong interface is selected;
- PowerShell execution failed;
- a VPN or policy is overriding adapter settings.

Fix:

1. Relaunch as administrator.
2. Select the interface manually in DNS.
3. Apply the profile again.
4. Check `%LOCALAPPDATA%\LucidNet\logs\app.log`.

## Proxy Does Not Behave as Expected

The app changes current-user WinINet proxy registry values. Some apps ignore WinINet and use their own proxy configuration.

If proxy changes keep coming back, another app or policy may be rewriting them. Check History and Settings Monitor.

## DDNS Fails

Likely causes:

- no URL is configured;
- the provider token is wrong;
- the URL has an invalid host or port;
- the provider returned a non-2xx status;
- the network blocks the request.

Fix:

1. Save a valid DDNS URL.
2. Use Force sync DDNS.
3. Review the redacted result in History.

Auto-DDNS retries failed updates with backoff. It does not mark an IP as synced until the provider update succeeds.

## Restore Did Not Revert Everything

Restore points are captured before successful app-driven DNS/proxy changes. They include IPv4 DNS, IPv6 DNS, proxy enable/server, bypass list, and PAC URL.

Changes made outside the app before a restore point was captured cannot be reconstructed.

## Public IP Shows Offline

The public IP endpoint may be blocked or offline. The app caches successful results briefly and backs off after failures.

Check general connectivity and whether your network requires an app-level proxy.

## Build Fails

Run:

```powershell
scripts\build_release.ps1
```

The script cleans stale artifacts and fails if `dist\LucidNet.exe` or `installer\output\LucidNet-Setup-2.0.0.exe` is not produced. Install Inno Setup 6 for release builds. Use `scripts\build_release.ps1 -SkipInstaller` only when you intentionally want a development-only onefile executable.

## Version mismatch during build

Keep these values identical before building:

- `core.APP_VERSION`
- `pyproject.toml` `project.version`
- `installer\LucidNet.iss` `MyAppVersion`

The smoke check and release build both fail when they diverge, which prevents split release metadata.

## Diagnostics Export Fails

Diagnostics export is best-effort. If a log/history file cannot be read, the bundle includes an error note instead of failing the whole export.
