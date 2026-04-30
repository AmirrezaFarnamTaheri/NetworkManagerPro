# ADR-001: Elevated Broker Design

Status: accepted for prototype.

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

The executable command contract is defined in `broker_contract.py`. The first command set is intentionally small:

- `status`: broker health check.
- `dns.set`: privileged DNS server mutation.
- `dns.clear`: privileged DNS reset.
- `hosts.apply_group`: privileged hosts-file managed group apply/disable.
- `firewall.apply_rule`: reserved future command for broker-only firewall mutation.

The contract includes schema version, request ID, command name, arguments, structured success/failure response, sanitized detail, and event payload support.

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

## Migration Plan

1. Keep the GUI standard-user capable and route only broker-owned commands through IPC.
2. Add a harmless broker `status` prototype.
3. Move DNS apply/reset into broker commands.
4. Move hosts-file writes into broker commands after the GUI hosts workflow exists.
5. Reserve firewall and HKLM policy operations for broker/service ownership only.
6. Revisit a persistent Windows Service when enterprise policy, telemetry, or fleet management requires it.

## Failure Behavior

- If the broker is unavailable, the GUI shows a clear failure message and does not attempt a privileged fallback.
- If a command fails validation, the broker rejects it before mutation.
- If a command mutates state and post-checks fail, the GUI records an event and triggers existing rollback logic where applicable.
- All broker results must be safe to include in diagnostics after redaction.

## Acceptance Criteria For Prototype

- The GUI can launch without administrator rights.
- A harmless broker `status` command succeeds through the named pipe.
- Unauthorized callers are rejected.
- Privileged command failures are visible to the user and logged as sanitized events.
- The app still exits cleanly if the broker is unavailable.
