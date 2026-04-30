from __future__ import annotations

import argparse
import json
import sys

import anomaly_detection
import core
import deep_diagnostics
import diagnostics
import forensics_plan
import overlay_networks


def build_parser():
    parser = argparse.ArgumentParser(prog="nmp", description="Network Manager Pro command-line companion")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    sub.add_parser("list-dns")
    dns_cmd = sub.add_parser("dns")
    dns_sub = dns_cmd.add_subparsers(dest="dns_command", required=True)
    dns_sub.add_parser("list")
    dns_apply = dns_sub.add_parser("apply")
    dns_apply.add_argument("--profile")
    dns_apply.add_argument("--servers", nargs="+")
    dns_apply.add_argument("--interface")
    dns_clear = dns_sub.add_parser("clear")
    dns_clear.add_argument("--interface")
    proxy_cmd = sub.add_parser("proxy")
    proxy_sub = proxy_cmd.add_subparsers(dest="proxy_command", required=True)
    proxy_sub.add_parser("status")
    proxy_enable = proxy_sub.add_parser("enable")
    proxy_enable.add_argument("--server", required=True)
    proxy_sub.add_parser("disable")
    ddns_cmd = sub.add_parser("ddns")
    ddns_sub = ddns_cmd.add_subparsers(dest="ddns_command", required=True)
    ddns_sub.add_parser("force")
    export = sub.add_parser("export-diagnostics")
    export.add_argument("--path-only", action="store_true")
    diag = sub.add_parser("diagnose")
    diag_sub = diag.add_subparsers(dest="diagnostic", required=True)
    captive = diag_sub.add_parser("captive")
    captive.add_argument("--i-consent", action="store_true", help="Confirm consent for this active diagnostic.")
    dns = diag_sub.add_parser("dns")
    dns.add_argument("--domain", required=True)
    dns.add_argument("--i-consent", action="store_true", help="Confirm consent for this external active diagnostic.")
    tls = diag_sub.add_parser("tls")
    tls.add_argument("--host", required=True)
    tls.add_argument("--expect-issuer", action="append", default=[])
    tls.add_argument("--i-consent", action="store_true", help="Confirm consent for this external active diagnostic.")
    sub.add_parser("overlay-status")
    sub.add_parser("multiwan-status")
    sub.add_parser("anomalies")
    pcap = sub.add_parser("pcap-plan")
    pcap.add_argument("--duration", type=int, default=30)
    pcap.add_argument("--interface", default="")
    return parser


def run(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "status":
            proxy_enabled, proxy_server = core.get_proxy_state()
            payload = {
                "app": core.APP_DISPLAY_NAME,
                "version": core.APP_VERSION,
                "admin": core.is_admin(),
                "config_path": core.config_path(),
                "app_data": core.app_data_dir(),
                "active_interface": core.get_active_interface_alias(),
                "dns_servers": core.get_dns_servers(),
                "proxy_enabled": proxy_enabled,
                "proxy_server": core.sanitize_proxy_server(proxy_server),
            }
            return _emit(payload, args.json)
        if args.command in ("list-dns",) or (args.command == "dns" and args.dns_command == "list"):
            cfg = core.normalize_config(core.load_config() or core.default_config())
            payload = {"dns_profiles": cfg.get("dns_profiles", {})}
            return _emit(payload, args.json)
        if args.command == "dns" and args.dns_command == "apply":
            cfg = core.normalize_config(core.load_config() or core.default_config())
            if args.profile:
                profiles = cfg.get("dns_profiles") or {}
                if args.profile not in profiles:
                    return _error(f"Unknown DNS profile: {args.profile}", args.json, code=2)
                servers = profiles[args.profile]
            else:
                servers = args.servers or []
            ok, msg = core.set_dns(list(servers), args.interface)
            return _emit({"success": ok, "message": msg}, args.json) if ok else _error(msg, args.json, code=1)
        if args.command == "dns" and args.dns_command == "clear":
            ok, msg = core.clear_dns(args.interface)
            return _emit({"success": ok, "message": msg}, args.json) if ok else _error(msg, args.json, code=1)
        if args.command == "proxy" and args.proxy_command == "status":
            enabled, server = core.get_proxy_state()
            return _emit({"proxy_enabled": enabled, "proxy_server": core.sanitize_proxy_server(server)}, args.json)
        if args.command == "proxy" and args.proxy_command == "enable":
            ok, msg = core.set_proxy(True, args.server)
            return _emit({"success": ok, "message": msg}, args.json) if ok else _error(msg, args.json, code=1)
        if args.command == "proxy" and args.proxy_command == "disable":
            ok, msg = core.set_proxy(False)
            return _emit({"success": ok, "message": msg}, args.json) if ok else _error(msg, args.json, code=1)
        if args.command == "ddns" and args.ddns_command == "force":
            cfg = core.normalize_config(core.load_config() or core.default_config())
            url = core.get_ddns_update_url(cfg)
            ok, msg = core.update_ddns(url)
            return _emit({"success": ok, "message": msg}, args.json) if ok else _error(msg, args.json, code=1)
        if args.command == "export-diagnostics":
            path = diagnostics.export_bundle(core.load_config() or core.default_config(), None)
            if args.path_only and not args.json:
                print(path)
                return 0
            return _emit({"path": path}, args.json)
        if args.command == "diagnose":
            if not getattr(args, "i_consent", False):
                return _error(
                    "This diagnostic requires explicit consent. Re-run with --i-consent after reviewing the test scope.",
                    args.json,
                    code=2,
                )
            if args.diagnostic == "captive":
                return _emit(deep_diagnostics.run_captive_portal_diagnostic(), args.json)
            if args.diagnostic == "dns":
                return _emit(deep_diagnostics.run_dns_integrity_diagnostic(args.domain), args.json)
            if args.diagnostic == "tls":
                return _emit(deep_diagnostics.run_tls_inspection_diagnostic(args.host, args.expect_issuer), args.json)
        if args.command == "overlay-status":
            tools = overlay_networks.detect_overlay_tools()
            statuses = {}
            for tool, meta in tools.items():
                statuses[tool] = overlay_networks.run_read_only_status(tool) if meta["installed"] else {"ok": False, "tool": tool, "output": "", "error": "Not installed."}
            return _emit({"tools": tools, "statuses": statuses}, args.json)
        if args.command == "multiwan-status":
            adapters = forensics_plan.adapter_inventory()
            return _emit({"adapters": adapters, "recommendation": forensics_plan.adapter_failover_recommendation(adapters)}, args.json)
        if args.command == "anomalies":
            return _emit({"findings": anomaly_detection.findings_from_metrics_db()}, args.json)
        if args.command == "pcap-plan":
            return _emit(forensics_plan.pcap_capture_plan(args.duration, interface=args.interface), args.json)
    except Exception as exc:
        return _error(str(exc), args.json, code=1)
    parser.error("Unknown command")
    return 2


def _emit(payload, as_json):
    payload = {"ok": True, **payload}
    if as_json:
        print(json.dumps(payload, sort_keys=True, default=str))
    else:
        for key, value in payload.items():
            print(f"{key}: {value}")
    return 0


def _error(message, as_json, code=1):
    payload = {"ok": False, "error": str(message)}
    if as_json:
        print(json.dumps(payload, sort_keys=True))
    else:
        print(f"Error: {message}", file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(run())
