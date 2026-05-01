import ctypes
import os
import shutil
import subprocess
import sys
import threading
import tkinter as tk
import tkinter.messagebox as messagebox
from datetime import datetime

from PIL import Image, ImageDraw
import pystray
from plyer import notification

import core
import enterprise_policy
import gui
from history_store import EventStore
from monitor_service import MonitorService
from plugin_manager import PluginManager


app = None
tray_icon = None
monitor = None
plugin_manager = None
event_store = None
single_instance_mutex = None


def _show_startup_error(title, message):
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(title, message)
        root.destroy()
    except Exception:
        core.logger().error("%s: %s", title, message)


def _config_path():
    return core.config_path()


def _ensure_config():
    """Load user config or create it from built-in defaults."""
    path = _config_path()
    if os.path.exists(path):
        cfg = core.load_config(path)
        if cfg:
            return cfg
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = f"{path}.{stamp}.invalid"
        try:
            shutil.copyfile(path, backup)
        except OSError:
            backup = None
        _show_startup_error(
            core.APP_DISPLAY_NAME,
            "config.json could not be read. A fresh default config will be created"
            + (f" and the unreadable file was backed up to:\n{backup}" if backup else ".")
            + "\n\nCheck JSON commas, quotes, and brackets before restoring custom values.",
        )
    cfg = core.default_config()
    try:
        core.save_config(cfg, path)
        core.logger().info("config_created path=%s", path)
        return cfg
    except OSError as exc:
        core.logger().error("config_create_failed path=%s error=%s", path, exc, exc_info=True)
        _show_startup_error(core.APP_DISPLAY_NAME, f"Could not create user config.\n\nPath: {path}\n\n{exc}")
        return None


def _apply_machine_policy(config):
    policies = enterprise_policy.read_hklm_policies()
    cfg, managed = enterprise_policy.apply_policy_overrides(config, policies)
    if managed:
        core.log_event("info", "policy.applied", managed=managed)
    return cfg, managed


def _elevation_command_line():
    """Parameters for elevated relaunch (avoid duplicating argv[0] for frozen exe)."""
    if getattr(sys, "frozen", False):
        return subprocess.list2cmdline(sys.argv[1:]) if len(sys.argv) > 1 else ""
    return subprocess.list2cmdline(sys.argv)


def _request_admin_or_exit():
    if core.is_admin():
        return True
    params = _elevation_command_line()
    rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
    if rc <= 32:
        core.logger().error("admin_elevation_failed rc=%s", rc)
        _show_startup_error(
            "Administrator rights required",
            f"{core.APP_DISPLAY_NAME} needs administrator rights to change DNS settings. "
            "Right-click the app and choose Run as administrator.",
        )
    else:
        core.logger().info("admin_elevation_requested rc=%s", rc)
    return False


def create_icon_image():
    """Tray icon: bundled PNG if present, else generated mark."""
    for name in ("assets/tray_64.png", "assets/tray_48.png"):
        p = core.resource_path(*name.split("/"))
        if os.path.isfile(p):
            try:
                return Image.open(p).convert("RGBA")
            except OSError:
                core.logger().debug("tray_icon_load_failed path=%s", p, exc_info=True)
    image = Image.new("RGBA", (64, 64), color=(0, 0, 0, 0))
    dc = ImageDraw.Draw(image)
    dc.rounded_rectangle((4, 4, 60, 60), radius=14, fill=(15, 118, 110, 255))
    dc.rounded_rectangle((6, 32, 58, 60), radius=12, fill=(11, 18, 32, 150))
    dc.line((16, 42, 16, 22, 24, 22, 24, 36, 38, 36), fill=(248, 250, 252, 255), width=5)
    dc.line((27, 43, 27, 24, 43, 41, 43, 22), fill=(94, 234, 212, 255), width=5)
    for x, y in ((16, 22), (24, 36), (43, 22), (43, 41)):
        dc.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(224, 242, 254, 255))
    return image


def show_window(icon=None, item=None):
    def _show_window_on_ui_thread():
        if not app:
            return
        app.deiconify()
        app.lift()
        app.focus_force()

    if app:
        try:
            app.after(0, _show_window_on_ui_thread)
        except Exception:
            core.logger().debug("tray_show_window_dispatch_failed", exc_info=True)


def _dispatch_app_action(action):
    if not app:
        return
    try:
        app.after(0, action)
    except Exception:
        core.logger().debug("tray_action_dispatch_failed", exc_info=True)


def tray_force_ddns(icon=None, item=None):
    _dispatch_app_action(app.force_update_ddns)


