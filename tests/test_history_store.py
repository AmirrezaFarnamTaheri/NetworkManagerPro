import sqlite3

from history_store import EventStore


def test_event_store_persists_recent_events_and_filters_by_type(tmp_path):
    path = tmp_path / "events.sqlite3"
    store = EventStore(str(path))

    first = store.append("dns.apply", "Applied DNS", {"token": "secret", "label": "safe"})
    second = store.append("proxy.toggle", "Proxy enabled", {"ok": True})

    assert path.exists()
    assert store.recent(0) == []
    assert [event["id"] for event in store.recent(2)] == [first["id"], second["id"]]
    assert [event["type"] for event in store.recent(10, event_type="proxy.toggle")] == ["proxy.toggle"]
    assert store.recent(10)[0]["details"]["token"] == "***"


def test_event_store_clear_deletes_existing_rows_and_records_clear_event(tmp_path):
    store = EventStore(str(tmp_path / "events.sqlite3"))
    store.append("demo", "Before clear")

    clear_event = store.clear()
    events = store.recent(10)

    assert clear_event["type"] == "history.cleared"
    assert [event["type"] for event in events] == ["history.cleared"]


def test_event_store_uses_wal_and_exports_redacted_jsonl(tmp_path):
    path = tmp_path / "events.sqlite3"
    store = EventStore(str(path))
    store.append("demo", "Export me", {"api_key": "secret", "label": "safe"})

    with sqlite3.connect(path) as conn:
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]

    exported = store.export_jsonl()

    assert mode.lower() == "wal"
    assert "secret" not in exported
    assert "safe" in exported
