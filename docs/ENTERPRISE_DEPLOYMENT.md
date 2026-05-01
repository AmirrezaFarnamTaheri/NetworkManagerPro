# Enterprise Deployment

Status: implementation and deployment guide for R-041, R-042, R-045, and R-046.

## Machine Policy

Lucid Net reserves this policy root:

```text
HKLM\SOFTWARE\Policies\LucidNet
```

Machine policy handling is implemented in `enterprise_policy.py` and applied during startup before the GUI, monitor, plugins, and event history are initialized. ADMX/ADML templates live under `enterprise\` and use the same policy names as `enterprise_policy.py`.

| Policy | Type | Behavior |
|---|---|---|
| `DisablePlugins` | DWORD/bool | Clears enabled plugin IDs. |
| `DisableProxyChanges` | DWORD/bool | Marks proxy mutation as managed-disabled. |
| `DisableDiagnosticsExport` | DWORD/bool | Marks diagnostics export as managed-disabled. |
| `DisableAutoUpdates` | DWORD/bool | Marks update behavior as managed-disabled. |
| `EnableWindowsEventLogExport` | DWORD/bool | Mirrors sanitized app history events to Windows Event Log after source registration. |
| `ForceRollbackOnConnectivityLoss` | DWORD/bool | Forces rollback policy on or off. |
| `MinimumCheckIntervalSeconds` | DWORD/int | Raises monitor interval to the configured minimum. |

Policy values override user config and are displayed as managed state in the UI before controls are locked.

## Administrative Templates

Copy these files to a Central Store or local PolicyDefinitions folder:

```text
enterprise\LucidNet.admx
enterprise\en-US\LucidNet.adml
```

The current template covers the primary machine policies and can be extended as additional policy keys graduate from research to release.

## Intune Model

Recommended Intune packaging path:

1. Build the Inno Setup installer.
2. Wrap `LucidNet-Setup-<version>.exe` with Microsoft Win32 Content Prep Tool.
3. Install command:

```powershell
LucidNet-Setup-1.0.0.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
```

4. Uninstall command:

```powershell
"%ProgramFiles%\Lucid Net\unins000.exe" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
```

5. Detection rule:

```text
File exists: %ProgramFiles%\Lucid Net\LucidNet.exe
```

Machine policy keys can be deployed with Intune Settings Catalog custom OMA-URI, PowerShell, or ADMX ingestion.

## GPO Model

Initial GPO deployment uses:

- Computer startup script for silent installation.
- Group Policy Preferences Registry items for `HKLM\SOFTWARE\Policies\LucidNet`.
- Optional file detection or software inventory for version reporting.

GPO deployment can also import the included ADMX/ADML templates into the Central Store.

## Silent Install And Uninstall

Inno Setup already supports silent mode. Supported commands:

```powershell
LucidNet-Setup-1.0.0.exe /SILENT /SUPPRESSMSGBOXES /NORESTART
LucidNet-Setup-1.0.0.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
"%ProgramFiles%\Lucid Net\unins000.exe" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
```

Default uninstall preserves `%LOCALAPPDATA%\LucidNet` so user config, logs, diagnostics, and history are not destroyed. Enterprise data removal is explicit: run the uninstaller with `/PURGEUSERDATA` when policy permits removing per-user app data.

## Code Signing And Verification

Release trust requires:

1. Sign `dist\LucidNet.exe`.
2. Build and sign `installer\output\LucidNet-Setup-<version>.exe`.
3. Verify Authenticode signatures.
4. Generate a SHA256 release manifest.
5. Publish the manifest beside the installer.

`scripts\build_release.ps1` writes `release-manifest.json` for the executable-only path and for the full installer path. It also signs and verifies artifacts when `LUCID_NET_SIGNING_CERT_PATH` or `-SigningCertPath` is supplied. `release_verification.py` provides testable SHA256 manifest creation, manifest verification, signing-plan metadata, and a `signtool verify` wrapper. The signing certificate and timestamp URL should be supplied by CI secrets, not committed to the repository.
