from __future__ import annotations

import argparse
import json
import os
import sys

import anomaly_detection
import branding
import core
import deep_diagnostics
import diagnostics
import forensics_plan
import hosts_manager
import overlay_networks
import plugin_host
import plugin_platform
import traffic_collector


def build_parser():
    parser = argparse.ArgumentParser(prog="nmp", description=f"{core.APP_DISPLAY_NAME} command-line companion")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("about")
    sub.add_parser("vision")
    sub.add_parser("brand")
    sub.add_parser("status")
    profiles = sub.add_parser("profiles")
    profiles_sub = profiles.add_subparsers(dest="profiles_command", required=True)
    profile_preview = profiles_sub.add_parser("preview")
    profile_preview.add_argument("--ssid", default="")
    profile_preview.add_argument("--bssid", default="")
    profile_preview.add_argument("--interface", default="")
    profile_preview.add_argument("--gateway", default="")
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
    proxy_pac = proxy_sub.add_parser("pac")
    proxy_pac.add_argument("--url", required=True)
    proxy_socks = proxy_sub.add_parser("socks5")
    proxy_socks.add_argument("--server", required=True)
    proxy_sub.add_parser("disable")
    ddns_cmd = sub.add_parser("ddns")
    ddns_sub = ddns_cmd.add_subparsers(dest="ddns_command", required=True)
    ddns_force = ddns_sub.add_parser("force")
    ddns_force.add_argument("--dual-stack", action="store_true")
    hosts_cmd = sub.add_parser("hosts")
    hosts_sub = hosts_cmd.add_subparsers(dest="hosts_command", required=True)
    hosts_preview = hosts_sub.add_parser("preview")
    hosts_preview.add_argument("--file", required=True)
    hosts_preview.add_argument("--group", required=True)
    hosts_preview.add_argument("--entry", action="append", default=[], help="Entry as IP,hostname[,comment].")
    hosts_preview.add_argument("--disable", action="store_true")
    hosts_apply = hosts_sub.add_parser("apply")
    hosts_apply.add_argument("--file", required=True)
    hosts_apply.add_argument("--group", required=True)
    hosts_apply.add_argument("--entry", action="append", default=[], help="Entry as IP,hostname[,comment].")
    hosts_apply.add_argument("--disable", action="store_true")
    hosts_apply.add_argument("--backup-dir", default="")
    plugins_cmd = sub.add_parser("plugins")
    plugins_sub = plugins_cmd.add_subparsers(dest="plugins_command", required=True)
    plugins_sub.add_parser("list")
    plugin_env = plugins_sub.add_parser("env-lock")
    plugin_env.add_argument("--manifest", required=True)
    plugin_bundle = plugins_sub.add_parser("verify-bundle")
    plugin_bundle.add_argument("--dir", required=True)
    plugin_bundle.add_argument("--manifest", required=True)
    plugin_marketplace = plugins_sub.add_parser("marketplace-plan")
    plugin_marketplace.add_argument("--registry", required=True)
    plugins_sub.add_parser("host-health")
    export = sub.add_parser("export-diagnostics")
    export.add_argument("--path-only", action="store_true")
    diag = sub.add_parser("diagnose")
    diag_sub = diag.add_subparsers(dest="diagnostic", required=True)
    captive = diag_sub.add_parser("captive")
    captive.add_argument("--i-consent", action="store_true", help="Confirm consent for this active diagnostic.")
    dns = diag_sub.add_parser("dns")
    dns.add_argument("--domain", required=True)
    dns.add_argument("--i-consent", action="store_true", help="Confirm consent for this external active diagnostic.")
    transparent_dns = diag_sub.add_parser("transparent-dns")
    transparent_dns.add_argument("--domain", required=True)
    transparent_dns.add_argument("--resolver-label", default="selected resolver")
    transparent_dns.add_argument("--i-consent", action="store_true", help="Confirm consent for this external active diagnostic.")
    tls = diag_sub.add_parser("tls")
    tls.add_argument("--host", required=True)
    tls.add_argument("--expect-issuer", action="append", default=[])
    tls.add_argument("--i-consent", action="store_true", help="Confirm consent for this external active diagnostic.")
    sni = diag_sub.add_parser("sni")
    sni.add_argument("--host", required=True)
    sni.add_argument("--i-consent", action="store_true", help="Confirm consent for this external active diagnostic.")
    sub.add_parser("overlay-status")
    sub.add_parser("multiwan-status")
    sub.add_parser("anomalies")
    traffic = sub.add_parser("traffic-history")
    traffic.add_argument("--limit", type=int, default=24)
    pcap = sub.add_parser("pcap-plan")
    pcap.add_argument("--duration", type=int, default=30)
    pcap.add_argument("--interface", default="")
    pcap.add_argument("--request", action="store_true")
    sub.add_parser("sidecar-decision")
    return parser


