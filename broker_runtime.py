from __future__ import annotations

import json
import os

import branding
import broker_contract
import core
import hosts_manager


PIPE_NAME = branding.BROKER_PIPE_NAME


def named_pipe_policy(current_user_sid="CURRENT_USER"):
    return {
        "schema_version": broker_contract.SCHEMA_VERSION,
        "pipe_name": PIPE_NAME,
        "acl": {
            "owner": "Administrators",
            "allow": ["SYSTEM", "Administrators", str(current_user_sid or "CURRENT_USER")],
            "deny_network_logon": True,
        },
        "message_framing": "newline-delimited-json",
        "timeouts_seconds": {"connect": 5, "request": 30},
    }


class BrokerDispatcher:
    def __init__(self, dns_setter=None, dns_clearer=None, hosts_applier=None, status_provider=None):
        self.dns_setter = dns_setter or core.set_dns
        self.dns_clearer = dns_clearer or core.clear_dns
        self.hosts_applier = hosts_applier or hosts_manager.apply_group
        self.status_provider = status_provider or _default_status

    def dispatch(self, request):
        ok, message = broker_contract.validate_request(request)
        if not ok:
            return broker_contract.make_response(request if isinstance(request, dict) else {}, False, message)
        command = request["command"]
        args = request.get("args") or {}
        try:
            if command == "status":
                return broker_contract.make_response(
                    request,
                    True,
                    "Broker status ready.",
                    detail=json.dumps(self.status_provider(), sort_keys=True, default=str),
                    event={"type": "broker.status"},
                )
            if command == "dns.set":
                success, detail = self.dns_setter(args["servers"], args["interface"])
                return broker_contract.make_response(request, success, "DNS set completed." if success else "DNS set failed.", detail)
            if command == "dns.clear":
                success, detail = self.dns_clearer(args["interface"])
                return broker_contract.make_response(request, success, "DNS clear completed." if success else "DNS clear failed.", detail)
            if command == "hosts.apply_group":
                entries = [hosts_manager.HostsEntry(**item) for item in args.get("entries", [])]
                hosts_path = args.get("path") or _hosts_path()
                backup = self.hosts_applier(hosts_path, args["group"], entries, enabled=bool(args["enabled"]))
                return broker_contract.make_response(request, True, "Hosts group applied.", backup)
        except Exception as exc:
            return broker_contract.make_response(request, False, f"Broker command failed: {exc}")
        return broker_contract.make_response(request, False, "Unsupported broker command.")


def route_privileged_command(command, args=None, dispatcher=None):
    dispatcher = dispatcher or BrokerDispatcher()
    request = broker_contract.make_request(command, args or {})
    return dispatcher.dispatch(request)


def _default_status():
    return {
        "app": core.APP_DISPLAY_NAME,
        "admin": core.is_admin(),
        "pipe": named_pipe_policy(),
        "commands": broker_contract.COMMANDS,
    }


def _hosts_path():
    return os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "drivers", "etc", "hosts")
