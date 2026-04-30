import core


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
