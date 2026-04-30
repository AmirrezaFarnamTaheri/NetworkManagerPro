import core
import monitor_service


class FakeResponse:
    def __init__(self, status_code=200, text="", headers=None):
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}


def test_network_profile_matching_requires_known_context():
    cfg = core.normalize_config(
        {
            "network_profiles": [
                {
                    "name": "Office",
                    "ssid": "CorpWifi",
                    "bssid": "AA-BB-CC-DD-EE-FF",
                    "dns_profile": "Cloudflare",
                    "proxy_profile": "127.0.0.1:8080",
                    "auto_apply": "false",
                }
            ]
        }
    )

    match = core.match_network_profile(cfg, {"ssid": "corpwifi", "bssid": "aa:bb:cc:dd:ee:ff"})
    assert match["name"] == "Office"
    assert match["bssid"] == "aa:bb:cc:dd:ee:ff"

    preview = core.network_profile_preview(cfg, {"ssid": "CorpWifi", "bssid": "aa:bb:cc:dd:ee:ff"})
    assert preview["matched"] is True
    assert preview["auto_apply"] is False
    assert {"type": "dns", "profile": "Cloudflare"} in preview["actions"]
    assert core.match_network_profile(cfg, {"ssid": "GuestWifi"}) is None


def test_network_profile_apply_plan_and_wifi_context_parser():
    cfg = core.normalize_config(
        {
            "dns_profiles": {"OfficeDNS": ["1.1.1.1"]},
            "network_profiles": [
                {
                    "name": "Office",
                    "ssid": "CorpWifi",
                    "dns_profile": "OfficeDNS",
                    "proxy_profile": "127.0.0.1:8080",
                    "auto_apply": True,
                }
            ],
        }
    )

    plan = core.network_profile_apply_plan(cfg, {"ssid": "CorpWifi"})
    assert plan["matched"] is True
    assert plan["auto_apply"] is True
    assert {"type": "dns", "profile": "OfficeDNS", "servers": ["1.1.1.1"], "requires_admin": True} in plan["steps"]
    assert {"type": "proxy", "profile": "127.0.0.1:8080", "requires_admin": False} in plan["steps"]

    netsh = """
    SSID                   : CorpWifi
    BSSID                  : aa-bb-cc-dd-ee-ff
    """
    assert core.get_current_wifi_ssid(query=lambda: netsh) == "CorpWifi"
    assert core.get_current_wifi_bssid(query=lambda: netsh) == "aa:bb:cc:dd:ee:ff"


def test_auto_apply_network_profile_applies_and_rolls_back_on_connectivity_failure():
    cfg = core.normalize_config(
        {
            "settings": {"rollback_on_connectivity_loss": True},
            "dns_profiles": {"OfficeDNS": ["1.1.1.1"]},
            "network_profiles": [
                {"name": "Office", "ssid": "CorpWifi", "dns_profile": "OfficeDNS", "proxy_profile": "127.0.0.1:8080", "auto_apply": True}
            ],
        }
    )
    calls = []
    executor = {
        "set_dns": lambda servers, interface=None: calls.append(("set_dns", servers, interface)) or (True, "dns ok"),
        "clear_dns": lambda interface=None: calls.append(("clear_dns", interface)) or (True, "dns cleared"),
        "set_proxy": lambda enabled, server="": calls.append(("set_proxy", enabled, server)) or (True, "proxy ok"),
        "restore_proxy_settings": lambda snapshot: calls.append(("restore_proxy", snapshot)) or (True, "proxy restored"),
        "get_dns_restore_state": lambda interface=None: {"interface": interface, "dns_servers_v4": ["8.8.8.8"], "dns_servers_v6": []},
        "get_proxy_settings": lambda: {"proxy_enabled": False, "proxy_server": None},
    }

    result = core.apply_network_profile_plan(
        cfg,
        {"ssid": "CorpWifi", "interface": "Wi-Fi"},
        captive_status="open",
        executor=executor,
        connectivity_checker=lambda: (False, "offline"),
    )

    assert result["rolled_back"] is True
    assert result["reason"] == "rolled_back"
    assert ("set_dns", ["1.1.1.1"], "Wi-Fi") in calls
    assert ("set_dns", ["8.8.8.8"], "Wi-Fi") in calls
    assert any(call[0] == "restore_proxy" for call in calls)


