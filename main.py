import sys
import threading
import time
if sys.platform == 'win32':
    import ctypes
from PIL import Image, ImageDraw
import pystray
from plyer import notification
import core
import gui

# --- Auto-Admin Privilege Request ---
if sys.platform == 'win32' and not core.is_admin():
    # If not admin, prompt UAC screen and relaunch script as Admin automatically
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

# Load Configuration
config = core.load_config()
if not config:
    print("Error: config.json not found in directory.")
    sys.exit(1)

app = None
tray_icon = None
last_ip = None

# --- System Tray Setup ---
def create_icon_image():
    """Generates a simple geometric icon for the Windows tray."""
    image = Image.new('RGB', (64, 64), color=(40, 40, 40))
    dc = ImageDraw.Draw(image)
    dc.ellipse((16, 16, 48, 48), fill=(46, 164, 114)) # Green circle
    return image

def show_window(icon, item):
    """Restores the UI from the tray."""
    if app:
        app.deiconify()

def exit_action(icon, item):
    """Closes the entire application completely."""
    icon.stop()
    if app:
        app.quit()
    sys.exit()

def on_gui_close():
    """Triggered when the user hits the 'X' button on the GUI."""
    notification.notify(
        title="Network Manager",
        message="Running in background. Check System Tray.",
        app_name="Network Manager Pro",
        timeout=3
    )

# --- Background DDNS Monitor ---
def ddns_monitor_loop():
    """Runs continuously in the background, checking IP and updating Shecan."""
    global last_ip
    url = config.get("shecan_update_url")
    interval = config.get("settings", {}).get("check_interval_seconds", 60)
    auto_update = config.get("settings", {}).get("auto_update_ddns", True)

    while True:
        current_ip = core.get_public_ip()
        
        # If IP changed and we have auto_update enabled
        if current_ip and last_ip and current_ip != last_ip and auto_update:
            success, msg = core.update_ddns(url)
            if success:
                notification.notify(
                    title="DDNS Auto-Updated",
                    message=f"IP shift detected ({current_ip}). DDNS synced.",
                    app_name="Network Manager Pro",
                    timeout=5
                )
        last_ip = current_ip
        time.sleep(interval)

# --- Main Execution ---
def main():
    global app, tray_icon

    # 1. Start the Background DDNS loop
    threading.Thread(target=ddns_monitor_loop, daemon=True).start()

    # 2. Setup the System Tray Icon
    menu = pystray.Menu(
        pystray.MenuItem('Open Manager', show_window, default=True),
        pystray.MenuItem('Exit', exit_action)
    )
    tray_icon = pystray.Icon("netmgr", create_icon_image(), "Network Manager Pro", menu)
    
    # 3. Start Tray loop in background
    threading.Thread(target=tray_icon.run, daemon=True).start()

    # 4. Start the Main CustomTkinter GUI
    app = gui.NetworkManagerGUI(config, on_close_callback=on_gui_close)
    app.mainloop()

if __name__ == "__main__":
    main()