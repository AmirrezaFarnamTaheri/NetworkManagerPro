# Lucid Net

Safe Windows network control, diagnostics, and automation.

[![License: AGPL-3.0-only](https://img.shields.io/badge/License-AGPL--3.0--only-blue.svg)](LICENSE)
[![Python 3.11-3.13](https://img.shields.io/badge/Python-3.11--3.13-blue.svg)](https://www.python.org/)
[![Windows 10/11](https://img.shields.io/badge/Windows-10%2F11-0078d4.svg)](https://www.microsoft.com/windows)

Lucid Net is a local-first Windows 10/11 desktop utility for DNS profiles, current-user proxy settings, DDNS updates, diagnostics, event history, lightweight traffic visibility, and trusted local plugins. It is designed as a tray-enabled operations console: practical for daily network switching, careful about rollback and redaction, and explicit about which ambitious features are still research.

Current release: `v1.0.0`

## What Lucid Net Does

- Applies, resets, adds, overwrites, and deletes DNS profiles for selected Windows interfaces.
- Supports IPv4 and IPv6 DNS server validation.
- Enables and disables current-user WinINet proxy profiles.
- Supports simple proxy endpoints, PAC profiles, and SOCKS5 endpoints with validation.
- Captures restore points and can roll back app-driven DNS/proxy changes after connectivity loss.
- Saves DDNS update URLs through Windows Credential Manager via `keyring` for new saves.
- Runs manual DDNS sync and optional automatic sync after public IP changes.
- Supports separate IPv4 and IPv6 DDNS update URLs.
- Exports sanitized diagnostics bundles from local app state.
- Stores event history in SQLite with WAL enabled.
- Stores aggregate traffic metrics in SQLite for short-term trend review.
- Shows best-effort process connection inventory through `psutil`.
- Provides context-aware profile previews and auto-apply rules by SSID, BSSID, interface alias, and gateway.
- Pauses profile auto-apply when captive portal detection says login is required.
- Provides a safety-first hosts-file manager with preview, app-owned markers, and backups.
- Discovers trusted plugins from bundled and user plugin folders.
- Exposes a CLI companion for status, DNS, proxy, DDNS, hosts, diagnostics, traffic history, plugins, branding, and research gates.
- Includes enterprise readiness pieces: ADMX/ADML templates, HKLM policy overrides, Windows Event Log mirroring, silent installer switches, and release manifest/signing helpers.

## What It Does Not Claim

Lucid Net is not a VPN client, packet capture suite, packet interception tool, firewall replacement, or operational evasion product. ETW per-process bandwidth, WFP, WinDivert, PCAP export, overlay orchestration, plugin marketplace installation, persistent Windows Service architecture, and advanced anti-censorship ideas are tracked as gated research or frontier work in [docs/RESEARCH_AND_FRONTIER_BACKLOG.md](docs/RESEARCH_AND_FRONTIER_BACKLOG.md).

The shipped product may diagnose network behavior and recommend lawful, user-consented local configuration changes. Features involving policy bypass, traffic camouflage, identity rotation, or anti-censorship countermeasures require legal, ethical, safety, and feasibility review before implementation.

## Runtime Data

Lucid Net creates its runtime data under:

```text
%LOCALAPPDATA%\LucidNet
```

Important paths:

- Config: `%LOCALAPPDATA%\LucidNet\config.json`
- Logs: `%LOCALAPPDATA%\LucidNet\logs\app.log`
- Event history: `%LOCALAPPDATA%\LucidNet\history\events.sqlite3`
- Traffic metrics: `%LOCALAPPDATA%\LucidNet\history\traffic_metrics.sqlite3`
- User plugins: `%LOCALAPPDATA%\LucidNet\plugins\`
- Plugin environment metadata: `%LOCALAPPDATA%\LucidNet\plugin_envs\`

The packaged executable does not require loose config, docs, assets, or plugin files beside it. Built-in defaults create the first config automatically.

## Installation

The normal release shape is:

- `dist\LucidNet.exe`: self-contained PyInstaller onefile executable.
- `installer\output\LucidNet-Setup-1.0.0.exe`: Inno Setup installer wrapping the executable.

After a release is published, download the installer from GitHub Releases and run it. The installer requires administrator privileges because Lucid Net changes Windows network settings.

For silent deployment:

```powershell
LucidNet-Setup-1.0.0.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
```

Uninstall preserves `%LOCALAPPDATA%\LucidNet` by default. To remove per-user app data intentionally, pass `/PURGEUSERDATA` to the uninstaller.

## Build From Source

Requirements:

- Windows 10/11 x64.
- Python 3.11, 3.12, or 3.13.
- Inno Setup 6 for installer builds.
- PowerShell 5.1 or later.

Build and verify:

```powershell
pip install -r requirements-dev.txt
python scripts\smoke_check.py
python -m pytest
scripts\build_release.ps1
```

Development-only executable build:

```powershell
scripts\build_release.ps1 -SkipInstaller
```

The build script cleans generated `build`, `dist`, and `installer\output` folders, creates an isolated `.venv-build`, regenerates icons from `assets\logo.svg`, verifies version consistency, builds `dist\LucidNet.exe`, and then invokes Inno Setup.

Directly compiling `installer\LucidNet.iss` requires `dist\LucidNet.exe` to exist first. If it is missing, the installer script now fails with an explicit message telling you to run the release build script first.

## Development Run

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Install development tools when you need tests and release checks:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

## CLI

Source checkouts can run:

```powershell
python lucid_cli.py status --json
python lucid_cli.py about --json
python lucid_cli.py dns list --json
python lucid_cli.py dns apply --profile Cloudflare --interface "Wi-Fi" --json
python lucid_cli.py dns clear --interface "Wi-Fi" --json
python lucid_cli.py proxy status --json
python lucid_cli.py proxy pac --url https://proxy.example/wpad.pac --json
python lucid_cli.py proxy socks5 --server 127.0.0.1:1080 --json
python lucid_cli.py ddns force --dual-stack --json
python lucid_cli.py export-diagnostics --path-only
python lucid_cli.py diagnose captive --i-consent --json
python lucid_cli.py traffic-history --limit 24 --json
python lucid_cli.py plugins list --json
python lucid_cli.py frontier status --json
```

Package installs expose the console command:

```powershell
lucid-net status --json
```

Privileged CLI actions currently use the same core functions as the GUI. Once the elevated broker is complete, DNS, proxy, hosts, firewall, and other privileged mutations should route through that broker.

## Architecture

The current codebase is intentionally flat and direct:

- `branding.py`: product name, version, brand architecture, panel families, and safety boundary.
- `core.py`: constants, runtime paths, config normalization, validation, logging, Windows DNS/proxy operations, DDNS, restore points, and redaction helpers.
- `main.py`: startup, elevation, single-instance guard, tray integration, monitor lifetime, plugin loading, and shutdown.
- `gui.py`: CustomTkinter interface and background dispatch for slow actions.
- `monitor_service.py`: effective network state polling, config reloads, settings-change events, and automatic DDNS checks.
- `history_store.py`: SQLite event history.
- `traffic_collector.py`: aggregate counters and best-effort process connection summaries.
- `diagnostics.py` and `deep_diagnostics.py`: redacted support bundles and consent-gated network evidence checks.
- `plugin_manager.py`, `plugin_api.py`, `plugin_platform.py`, and `plugin_host.py`: trusted plugin loading plus isolation and marketplace-readiness groundwork.
- `broker_contract.py` and `broker_runtime.py`: elevated broker request/response contract and initial runtime policy shape.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full release and privilege-separation direction.

## Security And Privacy

- Runtime data stays local under `%LOCALAPPDATA%\LucidNet`.
- The app does not include general telemetry.
- Built-in outbound calls are limited to public IP lookup, user-configured DDNS updates, and explicit consent-gated diagnostics.
- Diagnostics and history redact DDNS tokens, common secret fields, proxy credentials, and plugin event details where possible.
- The current packaged app requests administrator rights on startup because DNS changes require elevation.
- The v1 plugin model is trusted-only. Manifest permissions gate official API helpers, but Python plugins are not a hard sandbox.

Report security issues privately using the process in [SECURITY.md](SECURITY.md).

## Documentation

- [docs/QUICKSTART.md](docs/QUICKSTART.md): first-run workflow.
- [docs/USAGE.md](docs/USAGE.md): UI panels and operations.
- [docs/CONFIG.md](docs/CONFIG.md): config schema and validation.
- [docs/INSTALL.md](docs/INSTALL.md): build, installer, silent deployment, and runtime layout.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): code layout, runtime ownership, concurrency, and release contract.
- [docs/PLUGINS.md](docs/PLUGINS.md): plugin manifest, permissions, lifecycle, and marketplace readiness.
- [docs/SECURITY_AND_PRIVACY.md](docs/SECURITY_AND_PRIVACY.md): local data, elevation, diagnostics, and plugin trust.
- [docs/CLI_AND_POWER_MODE.md](docs/CLI_AND_POWER_MODE.md): CLI companion and reduced background work policy.
- [docs/ENTERPRISE_DEPLOYMENT.md](docs/ENTERPRISE_DEPLOYMENT.md): ADMX/GPO/Intune, policy keys, Event Log, signing, and silent deployment.
- [docs/PRODUCT_VISION_AND_BRANDING.md](docs/PRODUCT_VISION_AND_BRANDING.md): product identity, panel family names, and safety boundary.
- [docs/RESEARCH_AND_FRONTIER_BACKLOG.md](docs/RESEARCH_AND_FRONTIER_BACKLOG.md): gated research and frontier work.
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md): common failures and recovery.
- [docs/GLOSSARY.md](docs/GLOSSARY.md): plain-language terms.
- [Audit and plan.md](Audit%20and%20plan.md): living audit, roadmap, item progress, and implementation bookkeeping.

## Verification

```powershell
$files = Get-ChildItem -Path . -Filter *.py -Recurse | Where-Object { $_.FullName -notmatch '\\.venv' -and $_.FullName -notmatch '\\.venv-build' -and $_.FullName -notmatch '\\build\\' -and $_.FullName -notmatch '\\dist\\' } | ForEach-Object { $_.FullName }
python -m py_compile @files
python -m pytest
python scripts\smoke_check.py
cargo check --manifest-path sidecars\forensics-sidecar-rust\Cargo.toml
```

## License

Lucid Net is licensed under the GNU Affero General Public License v3.0 only. See [LICENSE](LICENSE).
