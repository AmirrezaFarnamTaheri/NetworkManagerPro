# Architecture

Lucid Net is a Windows desktop app packaged as a PyInstaller onefile executable and installed by a single Inno Setup executable. The installed app does not depend on loose repository files.

## Runtime Layout

- `core.py` owns app constants, runtime paths, config normalization, validation, logging, Windows DNS/proxy operations, DDNS calls, and redaction helpers.
- `main.py` owns startup, elevation, single-instance protection, tray integration, service lifetime, plugin loading, and graceful shutdown.
- `gui.py` owns the CustomTkinter interface and dispatches slow operations to background worker threads.
- `monitor_service.py` owns the single polling loop for effective network state, external config reloads, settings-change events, and automatic DDNS updates.
- `history_store.py` stores local event history in SQLite with WAL enabled.
- `diagnostics.py` exports redacted diagnostics bundles.
- `traffic_collector.py` provides best-effort process connection summaries.
- `plugin_manager.py` and `plugin_api.py` load trusted plugins from bundled and user plugin folders.
- `plugin_platform.py` and `plugin_host.py` define the plugin isolation, environment-lock, bundle-integrity, and marketplace-readiness primitives that will become the subprocess plugin boundary.

## Data Ownership

User-writable data lives under `%LOCALAPPDATA%\LucidNet`:

- `config.json`: normalized user configuration.
- `logs\app.log`: rotating app log.
- `history\events.sqlite3`: local event history.
- `history\traffic_metrics.sqlite3`: aggregate traffic metrics from manual refreshes.
- `plugins\`: optional user-installed plugins.

Bundled docs, assets, and example plugins are embedded into `LucidNet.exe` by PyInstaller. They are not required beside the installed executable.

## Concurrency Model

The GUI remains the owner of visible UI state. Slow DNS, proxy, DDNS, diagnostics, and traffic operations run in short-lived background threads and report back through Tk's event loop. The monitor service runs one daemon thread and protects snapshots with a re-entrant lock. Config reads and writes use the shared `core.config_lock()` plus atomic file replacement so UI saves, monitor reloads, and plugin reads do not race inside one process.

Plugin periodic tasks are tracked before their worker thread starts, so shutdown can signal every registered task even if a plugin starts while the app is closing. Plugin reload can now target changed manifests instead of restarting every enabled plugin.

## Privilege Direction

The current packaged app can still perform privileged operations from the main process, but the accepted architecture path is a standard-user GUI plus an on-demand elevated broker. The GUI owns presentation, validation, config editing, diagnostics, trusted plugin discovery, and read-only status. The broker will own privileged mutations such as DNS changes, hosts-file writes, future firewall operations, and future HKLM policy setup.

The broker command surface starts in `broker_contract.py` so request/response validation can be tested before a live named-pipe server exists. The initial IPC target is an ACL-secured local named pipe with request IDs, schema versioning, timeouts, audit events, and sanitized errors. The Windows Service option is deferred until enterprise and persistent-management requirements justify the installer and attack-surface cost.

## Release Contract

The repository source of truth for the current release is `branding.PRODUCT_VERSION`, exposed as `core.APP_VERSION`; `pyproject.toml` and `installer\LucidNet.iss` must match it. `scripts\smoke_check.py` verifies this, and `scripts\build_release.ps1` refuses to build if the versions diverge.

Release builds are intentionally clean:

1. Remove generated `build`, `dist`, and `installer\output` folders inside the repository.
2. Build `dist\LucidNet.exe` as a PyInstaller onefile executable.
3. Build `installer\output\LucidNet-Setup-<version>.exe`.

Generated artifacts are ignored by Git and should not be committed.
