# WASM Plugin Runtime Research

Status: research note for R-052.

## Recommendation

Do not replace the Python plugin model with WASM in the near term. Build subprocess isolation first, then revisit WASM for narrower, untrusted extension points.

## Why

WASM with WASI can provide a stronger capability boundary than in-process Python, but it changes the developer model, complicates packaging, and does not naturally support Tk UI integration. The current product benefits more immediately from subprocess crash containment, explicit IPC, and per-plugin environments.

## Candidate Stack

- `wasmtime-py` for local runtime experiments.
- WASI preview interfaces for limited filesystem and environment access.
- Host-provided imports for event emission and read-only network state.

## Prototype Criteria

1. Load a signed or digest-verified WASM module.
2. Provide a minimal host function for emitting one sanitized event.
3. Deny filesystem and network access by default.
4. Measure startup time and memory overhead.
5. Package the runtime in a PyInstaller build without fragile native dependency issues.

## Decision Gate

WASM should proceed only if it clearly improves safety compared with subprocess Python while keeping plugin authoring practical. Otherwise, keep WASM as a specialized runtime for small policy or diagnostics plugins.
