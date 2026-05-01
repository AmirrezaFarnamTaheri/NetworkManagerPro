# CLI And Power Efficiency

Status: implementation note for R-069 and R-070.

## CLI Companion

`lucid_cli.py` provides the command-line companion surface without changing normal GUI startup. Source checkouts can run `python lucid_cli.py ...`; package installs expose the `lucid-net` console command through `pyproject.toml`.

Current commands:

```powershell
python lucid_cli.py status
python lucid_cli.py status --json
python lucid_cli.py about --json
python lucid_cli.py vision --json
python lucid_cli.py brand --json
python lucid_cli.py profiles preview --ssid CorpWifi --json
python lucid_cli.py list-dns --json
python lucid_cli.py dns list --json
python lucid_cli.py dns apply --profile Cloudflare --interface "Wi-Fi" --json
python lucid_cli.py dns apply --servers 1.1.1.1 1.0.0.1 --interface "Wi-Fi" --json
python lucid_cli.py dns clear --interface "Wi-Fi" --json
python lucid_cli.py proxy status --json
python lucid_cli.py proxy enable --server 127.0.0.1:8080 --json
python lucid_cli.py proxy pac --url https://proxy.example/wpad.pac --json
python lucid_cli.py proxy socks5 --server 127.0.0.1:1080 --json
python lucid_cli.py proxy disable --json
python lucid_cli.py ddns force --json
python lucid_cli.py ddns force --dual-stack --json
python lucid_cli.py hosts preview --file C:\Windows\System32\drivers\etc\hosts --group dev --entry 10.0.0.2,dev.local,dev --json
python lucid_cli.py hosts apply --file C:\Windows\System32\drivers\etc\hosts --group dev --entry 10.0.0.2,dev.local,dev --json
python lucid_cli.py export-diagnostics --path-only
python lucid_cli.py diagnose captive --i-consent --json
python lucid_cli.py diagnose dns --domain example.com --i-consent --json
python lucid_cli.py diagnose tls --host example.com --i-consent --json
python lucid_cli.py overlay-status --json
python lucid_cli.py multiwan-status --json
python lucid_cli.py anomalies --json
python lucid_cli.py traffic-history --limit 24 --json
python lucid_cli.py pcap-plan --duration 30 --interface "Wi-Fi" --json
python lucid_cli.py frontier catalog --json
python lucid_cli.py frontier status --json
python lucid_cli.py frontier gate --capability wfp_enforcement --operation prototype --i-consent --lab-mode --review legal --review ethical --review safety --review feasibility --review driver_signing --review rollback --review performance --json
```

The current CLI is support-focused and now covers the same high-value operator actions exposed through the GUI: product identity, product vision, brand architecture, status, context-aware profile preview, DNS profile listing and application, DNS reset, proxy status and mutation, PAC/SOCKS5 proxy modes, forced legacy and dual-stack DDNS sync, hosts preview/apply, diagnostics export, consent-gated active diagnostics, overlay status, multi-adapter recommendations, anomaly review, traffic history, and PCAP capture planning.

Privileged actions currently use the same core functions as the GUI. Once the elevated broker exists, DNS apply/reset, proxy mutation, hosts edits, firewall operations, and other privileged changes must route through the broker instead of direct GUI or CLI calls.

CLI rules:

- Stable exit code `0` on success.
- Nonzero exit on error.
- Optional JSON output for scripts.
- No GUI initialization for CLI-only commands.
- Active diagnostics require explicit `--i-consent`.
- Frontier commands are read-only or plan-only until reviewed implementation exists.
- Operational bypass, traffic camouflage, identity rotation, and evasion operations are blocked by the frontier policy gate even when warnings are present.
- Mutation commands should preserve the same validation, redaction, and rollback behavior as the GUI.
- CLI and GUI capabilities should remain on-par unless a feature is inherently visual.

Unimplemented research and frontier work is tracked in `docs/RESEARCH_AND_FRONTIER_BACKLOG.md`. The CLI `frontier` commands expose the same capability catalog and gate decisions used by diagnostics and the GUI Tools action.

## Power Efficiency

`power_policy.py` defines a power-aware policy layer:

- Query best-effort Windows battery status.
- Increase polling interval while on battery, battery saver, or minimized.
- Suspend expensive analytics while reduced mode is active.
- Pause UI refresh loops while minimized where safe.
- Pause automatic DDNS while battery saver asks for reduced background work.
- Surface reduced-mode state in the monitor snapshot for GUI display.

Power policy complements metered-connection awareness. It does not disable core safety checks or user-triggered actions.

The Settings tab exposes switches for reducing background work on metered networks, reducing background work on battery, and rolling back risky DNS/proxy changes when connectivity fails. The Tools tab exposes quick checks for captive portal state, overlay clients, and power policy so the GUI can show the same operational context available through the CLI.
