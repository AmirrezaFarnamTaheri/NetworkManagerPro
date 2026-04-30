# Network Manager Pro

Network Manager Pro is a Windows 10/11 desktop utility for managing DNS profiles, current-user proxy settings, DDNS updates, diagnostics, event history, and lightweight traffic visibility from one tray-enabled app.

The release model is intentionally simple: build one self-contained `NetworkManagerPro.exe`, then wrap it in one installer executable. At runtime the app creates and manages its own user data under `%LOCALAPPDATA%\NetworkManagerPro`.

Supported build/runtime Python versions for source builds are 3.11 through 3.13. End users run the packaged executable and do not need Python installed.

## Core Features

- Apply, reset, add, overwrite, and delete DNS profiles.
- Enable, disable, add, and delete simple `host:port` proxy profiles.
- Preserve and restore DNS, proxy bypass, and PAC settings after app-driven changes.
- Run manual DDNS sync or automatic sync after public IP changes.
- Export sanitized diagnostics bundles for support.
- Track recent actions and detected setting changes in local history.
- Discover trusted plugins from user and bundled plugin folders.
- Run as a tray app with a single-instance guard.

## Runtime Data

- Config: `%LOCALAPPDATA%\NetworkManagerPro\config.json`
- Logs: `%LOCALAPPDATA%\NetworkManagerPro\logs\app.log`
- History: `%LOCALAPPDATA%\NetworkManagerPro\history\events.sqlite3`
- User plugins: `%LOCALAPPDATA%\NetworkManagerPro\plugins\`

The app creates config from built-in defaults on first launch. There is no required loose config file beside the executable.

## Build

```powershell
pip install -r requirements-dev.txt
python scripts\smoke_check.py
scripts\build_release.ps1
```

`scripts\build_release.ps1` creates an isolated `.venv-build`, cleans stale artifacts, verifies release metadata, builds `dist\NetworkManagerPro.exe`, and then builds `installer\output\NetworkManagerPro-Setup-2.0.0.exe`. Inno Setup 6 is required for release builds; use `scripts\build_release.ps1 -SkipInstaller` only for development-only executable checks.

## Documentation

- `docs/QUICKSTART.md`: first-run workflow.
- `docs/USAGE.md`: UI panels and operations.
- `docs/CONFIG.md`: config schema and validation.
- `docs/ARCHITECTURE.md`: code layout, runtime ownership, concurrency, and release contract.
- `docs/INSTALL.md`: build, installer, and runtime layout.
- `docs/PLUGINS.md`: plugin manifest, permissions, and lifecycle.
- `docs/SECURITY_AND_PRIVACY.md`: local data, elevation, diagnostics, and plugin trust.
- `docs/TROUBLESHOOTING.md`: common failures and recovery.
- `docs/GLOSSARY.md`: plain-language terms.
- `SECURITY.md`: reporting and security policy.
- `CHANGELOG.md`: release notes.

## Verification

```powershell
python -m py_compile core.py diagnostics.py gui.py history_store.py main.py monitor_service.py plugin_api.py plugin_manager.py traffic_collector.py scripts\smoke_check.py
python scripts\smoke_check.py
```
