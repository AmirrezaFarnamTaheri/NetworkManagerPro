import json
import zipfile

import core
import diagnostics
from history_store import EventStore


def test_sanitize_url_and_proxy_redact_credentials_and_tokens():
    assert (
        core.sanitize_url("https://user:password@example.test/update/path?token=abc&host=demo", redact_path=True)
        == "https://***@example.test/***/***?token=***&host=***"
    )
    assert (
        core.sanitize_url("https://example.test/update?token=abc&host=demo", redact_path=False)
        == "https://example.test/update?token=***&host=demo"
    )
    assert core.sanitize_proxy_server("http=username:password@proxy.test:8080") == "http=***@proxy.test:8080"


def test_redact_value_recurses_through_sensitive_keys_and_urls():
    payload = {
        "api_key": "secret-value",
        "nested": {"password": "pw", "safe": "keep"},
        "items": [{"auth_token": "abc"}, "https://example.test/path?token=abc&safe=yes"],
        "proxy": "user:pass@proxy.test:8080",
    }

    redacted = core.redact_value(payload)

    assert redacted["api_key"] == "***"
    assert redacted["nested"]["password"] == "***"
    assert redacted["nested"]["safe"] == "keep"
    assert redacted["items"][0]["auth_token"] == "***"
    assert "abc" not in str(redacted)
    assert redacted["proxy"] == "***@proxy.test:8080"


def test_diagnostics_summary_and_bundle_redact_sensitive_content(monkeypatch, tmp_path):
    monkeypatch.setattr(core, "app_data_dir", lambda: str(tmp_path))
    monkeypatch.setattr(core, "logs_dir", lambda: str(tmp_path / "logs"))
    monkeypatch.setattr(core, "history_dir", lambda: str(tmp_path / "history"))
    monkeypatch.setattr(core, "plugins_dir", lambda: str(tmp_path / "plugins"))
    monkeypatch.setattr(core, "config_path", lambda: str(tmp_path / "config.json"))
    monkeypatch.setattr(core, "log_file_path", lambda: str(tmp_path / "logs" / "app.log"))
    monkeypatch.setattr(core, "history_db_path", lambda: str(tmp_path / "history" / "events.sqlite3"))

    (tmp_path / "logs").mkdir()
    (tmp_path / "history").mkdir()
    (tmp_path / "logs" / "app.log").write_text(
        "url=https://user:password@example.test/update/secret?token=abc\n",
        encoding="utf-8",
    )
    EventStore(str(tmp_path / "history" / "events.sqlite3")).append(
        "demo",
        "summary",
        {"api_key": "secret", "label": "safe"},
    )

    config = {
        "ddns_update_url": "https://user:password@example.test/update/secret?token=abc",
        "plugins": {"settings": {"demo": {"password": "pw", "label": "safe"}}},
    }
    summary_text = json.dumps(diagnostics.diagnostics_summary(config), default=str)

    assert "abc" not in summary_text
    assert "secret" not in summary_text
    assert "pw" not in summary_text
    assert "safe" in summary_text

    bundle_path = diagnostics.export_bundle(config)
    with zipfile.ZipFile(bundle_path) as bundle:
        app_log = bundle.read("logs/app.log").decode("utf-8")
        history = bundle.read("history/events.jsonl").decode("utf-8")

    assert "abc" not in app_log
    assert "user:password" not in app_log
    assert "secret" not in history
    assert "safe" in history
