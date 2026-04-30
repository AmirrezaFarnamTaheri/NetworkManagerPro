import os

import core
import hosts_manager
import traffic_collector


class FakeIPResponse:
    def __init__(self, ip):
        self._ip = ip

    def raise_for_status(self):
        return None

    def json(self):
        return {"ip": self._ip}


def test_pac_and_socks5_validation_normalize_inputs():
    assert core.validate_pac_url("https://proxy.test/wpad.pac") == (True, "https://proxy.test/wpad.pac")
    assert core.validate_pac_url("https://proxy.test/not-pac.txt")[0] is False

    assert core.validate_socks5_proxy("socks5://LOCALHOST:1080") == (True, "localhost:1080")
    assert core.validate_socks5_proxy("bad host:1080")[0] is False

    cfg = core.normalize_config(
        {
            "pac_profiles": ["https://proxy.test/wpad.pac", "https://proxy.test/no.txt"],
            "socks5_profiles": ["socks5://127.0.0.1:1080", "bad host:1"],
        }
    )
    assert cfg["pac_profiles"] == ["https://proxy.test/wpad.pac"]
    assert cfg["socks5_profiles"] == ["127.0.0.1:1080"]


def test_hosts_manager_previews_and_backs_up_before_apply(tmp_path):
    hosts_path = tmp_path / "hosts"
    hosts_path.write_text("127.0.0.1 localhost\n", encoding="utf-8")
    entries = [hosts_manager.HostsEntry("10.0.0.2", "dev.local", "dev override")]

    preview = hosts_manager.preview_apply(hosts_path.read_text(encoding="utf-8"), "dev", entries)
    assert "# LucidNet BEGIN dev" in preview
    assert "10.0.0.2 dev.local # dev override" in preview

    backup = hosts_manager.apply_group(str(hosts_path), "dev", entries, backup_dir=str(tmp_path / "backups"))
    assert os.path.exists(backup)
    updated = hosts_path.read_text(encoding="utf-8")
    assert "dev.local" in updated

    disabled = hosts_manager.preview_apply(updated, "dev", entries, enabled=False)
    assert "dev.local" not in disabled


def test_hosts_manager_validates_entries():
    ok, msg, clean = hosts_manager.validate_entries([hosts_manager.HostsEntry("10.0.0.2", "Dev.Local", "ok")])
    assert ok is True
    assert clean[0].hostname == "dev.local"

    ok, msg, clean = hosts_manager.validate_entries([hosts_manager.HostsEntry("not-ip", "dev.local")])
    assert ok is False
    assert "Invalid hosts IP" in msg
    assert clean == []


def test_public_ip_family_and_ddns_url_selection(monkeypatch):
    def fetcher(url, timeout=8):
        if "api64" in url:
            return FakeIPResponse("2001:db8::1")
        return FakeIPResponse("203.0.113.7")

    assert core.get_public_ip_family("ipv4", fetcher=fetcher) == "203.0.113.7"
    assert core.get_public_ip_family("ipv6", fetcher=fetcher) == "2001:db8::1"

    cfg = core.normalize_config(
        {
            "ddns_update_url_v4": "https://ddns.test/update-a",
            "ddns_update_url_v6": "https://ddns.test/update-aaaa",
        }
    )
    assert core.ddns_update_urls(cfg)["ipv4"] == "https://ddns.test/update-a"
    assert core.ddns_update_urls(cfg)["ipv6"] == "https://ddns.test/update-aaaa"


def test_traffic_metrics_sqlite_roundtrip(tmp_path):
    db_path = tmp_path / "traffic.sqlite3"
    traffic_collector.append_metrics(
        str(db_path),
        totals={"bytes_sent": 100, "bytes_recv": 200, "packets_sent": 3, "packets_recv": 4},
        timestamp=1,
    )
    traffic_collector.append_metrics(
        str(db_path),
        totals={"bytes_sent": 160, "bytes_recv": 260, "packets_sent": 5, "packets_recv": 6},
        timestamp=3,
    )

    rows = traffic_collector.recent_metrics(str(db_path), limit=10)
    summary = traffic_collector.summarize_metric_deltas(rows)
    assert len(rows) == 2
    assert summary["bytes_sent_delta"] == 60
    assert summary["bytes_recv_delta"] == 60
    assert summary["duration_seconds"] == 2


def test_traffic_metrics_summary_includes_latency(tmp_path):
    db_path = tmp_path / "traffic.sqlite3"
    traffic_collector.append_metrics(
        str(db_path),
        totals={"bytes_sent": 100, "bytes_recv": 200, "packets_sent": 3, "packets_recv": 4},
        latency_ms=20,
        timestamp=1,
    )
    traffic_collector.append_metrics(
        str(db_path),
        totals={"bytes_sent": 200, "bytes_recv": 300, "packets_sent": 4, "packets_recv": 5},
        latency_ms=40,
        timestamp=3,
    )

    payload = traffic_collector.history_summary(str(db_path), limit=10)

    assert payload["summary"]["latency_min_ms"] == 20
    assert payload["summary"]["latency_avg_ms"] == 30
    assert payload["summary"]["latency_max_ms"] == 40
