# Architecture

Network Manager Pro is a Windows desktop app packaged as a PyInstaller onefile executable and installed by a single Inno Setup executable. The installed app does not depend on loose repository files.

## Runtime Layout

- `core.py` owns app constants, runtime paths, config normalization, validation, logging, Windows DNS/proxy operations, DDNS calls, and redaction helpers.
- `main.py` owns startup, elevation, single-instance protection, tray integration, service lifetime, plugin loading, and graceful shutdown.
- `gui.py` owns the CustomTkinter interface and dispatches slow operations to background worker threads.
- `monitor_service.py` owns the single polling loop for effective network state, external config reloads, settings-change events, and automatic DDNS updates.
- `history_store.py` stores local event history as JSON lines with rotation.
- `diagnostics.py` exports redacted diagnostics bundles.
- `traffic_collector.py` provides best-effort process connection summaries.
- `plugin_manager.py` and `plugin_api.py` load trusted plugins from bundled and user plugin folders.

## Data Ownership

User-writable data lives under `%LOCALAPPDATA%\NetworkManagerPro`:

- `config.json`: normalized user configuration.
- `logs\app.log`: rotating app log.
- `history\events.jsonl`: local event history.
- `plugins\`: optional user-installed plugins.

Bundled docs, assets, and example plugins are embedded into `NetworkManagerPro.exe` by PyInstaller. They are not required beside the installed executable.

## Concurrency Model

The GUI remains the owner of visible UI state. Slow DNS, proxy, DDNS, diagnostics, and traffic operations run in short-lived background threads and report back through Tk's event loop. The monitor service runs one daemon thread and protects snapshots with a re-entrant lock. Config reads and writes use the shared `core.config_lock()` plus atomic file replacement so UI saves, monitor reloads, and plugin reads do not race inside one process.

Plugin periodic tasks are tracked before their worker thread starts, so shutdown can signal every registered task even if a plugin starts while the app is closing.

## Release Contract

The repository source of truth for the current release is `core.APP_VERSION`; `pyproject.toml` and `installer\NetworkManagerPro.iss` must match it. `scripts\smoke_check.py` verifies this, and `scripts\build_release.ps1` refuses to build if the versions diverge.

Release builds are intentionally clean:

1. Remove generated `build`, `dist`, and `installer\output` folders inside the repository.
2. Build `dist\NetworkManagerPro.exe` as a PyInstaller onefile executable.
3. Build `installer\output\NetworkManagerPro-Setup-<version>.exe`.

Generated artifacts are ignored by Git and should not be committed.
