# Plugin Platform Roadmap

Status: implementation and research note for R-047 through R-052.

## Current Boundary

The v1 plugin model remains trusted-only for normal app startup. Capability validation is centralized in `plugin_platform.py` and enforced by `plugin_manager.py`. A first `plugin_host.py` subprocess host now exists for isolated smoke execution, health checks, and future IPC hardening.

## Subprocess Isolation

The first isolated runtime should use one plugin host subprocess per enabled plugin. The host process receives a narrow request contract, runs with timeouts, and reports sanitized events back to the main app. A plugin crash should terminate only that plugin host, not the GUI.

Current implementation:

- `plugin_platform.isolation_plan(...)` defines host command, timeout, venv path, and permissions.
- `plugin_host.py` exposes a JSON-line health command and a `run-once` command that loads one manifest in a separate process boundary.
- `broker_contract.py` gives the pattern for request IDs, schema versions, and structured responses.
- CLI command `nmp plugins host-health --json` verifies the host contract.

Remaining work:

- Move PluginAPI calls through IPC.
- Restart crashed plugin hosts with backoff.
- Route plugin UI contributions through a safe host-to-GUI registration channel.

## Per-Plugin Virtual Environments

Each plugin receives a deterministic environment path under:

```text
%LOCALAPPDATA%\LucidNet\plugin_envs\<plugin_id>
```

Manifest metadata can now define `dependencies` and `requirements`. `plugin_platform.environment_spec(...)`, `write_environment_lock(...)`, and `create_plugin_environment(...)` create deterministic per-plugin virtual environments and write `environment-lock.json` metadata. Dependency installation is explicit and failure-contained so the host app never installs plugin dependencies into its own runtime environment.

## Hot Reload

`PluginManager.changed_manifests()` detects manifest or entrypoint fingerprint changes. `PluginManager.reload_changed()` stops and reloads only changed enabled plugins; `reload_enabled()` still exists for a full manual reload.

Future subprocess mode should restart only changed plugin hosts with crash backoff.

## Signed Bundles

`plugin_platform.bundle_manifest(...)` creates a file digest manifest for a plugin folder and `verify_bundle_manifest(...)` detects missing, changed, or escaping paths. `plugin_platform.signed_bundle_metadata(...)`, `verify_signed_bundle(...)`, and `install_plugin_bundle(...)` define the signed bundle enforcement path so the install workflow can reject missing publishers, untrusted publishers, mismatched bundle digests, and research-only signatures before extraction is trusted.

Remaining signature work must define:

- Bundle archive format.
- Publisher identity.
- Signature algorithm.
- Key rotation.
- Revocation.
- Offline verification behavior.

## Marketplace Registry

`plugin_platform.parse_marketplace_registry(...)` defines the first registry shape, and `marketplace_install_plan(...)` turns registry entries into user-visible install/update/readiness rows:

```json
{
  "schema_version": 1,
  "plugins": [
    {
      "id": "example",
      "name": "Example",
      "version": "1.0.0",
      "publisher": "Example Publisher",
      "bundle_url": "https://plugins.example/example.nmp-plugin",
      "sha256": "...",
      "permissions": ["events"],
      "signature": {}
    }
  ]
}
```

The GUI Plugins tab now includes a Marketplace readiness grid backed by `plugins.marketplace_registry` config. `plugin_platform.marketplace_operation(...)` gates install, update, remove, and inspect actions against signed metadata readiness. The CLI can inspect the same plan with `nmp plugins marketplace-plan --registry registry.json --json`.

## WASM Research

WASM is not the first implementation path. Subprocess isolation is more compatible with the current Python plugin ecosystem. WASM remains a research option for future untrusted extensions if packaging, WASI capability limits, and developer experience prove acceptable.
