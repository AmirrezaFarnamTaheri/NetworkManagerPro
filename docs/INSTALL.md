# Install and Build

Lucid Net supports 64-bit Windows 10/11.

## Release Shape

The release has two executable artifacts:

- `dist\LucidNet.exe`: a self-contained PyInstaller onefile app executable.
- `installer\output\LucidNet-Setup-1.0.0.exe`: a single Inno Setup installer that installs the app executable.

The app creates runtime config, logs, history, and user plugin folders under `%LOCALAPPDATA%\LucidNet`. It does not need loose JSON, docs, assets, or plugin files beside the installed executable.

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
5. Verifies that `core.py`, `pyproject.toml`, and `installer\LucidNet.iss` all use the same version.
6. Builds `dist\LucidNet.exe`.
7. Builds `installer\output\LucidNet-Setup-1.0.0.exe`.
8. Fails if either expected executable is missing.

For a development-only onefile executable check without the installer, run:

```powershell
scripts\build_release.ps1 -SkipInstaller
```

## Silent Enterprise Install

The Inno Setup installer supports standard silent switches:

```powershell
LucidNet-Setup-1.0.0.exe /SILENT /SUPPRESSMSGBOXES /NORESTART
LucidNet-Setup-1.0.0.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
"%ProgramFiles%\Lucid Net\unins000.exe" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
```

Uninstall preserves `%LOCALAPPDATA%\LucidNet` by default. Enterprise cleanup of user data must be explicit so config, logs, diagnostics, and history are not removed accidentally. To remove per-user app data during uninstall, pass `/PURGEUSERDATA` to the uninstaller.

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
$files = Get-ChildItem -Path . -Filter *.py -Recurse | Where-Object { $_.FullName -notmatch '\\.venv' -and $_.FullName -notmatch '\\.venv-build' -and $_.FullName -notmatch '\\build\\' -and $_.FullName -notmatch '\\dist\\' } | ForEach-Object { $_.FullName }
python -m py_compile @files
python -m pytest
python scripts\smoke_check.py
```

## Elevation

The app requests administrator rights on startup because DNS changes require elevation. Current-user proxy, DDNS, diagnostics, history, and plugins are also run inside that elevated process, so only trusted plugins should be enabled.
