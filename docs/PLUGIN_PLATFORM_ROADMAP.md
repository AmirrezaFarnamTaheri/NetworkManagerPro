# Plugin Platform Roadmap

Status: implementation and research note for R-047 through R-052.

## Current Boundary

The v1 plugin model remains trusted-only. Python plugins still run in-process today, but capability validation is now centralized in `plugin_platform.py` and enforced by `plugin_manager.py`.

## Subprocess Isolation

The first isolated runtime should use one plugin host subprocess per enabled plugin. The host process receives a narrow request contract, runs with timeouts, and reports sanitized events back to the main app. A plugin crash should terminate only that plugin host, not the GUI.

Current scaffolding:

- `plugin_platform.isolation_plan(...)` defines host command, timeout, venv path, and permissions.
- `broker_contract.py` gives the pattern for request IDs, schema versions, and structured responses.

Remaining work:

- Build `plugin_host.py`.
- Move PluginAPI calls through IPC.
- Restart crashed plugin hosts with backoff.
- Route plugin UI contributions through a safe host-to-GUI registration channel.

## Per-Plugin Virtual Environments

Each plugin receives a deterministic environment path under:

```text
%LOCALAPPDATA%\NetworkManagerPro\plugin_envs\<plugin_id>
```

Manifest metadata should later define dependency files or lock files. The host app must never install dependencies into its own runtime environment.

## Hot Reload

`PluginManager.changed_manifests()` can now detect manifest or entrypoint fingerprint changes. `PluginManager.reload_enabled()` stops all plugin tasks before reloading enabled plugins.

Future subprocess mode should restart only changed plugin hosts.

## Signed Bundles

`plugin_platform.bundle_manifest(...)` creates a file digest manifest for a plugin folder and `verify_bundle_manifest(...)` detects missing, changed, or escaping paths. This is integrity scaffolding, not publisher identity yet.

Future signature work must define:

- Bundle archive format.
- Publisher identity.
- Signature algorithm.
- Key rotation.
- Revocation.
- Offline verification behavior.

## Marketplace Registry

`plugin_platform.parse_marketplace_registry(...)` defines the first registry shape:

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

Marketplace UI must show publisher, permissions, digest/signature state, update status, and risk warnings before install.

## WASM Research

WASM is not the first implementation path. Subprocess isolation is more compatible with the current Python plugin ecosystem. WASM remains a research option for future untrusted extensions if packaging, WASI capability limits, and developer experience prove acceptable.
