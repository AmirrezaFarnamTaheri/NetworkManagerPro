# CLI And Power Efficiency

Status: implementation note for R-069 and R-070.

## CLI Companion

`nmp_cli.py` provides the first command-line companion surface without changing normal GUI startup.

Current commands:

```powershell
python nmp_cli.py status
python nmp_cli.py status --json
python nmp_cli.py list-dns --json
python nmp_cli.py export-diagnostics --path-only
python nmp_cli.py diagnose captive --i-consent --json
python nmp_cli.py diagnose dns --domain example.com --i-consent --json
python nmp_cli.py diagnose tls --host example.com --i-consent --json
python nmp_cli.py overlay-status --json
python nmp_cli.py multiwan-status --json
python nmp_cli.py anomalies --json
python nmp_cli.py pcap-plan --duration 30 --interface "Wi-Fi" --json
```

The current CLI is read-mostly and support-focused. Future privileged actions such as DNS apply, proxy mutation, hosts edits, and firewall operations must route through the elevated broker once the broker exists.

CLI rules:

- Stable exit code `0` on success.
- Nonzero exit on error.
- Optional JSON output for scripts.
- No GUI initialization for CLI-only commands.
- Active diagnostics require explicit `--i-consent`.
- Frontier commands are read-only or plan-only until reviewed implementation exists.

## Power Efficiency

`power_policy.py` defines a power-aware policy layer:

- Query best-effort Windows battery status.
- Increase polling interval while on battery, battery saver, or minimized.
- Suspend expensive analytics while reduced mode is active.
- Pause UI refresh loops while minimized where safe.

Power policy complements metered-connection awareness. It does not disable core safety checks or user-triggered actions.
