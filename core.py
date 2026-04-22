import subprocess
import winreg
import requests
import ctypes
import sys
import psutil
import socket
import json
import os
from ping3 import ping

def is_admin():
    """Check if the script is running with administrative privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def load_config(config_path="config.json"):
    """Loads settings from the JSON configuration file."""
    if not os.path.exists(config_path):
        return None
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_active_interface_alias():
    """
    Finds the active network interface name (e.g., 'Wi-Fi' or 'Ethernet')
    that has the active internet connection, avoiding VM/VPN adapters.
    """
    try:
        # Create a dummy socket to find the active local IP routing to the internet
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        active_ip = s.getsockname()[0]
        s.close()

        # Match the active IP to the Windows interface name
        for interface_name, snics in psutil.net_if_addrs().items():
            for snic in snics:
                if snic.family == socket.AF_INET and snic.address == active_ip:
                    return interface_name
    except Exception:
        pass
    return None

def run_powershell(script):
    """Executes a PowerShell script silently."""
    try:
        subprocess.run(["powershell", "-Command", script], check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        return True, "Success"
    except subprocess.CalledProcessError as e:
        return False, str(e)

def set_dns(dns_list):
    """Sets the DNS for the smart-detected active interface."""
    interface = get_active_interface_alias()
    if not interface:
        return False, "Could not detect active internet interface."
    
    # Format the IPs for PowerShell: ("IP1","IP2")
    dns_str = ",".join([f'"{ip}"' for ip in dns_list])
    cmd = f'Set-DnsClientServerAddress -InterfaceAlias "{interface}" -ServerAddresses ({dns_str})'
    return run_powershell(cmd)

def clear_dns():
    """Sets the DNS to automatic for the active interface."""
    interface = get_active_interface_alias()
    if not interface:
        return False, "Could not detect active internet interface."
    
    cmd = f'Set-DnsClientServerAddress -InterfaceAlias "{interface}" -ResetServerAddresses'
    return run_powershell(cmd)

def set_proxy(enable, proxy_server=""):
    """Enables or disables the Windows system-wide proxy via Registry."""
    try:
        internet_settings = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                           r'Software\Microsoft\Windows\CurrentVersion\Internet Settings', 
                                           0, winreg.KEY_ALL_ACCESS)
        
        # 1 means enable, 0 means disable
        winreg.SetValueEx(internet_settings, 'ProxyEnable', 0, winreg.REG_DWORD, 1 if enable else 0)
        
        if enable:
            winreg.SetValueEx(internet_settings, 'ProxyServer', 0, winreg.REG_SZ, proxy_server)
            
        winreg.CloseKey(internet_settings)
        
        # Force Windows to refresh settings so it applies instantly
        internet_option_settings_changed = 39
        internet_option_refresh = 37
        internet_set_option = ctypes.windll.wininet.InternetSetOptionW
        internet_set_option(0, internet_option_settings_changed, 0, 0)
        internet_set_option(0, internet_option_refresh, 0, 0)
        
        return True, "Proxy updated successfully."
    except Exception as e:
        return False, f"Registry error: {e}"

def get_public_ip():
    """Fetches the current public IP."""
    try:
        response = requests.get("https://api.ipify.org?format=json", timeout=5)
        return response.json().get("ip")
    except:
        return None

def update_ddns(url):
    """Hits the Shecan DDNS update URL."""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return True, "DDNS Updated Successfully."
        return False, f"Server returned status {response.status_code}"
    except Exception as e:
        return False, f"Connection error: {e}"

def measure_latency(ip):
    """Measures ping latency to an IP in milliseconds."""
    try:
        delay = ping(ip, timeout=2)
        if delay is None or delay is False:
            return "Timeout"
        return f"{int(delay * 1000)} ms"
    except:
        return "Error"