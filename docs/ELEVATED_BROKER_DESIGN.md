# Elevated Broker Design

Status: architecture decision note for privilege separation research.

## Decision

Use a staged on-demand elevated broker first, then revisit a full Windows Service after the command surface and installer contract are stable.

This keeps the initial implementation smaller than a service migration while still moving privileged mutations out of the GUI process. The broker should be a minimal local process launched only when an operation requires elevation. The standard-user GUI remains responsible for UI, config editing, diagnostics display, and non-privileged reads.

## Responsibilities

The standard-user GUI owns:

- Window, tray, and user interaction.
- Config editing and validation.
- Read-only status display.
- Plugin discovery for trusted local plugins until plugin subprocess isolation exists.
- Diagnostics presentation and export orchestration.

The elevated broker owns:

- DNS apply and reset operations.
- Future hosts file edits.
- Future firewall and per-app block operations.
- Future HKLM policy setup tasks that require elevation.
- Auditable privileged command results.

## IPC Direction

Use a local named pipe with explicit access control as the first IPC target:

- Restrict callers to the current interactive user.
- Use a small request/response JSON schema.
- Include command name, request ID, schema version, and arguments.
- Return success, user-safe message, sanitized technical detail, and optional event payload.
- Apply strict timeouts and fail closed if the broker cannot be reached.

## Service Comparison

An on-demand broker is preferred first because:

- It has less installer complexity.
- It avoids a persistent SYSTEM process during early architecture work.
- It is easier to replace if the command contract changes.
- It still proves the security boundary and IPC model.

A Windows Service should be reconsidered when:

- Enterprise policy support requires persistent management.
- Background enforcement or telemetry requires a stable service host.
- Silent deployment and fleet management become first-class release goals.

## Acceptance Criteria For Prototype

- The GUI can launch without administrator rights.
- A harmless broker `status` command succeeds through the named pipe.
- Unauthorized callers are rejected.
- Privileged command failures are visible to the user and logged as sanitized events.
- The app still exits cleanly if the broker is unavailable.
