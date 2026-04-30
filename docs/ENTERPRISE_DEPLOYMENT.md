# Enterprise Deployment

Status: implementation and deployment guide for R-041, R-042, R-045, and R-046.

## Machine Policy

Network Manager Pro reserves this policy root:

```text
HKLM\SOFTWARE\Policies\NetworkManagerPro
```

Current policy scaffolding is implemented in `enterprise_policy.py`. The GUI integration and ADMX packaging are future work, but the precedence model is now defined and testable.

| Policy | Type | Behavior |
|---|---|---|
| `DisablePlugins` | DWORD/bool | Clears enabled plugin IDs. |
| `DisableProxyChanges` | DWORD/bool | Marks proxy mutation as managed-disabled. |
| `DisableDiagnosticsExport` | DWORD/bool | Marks diagnostics export as managed-disabled. |
| `DisableAutoUpdates` | DWORD/bool | Marks update behavior as managed-disabled. |
| `ForceRollbackOnConnectivityLoss` | DWORD/bool | Forces rollback policy on or off. |
| `MinimumCheckIntervalSeconds` | DWORD/int | Raises monitor interval to the configured minimum. |

Policy values override user config and should be displayed as managed state in the UI before controls are locked.

## Intune Model

Recommended Intune packaging path:

1. Build the Inno Setup installer.
2. Wrap `NetworkManagerPro-Setup-<version>.exe` with Microsoft Win32 Content Prep Tool.
3. Install command:

```powershell
NetworkManagerPro-Setup-2.0.0.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
```

4. Uninstall command:

```powershell
"%ProgramFiles%\Network Manager Pro\unins000.exe" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
```

5. Detection rule:

```text
File exists: %ProgramFiles%\Network Manager Pro\NetworkManagerPro.exe
```

Machine policy keys can be deployed with Intune Settings Catalog custom OMA-URI, PowerShell, or future ADMX ingestion.

## GPO Model

Initial GPO deployment uses:

- Computer startup script for silent installation.
- Group Policy Preferences Registry items for `HKLM\SOFTWARE\Policies\NetworkManagerPro`.
- Optional file detection or software inventory for version reporting.

Future work: ship ADMX/ADML templates after the policy set stabilizes.

## Silent Install And Uninstall

Inno Setup already supports silent mode. Supported commands:

```powershell
NetworkManagerPro-Setup-2.0.0.exe /SILENT /SUPPRESSMSGBOXES /NORESTART
NetworkManagerPro-Setup-2.0.0.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
"%ProgramFiles%\Network Manager Pro\unins000.exe" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
```

Default uninstall preserves `%LOCALAPPDATA%\NetworkManagerPro` so user config, logs, diagnostics, and history are not destroyed. Enterprise data removal must be explicit, for example through a separate admin cleanup script or future installer option.

## Code Signing And Verification

Release trust requires:

1. Sign `dist\NetworkManagerPro.exe`.
2. Build and sign `installer\output\NetworkManagerPro-Setup-<version>.exe`.
3. Verify Authenticode signatures.
4. Generate a SHA256 release manifest.
5. Publish the manifest beside the installer.

`release_verification.py` provides testable SHA256 manifest creation, manifest verification, and a `signtool verify` wrapper. The signing certificate and timestamp URL should be supplied by CI secrets, not committed to the repository.
