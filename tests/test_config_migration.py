import json

import core


def test_load_config_backs_up_invalid_json_and_returns_none(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("{not-json", encoding="utf-8")

    assert core.load_config(str(path)) is None
    assert not path.exists()
    backups = list(tmp_path.glob("config.json.invalid.*.bak"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == "{not-json"


def test_load_config_backs_up_unsupported_future_config(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"config_version": core.CONFIG_VERSION + 1}), encoding="utf-8")

    assert core.load_config(str(path)) is None
    assert not path.exists()
    assert len(list(tmp_path.glob("config.json.unsupported.*.bak"))) == 1


def test_normalize_config_forces_current_schema_version():
    cfg = core.normalize_config({"config_version": 0})

    assert cfg["config_version"] == core.CONFIG_VERSION
