import logging

import core


def test_log_event_redacts_sensitive_fields_and_normalizes_event_name(caplog):
    caplog.set_level(logging.INFO, logger=core.APP_NAME)

    core.log_event(
        logging.INFO,
        "DDNS Sync!",
        url="https://user:password@example.test/update/path?token=abc",
        api_key="secret",
        status="ok",
    )

    text = caplog.text

    assert "DDNS_Sync" in text
    assert "status=\"ok\"" in text
    assert "abc" not in text
    assert "secret" not in text
    assert "user:password" not in text
    assert "***" in text
