import json

import core


def test_normalize_config_drops_unknown_keys_and_clamps_interval():
    cfg = core.normalize_config(
        {
            "settings": {"auto_update_ddns": "false", "check_interval_seconds": "1"},
            "dns_profiles": {"Invalid": ["not-ip"], "Valid": ["1.1.1.1", ""]},
            "proxy_profiles": ["bad host:8080", "127.0.0.1:8080"],
            "plugins": {"enabled": ["demo_plugin"], "settings": {"demo_plugin": {"enabled": True}}},
            "unexpected": "drop me",
        }
    )

    assert cfg["config_version"] == 1
    assert cfg["settings"]["auto_update_ddns"] is False
    assert cfg["settings"]["check_interval_seconds"] == 15
    assert cfg["dns_profiles"] == {"Valid": ["1.1.1.1"]}
    assert cfg["proxy_profiles"] == ["127.0.0.1:8080"]
    assert cfg["plugins"]["enabled"] == ["demo_plugin"]
    assert "unexpected" not in cfg


def test_validate_network_inputs_cover_dns_proxy_and_ddns_url():
    assert core.validate_dns_servers(["1.1.1.1", "2606:4700:4700::1111"])[0] is True
    assert core.validate_dns_servers(["not-an-ip"])[0] is False
    assert core.validate_dns_servers([])[0] is False

    assert core.validate_proxy_server("127.0.0.1:8080") == (True, "127.0.0.1:8080")
    assert core.validate_proxy_server("LOCALHOST:08080") == (True, "localhost:8080")
    assert core.validate_proxy_server("http://127.0.0.1:8080")[0] is False
    assert core.validate_proxy_server("127.0.0.1:0")[0] is False
    assert core.validate_proxy_server("127.0.0.1:65536")[0] is False
    assert core.validate_proxy_server("bad host:8080")[0] is False
    assert core.validate_proxy_server("username:password@host:8080")[0] is False
    assert core.validate_proxy_server("2001:db8::1:8080")[0] is False
    assert core.validate_proxy_server("[2001:db8::1]:8080") == (True, "[2001:db8::1]:8080")
    assert core.validate_proxy_server("[127.0.0.1]:8080")[0] is False

    assert core.validate_http_url("https://provider.test/update?token=x", required=True)[0] is True
    assert core.validate_http_url("", required=False) == (True, "")
    assert core.validate_http_url("", required=True)[0] is False
    assert core.validate_http_url("https://provider.test:abc/update", required=True)[0] is False
    assert core.validate_http_url("file:///tmp/nope", required=True)[0] is False
    assert core.validate_http_url("https://example.com/your-ddns-update?token=YOUR_TOKEN", required=True)[0] is False


def test_save_and_load_config_roundtrip_uses_temp_path(tmp_path):
    path = tmp_path / "config.json"

    core.save_config({"settings": {"check_interval_seconds": 999999}}, str(path))
    loaded = core.load_config(str(path))

    assert loaded["settings"]["check_interval_seconds"] == 86400
    assert json.loads(path.read_text(encoding="utf-8"))["config_version"] == 1
