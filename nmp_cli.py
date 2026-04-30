from __future__ import annotations

import argparse
import json
import sys

import core
import diagnostics


def build_parser():
    parser = argparse.ArgumentParser(prog="nmp", description="Network Manager Pro command-line companion")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    sub.add_parser("list-dns")
    export = sub.add_parser("export-diagnostics")
    export.add_argument("--path-only", action="store_true")
    return parser


def run(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "status":
            payload = {
                "app": core.APP_DISPLAY_NAME,
                "version": core.APP_VERSION,
                "admin": core.is_admin(),
                "config_path": core.config_path(),
                "app_data": core.app_data_dir(),
            }
            return _emit(payload, args.json)
        if args.command == "list-dns":
            cfg = core.normalize_config(core.load_config() or core.default_config())
            payload = {"dns_profiles": cfg.get("dns_profiles", {})}
            return _emit(payload, args.json)
        if args.command == "export-diagnostics":
            path = diagnostics.export_bundle(core.load_config() or core.default_config(), None)
            if args.path_only and not args.json:
                print(path)
                return 0
            return _emit({"path": path}, args.json)
    except Exception as exc:
        payload = {"ok": False, "error": str(exc)}
        if args.json:
            print(json.dumps(payload, sort_keys=True))
        else:
            print(f"Error: {exc}", file=sys.stderr)
        return 1
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


if __name__ == "__main__":
    raise SystemExit(run())
