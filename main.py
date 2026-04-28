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
            "Network Manager Pro",
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
        _show_startup_error("Network Manager Pro", f"Could not create user config.\n\nPath: {path}\n\n{exc}")
        return None


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
            "Network Manager Pro needs administrator rights to change DNS settings. "
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
    image = Image.new("RGBA", (64, 64), color=(30, 32, 38, 255))
    dc = ImageDraw.Draw(image)
    dc.rounded_rectangle((8, 8, 56, 56), radius=12, fill=(46, 164, 114, 255))
    dc.rectangle((22, 24, 42, 28), fill=(255, 255, 255, 255))
    dc.rectangle((22, 32, 42, 36), fill=(255, 255, 255, 200))
    dc.rectangle((22, 40, 34, 44), fill=(255, 255, 255, 180))
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


def _acquire_single_instance():
    global single_instance_mutex
    try:
        kernel32 = ctypes.windll.kernel32
        single_instance_mutex = kernel32.CreateMutexW(None, False, f"Local\\{core.APP_NAME}")
        if not single_instance_mutex:
            return True
        if kernel32.GetLastError() == 183:
            _show_startup_error(core.APP_DISPLAY_NAME, "Network Manager Pro is already running.")
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
            title="Network Manager Pro",
            message="Still running in the background. Use the tray icon to reopen or exit.",
            app_name="Network Manager Pro",
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

    event_store = EventStore()
    event_store.append("app.start", "Application started", {"version": core.APP_VERSION, "admin": core.is_admin()})

    monitor = MonitorService(config, _config_path(), event_store=event_store)
    monitor.start()

    menu = pystray.Menu(
        pystray.MenuItem("Open Manager", show_window, default=True),
        pystray.MenuItem("Exit", exit_action),
    )
    tray_icon = pystray.Icon("netmgr", create_icon_image(), "Network Manager Pro", menu)
    threading.Thread(target=tray_icon.run, daemon=True).start()

    app = gui.NetworkManagerGUI(
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
