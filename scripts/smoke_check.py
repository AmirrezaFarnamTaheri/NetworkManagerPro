import os
import re
import sys
import tempfile
import types
import tomllib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def _install_import_stubs():
    """Let smoke checks run in bare environments without runtime deps installed."""
    if "psutil" not in sys.modules:
        psutil = types.ModuleType("psutil")
        psutil.net_if_addrs = lambda: {}
        sys.modules["psutil"] = psutil

    if "ping3" not in sys.modules:
        ping3 = types.ModuleType("ping3")
        ping3.ping = lambda *_args, **_kwargs: None
        sys.modules["ping3"] = ping3

    if "requests" not in sys.modules:
        requests = types.ModuleType("requests")

        class RequestException(Exception):
            pass

        class Session:
            def get(self, *_args, **_kwargs):
                raise RequestException("requests is not installed in this smoke-check environment")

        requests.RequestException = RequestException
        requests.Session = Session
        sys.modules["requests"] = requests


_install_import_stubs()

import core
import diagnostics
from history_store import EventStore
from monitor_service import MonitorService
from plugin_api import PluginAPI


def check_config_normalization():
    cfg = core.normalize_config(
        {
            "settings": {"auto_update_ddns": "false", "check_interval_seconds": "1"},
            "dns_profiles": {"Empty": [], "Invalid": ["not-ip"], "Valid": ["1.1.1.1", ""]},
            "proxy_profiles": ["", "bad host:8080", "username:password@host:8080", "127.0.0.1:8080"],
            "plugins": {"enabled": ["example_plugin"]},
            "unknown_top_level": "drop me",
        }
    )
    assert cfg["config_version"] == 1
    assert cfg["settings"]["auto_update_ddns"] is False
    assert cfg["settings"]["check_interval_seconds"] == 15
    assert cfg["dns_profiles"] == {"Valid": ["1.1.1.1"]}
    assert cfg["proxy_profiles"] == ["127.0.0.1:8080"]
    assert cfg["plugins"]["enabled"] == ["example_plugin"]
    assert "unknown_top_level" not in cfg


def check_sanitization():
    summary = diagnostics.diagnostics_summary(
        {
            "ddns_update_url": "https://user:password@example.test/update/TOKEN-SECRET-HERE?token=abc&host=demo",
            "proxy_profiles": ["username:password@host:8080"],
            "plugins": {"settings": {"demo": {"api_key": "secret", "label": "safe", "nested": {"password": "pw"}}}},
        }
    )
    text = str(summary)
    assert "abc" not in text
    assert "user:password" not in text
    assert "TOKEN-SECRET-HERE" not in text
    assert "secret" not in text
    assert "pw" not in text
    assert "***" in text


def check_config_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "config.json")
        core.save_config({"settings": {"check_interval_seconds": 999999}}, path)
        cfg = core.load_config(path)
        assert cfg["settings"]["check_interval_seconds"] == 86400


def check_input_validation():
    assert core.validate_dns_servers(["1.1.1.1", "2606:4700:4700::1111"])[0] is True
    assert core.validate_dns_servers(["not-an-ip"])[0] is False
    assert core.validate_http_url("https://example.test/update?token=x", required=True)[0] is True
    assert core.validate_http_url("http://example.test:abc/path", required=True)[0] is False
    assert core.validate_http_url("https://example.com/your-ddns-update?token=YOUR_TOKEN", required=True)[0] is False
    assert core.validate_http_url("file:///tmp/nope", required=True)[0] is False
    assert core.validate_proxy_server("127.0.0.1:8080") == (True, "127.0.0.1:8080")
    assert core.validate_proxy_server("http://127.0.0.1:8080")[0] is False
    assert core.validate_proxy_server("bad host:8080")[0] is False
    assert core.validate_proxy_server("username:password@host:8080")[0] is False
    assert core.validate_proxy_server("http=host:8080;https=host:8081")[0] is False
    assert core.validate_proxy_server("2001:db8::1:8080")[0] is False
    assert core.validate_proxy_server("[2001:db8::1]:8080") == (True, "[2001:db8::1]:8080")


def check_plugin_config_resilience():
    cfg = {"plugins": "invalid"}
    api = PluginAPI("demo", cfg, monitor=None, event_store=None)
    settings = api.get_config({"enabled": True})
    assert settings == {"enabled": True}
    assert cfg["plugins"]["settings"]["demo"] == {"enabled": True}
    assert api.network_state() is None

    allowed = PluginAPI("demo", cfg, monitor=None, event_store=None, permissions=["network_state", "events"])
    assert allowed.emit_event("test", "summary") is None


def check_history_serialization():
    with tempfile.TemporaryDirectory() as tmp:
        store = EventStore(os.path.join(tmp, "events.sqlite3"))
        store.append("test.object", "Object detail", {"path": os.path.join(tmp, "x"), "type": object()})
        assert store.recent(0) == []
        events = store.recent(1)
        assert events[0]["type"] == "test.object"


def check_monitor_defaults():
    monitor = MonitorService({"settings": {"auto_update_ddns": "false"}}, "missing-config.json")
    assert monitor.config["settings"]["auto_update_ddns"] is False
    assert monitor.snapshot().ddns_last_result == "Not run"


def check_monitor_ddns_retry_state():
    calls = []
    original_update = core.update_ddns
    try:
        def fake_update(url):
            calls.append(url)
            return False, "temporary failure"

        core.update_ddns = fake_update
        monitor = MonitorService(
            {"ddns_update_url": "https://provider.test/update?token=x", "settings": {"auto_update_ddns": True}},
            "missing-config.json",
        )
        assert monitor._maybe_update_ddns(monitor.config, "203.0.113.10") == "temporary failure"
        assert monitor._last_ddns_success_ip is None
        assert len(calls) == 1
        monitor._next_ddns_retry = 0.0
        assert monitor._maybe_update_ddns(monitor.config, "203.0.113.10") == "temporary failure"
        assert len(calls) == 2
    finally:
        core.update_ddns = original_update


def check_release_metadata_consistency():
    with open(os.path.join(ROOT, "pyproject.toml"), "rb") as f:
        project_version = tomllib.load(f)["project"]["version"]
    with open(os.path.join(ROOT, "installer", "NetworkManagerPro.iss"), "r", encoding="utf-8") as f:
        installer_text = f.read()
    match = re.search(r'#define\s+MyAppVersion\s+"([^"]+)"', installer_text)
    assert match, "installer version define is missing"
    assert core.APP_VERSION == project_version == match.group(1)


def main():
    check_config_normalization()
    check_sanitization()
    check_config_roundtrip()
    check_input_validation()
    check_plugin_config_resilience()
    check_history_serialization()
    check_monitor_defaults()
    check_monitor_ddns_retry_state()
    check_release_metadata_consistency()
    print("Smoke checks passed.")


if __name__ == "__main__":
    main()
