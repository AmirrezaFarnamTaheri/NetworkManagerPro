import core
from monitor_service import MonitorService


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise core.requests.RequestException(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, response=None, error=None):
        self.response = response or FakeResponse()
        self.error = error
        self.calls = []

    def get(self, url, timeout):
        self.calls.append((url, timeout))
        if self.error:
            raise self.error
        return self.response


class FakeKeyring:
    def __init__(self):
        self.values = {}

    def set_password(self, service, username, password):
        self.values[(service, username)] = password

    def get_password(self, service, username):
        return self.values.get((service, username))

    def delete_password(self, service, username):
        self.values.pop((service, username), None)


def test_ddns_secret_storage_uses_keyring_and_config_fallback(monkeypatch):
    fake_keyring = FakeKeyring()
    monkeypatch.setattr(core, "keyring", fake_keyring)

    ok, saved = core.store_ddns_update_url("https://provider.test/update?token=x")

    assert ok is True
    assert saved == "https://provider.test/update?token=x"
    assert core.get_ddns_update_url({"ddns_update_url": ""}) == "https://provider.test/update?token=x"

    core.clear_ddns_update_url()
    assert core.get_ddns_update_url({"ddns_update_url": "https://fallback.test/update?token=y"}) == (
        "https://fallback.test/update?token=y"
    )


def test_ddns_secret_storage_reports_missing_keyring(monkeypatch):
    monkeypatch.setattr(core, "keyring", None)

    ok, msg = core.store_ddns_update_url("https://provider.test/update?token=x")

    assert ok is False
    assert "keyring" in msg.lower()


def test_update_ddns_success_and_status_failure(monkeypatch):
    success = FakeSession(FakeResponse(204))
    monkeypatch.setattr(core, "_http_session", success)

    assert core.update_ddns("https://provider.test/update?token=x") == (True, "DDNS updated successfully.")
    assert success.calls == [("https://provider.test/update?token=x", 10)]

    failure = FakeSession(FakeResponse(500))
    monkeypatch.setattr(core, "_http_session", failure)

    assert core.update_ddns("https://provider.test/update?token=x") == (False, "Server returned status 500")


def test_update_ddns_rejects_invalid_url_before_http(monkeypatch):
    session = FakeSession()
    monkeypatch.setattr(core, "_http_session", session)

    ok, msg = core.update_ddns("file:///tmp/nope")

    assert ok is False
    assert "http:// or https://" in msg
    assert session.calls == []


def test_get_public_ip_caches_success_and_backs_off_failure(monkeypatch):
    session = FakeSession(FakeResponse(200, {"ip": "203.0.113.10"}))
    monkeypatch.setattr(core, "_http_session", session)
    core._public_ip_cache.update({"value": None, "timestamp": 0.0, "failures": 0, "next_retry": 0.0})

    assert core.get_public_ip() == "203.0.113.10"
    assert core.get_public_ip() == "203.0.113.10"
    assert len(session.calls) == 1

    error_session = FakeSession(error=core.requests.RequestException("offline"))
    monkeypatch.setattr(core, "_http_session", error_session)
    core._public_ip_cache.update({"value": None, "timestamp": 0.0, "failures": 0, "next_retry": 0.0})

    assert core.get_public_ip() is None
    assert core._public_ip_cache["failures"] == 1
    assert core._public_ip_cache["next_retry"] > 0


def test_monitor_auto_ddns_success_failure_and_retry(monkeypatch):
    calls = []

    def fake_update(url):
        calls.append(url)
        return False, "temporary failure"

    monkeypatch.setattr(core, "update_ddns", fake_update)
    monitor = MonitorService(
        {"ddns_update_url": "https://provider.test/update?token=x", "settings": {"auto_update_ddns": True}},
        "missing-config.json",
    )

    assert monitor._maybe_update_ddns(monitor.config, "203.0.113.10") == "temporary failure"
    assert monitor._last_ddns_success_ip is None
    assert len(calls) == 1
    assert monitor._next_ddns_retry > 0

    assert monitor._maybe_update_ddns(monitor.config, "203.0.113.10") is None
    assert len(calls) == 1

    def fake_success(url):
        calls.append(url)
        return True, "ok"

    monkeypatch.setattr(core, "update_ddns", fake_success)
    monitor._next_ddns_retry = 0.0

    assert monitor._maybe_update_ddns(monitor.config, "203.0.113.10") == "ok"
    assert monitor._last_ddns_success_ip == "203.0.113.10"
