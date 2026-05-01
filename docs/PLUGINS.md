# Plugins

Plugins are trusted local extensions. Normal app startup still loads enabled plugins in-process with the same OS privileges as Lucid Net, while the new `plugin_host.py` subprocess host provides the first isolated execution path for smoke checks and future IPC hardening.

Security warning: the v1 plugin model is trusted-only. Manifest permissions limit access to official PluginAPI helpers, but they do not sandbox Python code. Do not install plugins from unknown publishers or copied code you have not reviewed.

## Locations

User plugins:

```text
%LOCALAPPDATA%\LucidNet\plugins\<plugin_id>\
```

Bundled read-only examples may also be discovered from inside the packaged app.

## Manifest

Each plugin requires `plugin.json`:

```json
{
  "id": "example_plugin",
  "name": "Example Plugin",
  "version": "0.1.0",
  "api_version": "1",
  "entrypoint": "plugin.py",
  "permissions": ["network_state", "events", "ui", "scheduled_tasks"],
  "isolation": "subprocess",
  "dependencies": [],
  "requirements": ""
}
```

Plugin IDs may contain letters, numbers, dot, dash, and underscore. Entrypoints must stay inside the plugin folder.

## Enablement

Plugins load only when their ID is listed in `plugins.enabled`:

```json
{
  "plugins": {
    "enabled": ["example_plugin"],
    "settings": {}
  }
}
```

## Permissions

Manifest permissions are enforced by the v1 PluginAPI:

- `network_state`: allows `api.network_state()`.
- `events`: allows `api.emit_event(...)`.
- `ui`: allows `api.register_tab(...)`.
- `scheduled_tasks`: allows `api.register_periodic_task(...)`.

Permissions are API gates, not a security sandbox. A malicious plugin is still arbitrary Python code inside the elevated process. Missing permissions raise `PermissionError` so plugin authors can see exactly which manifest permission is required.

## Lifecycle

Optional hooks:

```python
def on_start(api):
    ...

def register_ui(api):
    ...

def on_stop(api):
    ...
```

Older no-argument `on_stop()` hooks are accepted. If startup or UI registration fails, any scheduled tasks already started by that plugin are stopped.

## API

- `api.network_state()`: latest monitor snapshot, if permission allows it.
- `api.emit_event(type, summary, details=None)`: append a redacted plugin event to History.
- `api.get_config(default=None)`: plugin-scoped mutable settings dictionary.
- `api.register_tab(title, builder)`: add a UI tab on the Tk main thread.
- `api.register_periodic_task(name, interval_seconds, callback)`: daemon scheduled task, clamped to at least five seconds.

Long-running plugin work must use timeouts and should regularly return. Shutdown is cooperative; blocked plugin code cannot be forcibly killed safely in-process.

## CLI

Useful plugin inspection commands:

```powershell
python lucid_cli.py plugins list --json
python lucid_cli.py plugins host-health --json
python lucid_cli.py plugins env-lock --manifest path\to\plugin.json --json
python lucid_cli.py plugins verify-bundle --dir path\to\plugin --manifest path\to\bundle-manifest.json --json
python lucid_cli.py plugins marketplace-plan --registry path\to\registry.json --json
```

`env-lock` writes deterministic per-plugin dependency metadata under `%LOCALAPPDATA%\LucidNet\plugin_envs\<plugin_id>\environment-lock.json`. It does not install packages yet.

## Marketplace Readiness

The Plugins tab includes a read-only Marketplace readiness grid. It shows registry entries, publisher, install/update action, signature metadata state, and risk classification. Installation remains blocked until signed bundle enforcement and trusted publisher policy are production-ready.
