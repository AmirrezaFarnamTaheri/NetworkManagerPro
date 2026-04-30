import pytest

from plugin_api import PluginAPI


def test_plugin_api_missing_permissions_raise_clear_errors():
    api = PluginAPI("demo", {}, monitor=None, event_store=None)

    with pytest.raises(PermissionError, match="network_state"):
        api.network_state()
    with pytest.raises(PermissionError, match="events"):
        api.emit_event("test", "summary")
    with pytest.raises(PermissionError, match="ui"):
        api.register_tab("Demo", lambda _parent, _api: None)
    with pytest.raises(PermissionError, match="scheduled_tasks"):
        api.register_periodic_task("demo", 5, lambda _api: None)


def test_plugin_api_allows_granted_permissions_without_event_store():
    api = PluginAPI("demo", {}, monitor=None, event_store=None, permissions=["network_state", "events"])

    assert api.network_state() is None
    assert api.emit_event("test", "summary") is None
