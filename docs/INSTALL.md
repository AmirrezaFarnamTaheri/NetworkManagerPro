# Install and Build

Network Manager Pro supports 64-bit Windows 10/11.

## Release Shape

The release has two executable artifacts:

- `dist\NetworkManagerPro.exe`: a self-contained PyInstaller onefile app executable.
- `installer\output\NetworkManagerPro-Setup-2.0.0.exe`: a single Inno Setup installer that installs the app executable.

The app creates runtime config, logs, history, and user plugin folders under `%LOCALAPPDATA%\NetworkManagerPro`. It does not need loose JSON, docs, assets, or plugin files beside the installed executable.

## Build the Installer

Install these tools first:

- Python 3.11, 3.12, or 3.13.
- Inno Setup 6.

From the repository root:

```powershell
scripts\build_release.ps1
```

The script:

1. Removes stale `build`, `dist`, and `installer\output` folders.
2. Creates `.venv-build` if needed.
3. Installs runtime and PyInstaller dependencies into that isolated build environment.
4. Regenerates icons.
5. Verifies that `core.py`, `pyproject.toml`, and `installer\NetworkManagerPro.iss` all use the same version.
6. Builds `dist\NetworkManagerPro.exe`.
7. Builds `installer\output\NetworkManagerPro-Setup-2.0.0.exe`.
8. Fails if either expected executable is missing.

For a development-only onefile executable check without the installer, run:

```powershell
scripts\build_release.ps1 -SkipInstaller
```

## Silent Enterprise Install

The Inno Setup installer supports standard silent switches:

```powershell
NetworkManagerPro-Setup-2.0.0.exe /SILENT /SUPPRESSMSGBOXES /NORESTART
NetworkManagerPro-Setup-2.0.0.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
"%ProgramFiles%\Network Manager Pro\unins000.exe" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
```

Uninstall preserves `%LOCALAPPDATA%\NetworkManagerPro` by default. Enterprise cleanup of user data must be explicit so config, logs, diagnostics, and history are not removed accidentally.

For Intune, GPO, policy keys, and release verification, see `docs\ENTERPRISE_DEPLOYMENT.md`.

## Development Run

Use a normal virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

For maintenance tools:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

## Verification

```powershell
python -m py_compile core.py diagnostics.py gui.py history_store.py main.py monitor_service.py plugin_api.py plugin_manager.py traffic_collector.py scripts\smoke_check.py
python scripts\smoke_check.py
```

## Elevation

The app requests administrator rights on startup because DNS changes require elevation. Current-user proxy, DDNS, diagnostics, history, and plugins are also run inside that elevated process, so only trusted plugins should be enabled.