def run(argv=None):
    parser = build_parser()
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--json" in argv:
        argv = [arg for arg in argv if arg != "--json"]
        argv.insert(0, "--json")
    args = parser.parse_args(argv)
    try:
        if args.command == "about":
            return _emit(branding.about_payload(), args.json)
        if args.command == "vision":
            return _emit({"vision": branding.product_vision(), "pillars": branding.product_pillars()}, args.json)
        if args.command == "brand":
            return _emit(
                {
                    "identity": branding.product_identity(),
                    "brand_architecture": branding.brand_architecture(),
                    "panel_branding": branding.panel_branding(),
                    "safety_boundary": branding.SAFETY_BOUNDARY,
                },
                args.json,
            )
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
        if args.command == "profiles" and args.profiles_command == "preview":
            cfg = core.normalize_config(core.load_config() or core.default_config())
            context = {
                "ssid": args.ssid,
                "bssid": args.bssid,
                "interface": args.interface,
                "gateway": args.gateway,
            }
            return _emit(core.network_profile_apply_plan(cfg, context), args.json)
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
        if args.command == "proxy" and args.proxy_command == "pac":
            ok, msg = core.set_pac_proxy(args.url)
            return _emit({"success": ok, "message": msg}, args.json) if ok else _error(msg, args.json, code=1)
        if args.command == "proxy" and args.proxy_command == "socks5":
            ok, msg = core.set_socks5_proxy(args.server)
            return _emit({"success": ok, "message": msg}, args.json) if ok else _error(msg, args.json, code=1)
        if args.command == "proxy" and args.proxy_command == "disable":
            ok, msg = core.set_proxy(False)
            return _emit({"success": ok, "message": msg}, args.json) if ok else _error(msg, args.json, code=1)
        if args.command == "ddns" and args.ddns_command == "force":
            cfg = core.normalize_config(core.load_config() or core.default_config())
            if args.dual_stack:
                result = core.update_ddns_dual_stack(cfg)
                return _emit(result, args.json) if result.get("ok") else _error(result.get("message"), args.json, code=1)
            url = core.get_ddns_update_url(cfg)
            ok, msg = core.update_ddns(url)
            return _emit({"success": ok, "message": msg}, args.json) if ok else _error(msg, args.json, code=1)
        if args.command == "hosts":
            entries = _parse_hosts_entries(args.entry)
            if args.hosts_command == "preview":
                with open(args.file, "r", encoding="utf-8", errors="replace") as f:
                    current = f.read()
                preview = hosts_manager.preview_apply(current, args.group, entries, enabled=not args.disable)
                return _emit({"preview": preview}, args.json)
            if args.hosts_command == "apply":
                backup = hosts_manager.apply_group(
                    args.file,
                    args.group,
                    entries,
                    enabled=not args.disable,
                    backup_dir=args.backup_dir or None,
                )
                return _emit({"success": True, "backup": backup}, args.json)
        if args.command == "plugins":
            if args.plugins_command == "list":
                return _emit({"plugins": _discover_plugins()}, args.json)
            if args.plugins_command == "env-lock":
                with open(args.manifest, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
                return _emit(plugin_platform.write_environment_lock(manifest), args.json)
            if args.plugins_command == "verify-bundle":
                with open(args.manifest, "r", encoding="utf-8") as f:
                    bundle = json.load(f)
                ok, failures = plugin_platform.verify_bundle_manifest(args.dir, bundle)
                payload = {"success": ok, "failures": failures}
                return _emit(payload, args.json) if ok else _error(json.dumps(payload), args.json, code=1)
            if args.plugins_command == "marketplace-plan":
                with open(args.registry, "r", encoding="utf-8") as f:
                    registry = json.load(f)
                installed = {item["id"]: item["version"] for item in _discover_plugins() if item.get("id")}
                return _emit(plugin_platform.marketplace_install_plan(registry, installed), args.json)
            if args.plugins_command == "host-health":
                return _emit(plugin_host.handle_request({"command": "health"}), args.json)
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
            if args.diagnostic == "transparent-dns":
                return _emit(
                    deep_diagnostics.run_transparent_dns_proxy_diagnostic(
                        args.domain,
                        requested_resolver_label=args.resolver_label,
                    ),
                    args.json,
                )
            if args.diagnostic == "tls":
                return _emit(deep_diagnostics.run_tls_inspection_diagnostic(args.host, args.expect_issuer), args.json)
            if args.diagnostic == "sni":
                return _emit(deep_diagnostics.run_sni_filtering_diagnostic(args.host), args.json)
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
        if args.command == "traffic-history":
            return _emit(traffic_collector.history_summary(core.traffic_metrics_db_path(), limit=args.limit), args.json)
        if args.command == "pcap-plan":
            payload = (
                forensics_plan.pcap_export_request(args.duration, interface=args.interface)
                if args.request
                else forensics_plan.pcap_capture_plan(args.duration, interface=args.interface)
            )
            return _emit(payload, args.json)
        if args.command == "sidecar-decision":
            return _emit(forensics_plan.sidecar_language_decision(), args.json)
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


def _parse_hosts_entries(values):
    entries = []
    for value in values or []:
        parts = [part.strip() for part in str(value).split(",", 2)]
        if len(parts) < 2:
            raise ValueError("Hosts entries must use IP,hostname[,comment].")
        comment = parts[2] if len(parts) > 2 else ""
        entries.append(hosts_manager.HostsEntry(parts[0], parts[1], comment))
    return entries


def _discover_plugins():
    rows = []
    for root in (core.plugins_dir(), core.bundled_plugins_dir()):
        if not os.path.isdir(root):
            continue
        for name in sorted(os.listdir(root)):
            path = os.path.join(root, name, "plugin.json")
            if not os.path.isfile(path):
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
                rows.append(
                    {
                        "id": str(manifest.get("id") or ""),
                        "name": str(manifest.get("name") or ""),
                        "version": str(manifest.get("version") or ""),
                        "path": path,
                        "isolation": plugin_platform.isolation_plan(manifest),
                    }
                )
            except Exception as exc:
                rows.append({"id": name, "path": path, "error": str(exc)})
    return rows


if __name__ == "__main__":
    raise SystemExit(run())