def tray_disable_proxy(icon=None, item=None):
    _dispatch_app_action(app.disable_proxy)


def tray_export_diagnostics(icon=None, item=None):
    _dispatch_app_action(app.export_diagnostics)


def tray_apply_dns_profile(profile):
    def _apply():
        if not app:
            return
        app.deiconify()
        if hasattr(app, "dns_var"):
            app.dns_var.set(profile)
        app.apply_dns()

    return lambda icon=None, item=None: _dispatch_app_action(_apply)


def _tray_dns_menu(config):
    profiles = config.get("dns_profiles") if isinstance(config, dict) else {}
    names = list(profiles.keys()) if isinstance(profiles, dict) else []
    if not names:
        return pystray.Menu(pystray.MenuItem("No DNS profiles", None, enabled=False))
    return pystray.Menu(*(pystray.MenuItem(name, tray_apply_dns_profile(name)) for name in names[:10]))


def _acquire_single_instance():
    global single_instance_mutex
    try:
        kernel32 = ctypes.windll.kernel32
        single_instance_mutex = kernel32.CreateMutexW(None, False, f"Local\\{core.APP_NAME}")
        if not single_instance_mutex:
            return True
        if kernel32.GetLastError() == 183:
            _show_startup_error(core.APP_DISPLAY_NAME, f"{core.APP_DISPLAY_NAME} is already running.")
            return False
    except Exception:
        core.logger().warning("single_instance_check_failed", exc_info=True)
    return True


def _release_single_instance():
    global single_instance_mutex
    if single_instance_mutex:
        try:
            ctypes.windll.kernel32.CloseHandle(single_instance_mutex)
        except Exception:
            pass
        single_instance_mutex = None


def exit_action(icon=None, item=None):
    global plugin_manager, monitor
    if icon:
        icon.stop()
    if plugin_manager:
        plugin_manager.stop_all()
    if monitor:
        monitor.stop()

    def _finish_exit():
        if app:
            app._alive = False
            app.quit()

    if app:
        try:
            app.after(0, _finish_exit)
        except Exception:
            _finish_exit()
    else:
        sys.exit(0)


def on_gui_close():
    try:
        notification.notify(
            title=core.APP_DISPLAY_NAME,
            message="Still running in the background. Use the tray icon to reopen or exit.",
            app_name=core.APP_DISPLAY_NAME,
            timeout=3,
        )
    except Exception:
        core.logger().debug("tray_notification_failed", exc_info=True)


def main():
    global app, tray_icon, monitor, plugin_manager, event_store

    core.setup_logging()
    if not _acquire_single_instance():
        return
    if not _request_admin_or_exit():
        _release_single_instance()
        return

    config = _ensure_config()
    if not config:
        _release_single_instance()
        return
    config, managed_policy = _apply_machine_policy(config)

    mirror_event_log = core.parse_bool((config.get("settings") or {}).get("policy_enable_windows_event_log_export"), False)
    event_store = EventStore(mirror_event_log=mirror_event_log)
    event_store.append("app.start", "Application started", {"version": core.APP_VERSION, "admin": core.is_admin()})
    if managed_policy:
        event_store.append("policy.applied", "Machine policy applied", managed_policy)

    monitor = MonitorService(config, _config_path(), event_store=event_store)
    monitor.start()

    menu = pystray.Menu(
        pystray.MenuItem("Open Manager", show_window, default=True),
        pystray.MenuItem("Apply DNS Profile", _tray_dns_menu(config)),
        pystray.MenuItem("Disable Proxy", tray_disable_proxy),
        pystray.MenuItem("Force DDNS Sync", tray_force_ddns),
        pystray.MenuItem("Export Diagnostics", tray_export_diagnostics),
        pystray.MenuItem("Exit", exit_action),
    )
    tray_icon = pystray.Icon("LucidNet", create_icon_image(), core.APP_DISPLAY_NAME, menu)
    threading.Thread(target=tray_icon.run, daemon=True).start()

    app = gui.LucidNetGUI(
        config,
        on_close_callback=on_gui_close,
        config_path=_config_path(),
        monitor=monitor,
        event_store=event_store,
    )
    plugin_manager = PluginManager(config, monitor=monitor, event_store=event_store, ui_host=app)
    plugin_manager.load_enabled()

    try:
        app.mainloop()
    finally:
        if plugin_manager:
            plugin_manager.stop_all()
        if monitor:
            monitor.stop()
        if tray_icon:
            try:
                tray_icon.stop()
            except Exception:
                pass
        if event_store:
            event_store.append("app.stop", "Application stopped")
        _release_single_instance()


if __name__ == "__main__":
    main()