def test_auto_apply_network_profile_respects_consent_and_captive_portal():
    cfg = core.normalize_config(
        {
            "dns_profiles": {"OfficeDNS": ["1.1.1.1"]},
            "network_profiles": [{"name": "Office", "ssid": "CorpWifi", "dns_profile": "OfficeDNS", "auto_apply": False}],
        }
    )

    disabled = core.apply_network_profile_plan(cfg, {"ssid": "CorpWifi"}, connectivity_checker=lambda: (True, "ok"))
    assert disabled["reason"] == "auto_apply_disabled"

    cfg["network_profiles"][0]["auto_apply"] = True
    captive = core.apply_network_profile_plan(cfg, {"ssid": "CorpWifi"}, captive_status="captive", connectivity_checker=lambda: (True, "ok"))
    assert captive["reason"] == "captive_portal"


def test_monitor_pauses_profile_auto_apply_on_captive_portal(monkeypatch, tmp_path):
    events = []

    class Store:
        def append(self, event_type, summary, details=None, attribution="LucidNet"):
            events.append((event_type, summary, details or {}))

    cfg = core.normalize_config(
        {
            "dns_profiles": {"OfficeDNS": ["1.1.1.1"]},
            "network_profiles": [{"name": "Office", "ssid": "CorpWifi", "dns_profile": "OfficeDNS", "auto_apply": True}],
        }
    )
    service = monitor_service.MonitorService(cfg, str(tmp_path / "config.json"), event_store=Store())
    state = monitor_service.NetworkState(interface="Wi-Fi", gateway="192.0.2.1", captive_portal_status="captive")
    monkeypatch.setattr(core, "get_current_wifi_ssid", lambda: "CorpWifi")
    monkeypatch.setattr(core, "get_current_wifi_bssid", lambda: "")

    assert service._maybe_apply_network_profile(cfg, state) is None
    assert events
    assert events[0][0] == "network_profile.auto_apply_paused"


def test_captive_portal_detection_classifies_open_redirect_and_modified_content():
    open_result = core.detect_captive_portal(
        fetcher=lambda *args, **kwargs: FakeResponse(200, "Microsoft Connect Test")
    )
    redirect_result = core.detect_captive_portal(
        fetcher=lambda *args, **kwargs: FakeResponse(302, "", {"Location": "http://login.test/"})
    )
    modified_result = core.detect_captive_portal(
        fetcher=lambda *args, **kwargs: FakeResponse(200, "<html>login</html>")
    )

    assert open_result["status"] == "open"
    assert redirect_result["status"] == "captive"
    assert modified_result["status"] == "captive"


def test_metered_background_policy_reduces_polling_when_enabled():
    cfg = core.normalize_config({"settings": {"check_interval_seconds": 30, "pause_background_on_metered": True}})
    policy = core.background_work_policy(cfg, {"metered": True})

    assert policy["reduced_mode"] is True
    assert policy["pause_ddns"] is True
    assert policy["poll_interval_seconds"] == 300

    normal = core.background_work_policy(cfg, {"metered": False})
    assert normal["reduced_mode"] is False
    assert normal["poll_interval_seconds"] == 30


def test_deadman_rollback_decision_respects_config_and_connectivity():
    cfg = core.normalize_config({"settings": {"rollback_on_connectivity_loss": True}})
    assert core.should_rollback_after_change(cfg, True, False) is True
    assert core.should_rollback_after_change(cfg, True, True) is False
    assert core.should_rollback_after_change(cfg, False, False) is False

    disabled = core.normalize_config({"settings": {"rollback_on_connectivity_loss": False}})
    assert core.should_rollback_after_change(disabled, True, False) is False
