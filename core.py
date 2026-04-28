import ctypes
import copy
import json
import logging
from logging.handlers import RotatingFileHandler
import os
import re
import socket
import subprocess
import sys
import threading
import time
from ipaddress import ip_address
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
import winreg

import psutil
import requests
from ping3 import ping

_config_file_lock = threading.RLock()
_http_lock = threading.RLock()
_http_session = requests.Session()
_public_ip_cache = {
    "value": None,
    "timestamp": 0.0,
    "failures": 0,
    "next_retry": 0.0,
}
_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_RUN_VALUE_NAME = "NetworkManagerPro"
APP_NAME = "NetworkManagerPro"
APP_DISPLAY_NAME = "Network Manager Pro"
APP_VERSION = "2.0.0"

DEFAULT_CONFIG = {
    "config_version": 1,
    "ddns_update_url": "",
    "settings": {
        "auto_update_ddns": False,
        "check_interval_seconds": 60,
        "minimize_to_tray_on_close": True,
    },
    "plugins": {
        "enabled": [],
        "settings": {},
    },
    "dns_profiles": {
        "Cloudflare": ["1.1.1.1", "1.0.0.1"],
        "Google": ["8.8.8.8", "8.8.4.4"],
    },
    "proxy_profiles": [
        "127.0.0.1:8080",
        "127.0.0.1:10809",
    ],
}

_SENSITIVE_KEY_TOKENS = ("token", "key", "secret", "pass", "auth", "credential")
_HOSTNAME_RE = re.compile(
    r"^(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)*"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$"
)


def logger():
    return logging.getLogger(APP_NAME)


def config_lock():
    """Shared lock for config file and in-memory config updates."""
    return _config_file_lock


def app_base_dir():
    """Directory containing the executable (frozen) or project files (dev)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def app_data_dir():
    """Writable per-user runtime directory."""
    local = os.environ.get("LOCALAPPDATA") or app_base_dir()
    return os.path.join(local, APP_NAME)


def logs_dir():
    return os.path.join(app_data_dir(), "logs")


def log_file_path():
    return os.path.join(logs_dir(), "app.log")


def history_dir():
    return os.path.join(app_data_dir(), "history")


def history_events_path():
    return os.path.join(history_dir(), "events.jsonl")


def plugins_dir():
    """Writable user-installable plugin directory."""
    return os.path.join(app_data_dir(), "plugins")


def bundled_plugins_dir():
    """Read-only bundled example plugins, if present."""
    return resource_path("plugins")


def config_path():
    return os.path.join(app_data_dir(), "config.json")


def ensure_runtime_dirs():
    for path in (app_data_dir(), logs_dir(), history_dir(), plugins_dir()):
        os.makedirs(path, exist_ok=True)


def setup_logging(level=logging.INFO):
    """Configure rotating file logging once and return the active log path."""
    ensure_runtime_dirs()
    root = logging.getLogger()
    root.setLevel(level)
    log_path = log_file_path()
    already_configured = any(getattr(h, "_network_manager_handler", False) for h in root.handlers)
    if not already_configured:
        handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=5, encoding="utf-8")
        handler._network_manager_handler = True
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
        root.addHandler(handler)
    logger().info(
        "startup app_version=%s frozen=%s app_base=%s config_path=%s log_path=%s history_path=%s plugins_dir=%s",
        APP_VERSION,
        bool(getattr(sys, "frozen", False)),
        app_base_dir(),
        config_path(),
        log_path,
        history_events_path(),
        plugins_dir(),
    )
    return log_path


def resource_path(*parts):
    """Bundled assets (PyInstaller _MEIPASS) or project-relative path."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, *parts)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), *parts)


def is_admin():
    """Check if the script is running with administrative privileges."""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def load_config(config_path=None):
    """Loads settings from JSON next to the app, or the given path (thread-safe)."""
    if config_path is None:
        config_path = globals()["config_path"]()
    with _config_file_lock:
        if not os.path.exists(config_path):
            return None
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return normalize_config(json.load(f))
        except (OSError, json.JSONDecodeError) as exc:
            logger().warning("config_load_failed path=%s error=%s", config_path, exc, exc_info=True)
            return None


def save_config(config, config_path=None):
    """Atomically write normalized user settings."""
    if config_path is None:
        config_path = globals()["config_path"]()
    config_path = os.path.abspath(config_path)
    parent = os.path.dirname(config_path) or "."
    os.makedirs(parent, exist_ok=True)
    tmp_path = config_path + ".tmp"
    config = normalize_config(config)
    with _config_file_lock:
        with open(tmp_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        last_error = None
        for attempt in range(5):
            try:
                os.replace(tmp_path, config_path)
                return
            except PermissionError as exc:
                last_error = exc
                time.sleep(0.1 * (attempt + 1))
        if last_error:
            raise last_error


def default_config():
    return copy.deepcopy(DEFAULT_CONFIG)


def normalize_config(config):
    """Merge user config with defaults and coerce risky values into safe shapes."""
    if not isinstance(config, dict):
        config = {}
    merged = default_config()
    for key in ("config_version", "ddns_update_url", "settings", "plugins", "dns_profiles", "proxy_profiles"):
        if key in config:
            merged[key] = config[key]

    settings = merged.get("settings")
    if not isinstance(settings, dict):
        settings = {}
    default_settings = default_config()["settings"]
    default_settings.update(settings)
    for bool_key in ("auto_update_ddns", "minimize_to_tray_on_close"):
        default_settings[bool_key] = parse_bool(default_settings.get(bool_key), DEFAULT_CONFIG["settings"][bool_key])
    try:
        default_settings["check_interval_seconds"] = max(
            15,
            min(86400, int(default_settings.get("check_interval_seconds", 60))),
        )
    except (TypeError, ValueError):
        default_settings["check_interval_seconds"] = 60
    merged["settings"] = default_settings

    plugins = merged.get("plugins")
    if not isinstance(plugins, dict):
        plugins = {}
    enabled = plugins.get("enabled")
    plugins["enabled"] = [str(item) for item in enabled] if isinstance(enabled, list) else []
    if not isinstance(plugins.get("settings"), dict):
        plugins["settings"] = {}
    merged["plugins"] = plugins

    profiles = merged.get("dns_profiles")
    clean_profiles = {}
    if isinstance(profiles, dict):
        for name, servers in profiles.items():
            if isinstance(servers, list):
                clean = [str(server).strip() for server in servers if str(server).strip()]
                valid, normalized_or_error = validate_dns_servers(clean)
                if valid:
                    clean_profiles[str(name)] = normalized_or_error
                else:
                    logger().warning("config_dns_profile_invalid name=%s error=%s", name, normalized_or_error)
    merged["dns_profiles"] = clean_profiles or default_config()["dns_profiles"]

    proxies = merged.get("proxy_profiles")
    clean_proxies = []
    if isinstance(proxies, list):
        for proxy in proxies:
            valid, normalized_or_error = validate_proxy_server(proxy)
            if valid:
                clean_proxies.append(normalized_or_error)
            elif str(proxy or "").strip():
                logger().warning("config_proxy_profile_invalid value=%r error=%s", proxy, normalized_or_error)
    merged["proxy_profiles"] = clean_proxies or default_config()["proxy_profiles"]

    if merged.get("ddns_update_url") is not None:
        merged["ddns_update_url"] = str(merged["ddns_update_url"]).strip()
    return merged


def parse_bool(value, default=False):
    """Parse config booleans without treating every non-empty string as True."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in ("1", "true", "yes", "on"):
            return True
        if normalized in ("0", "false", "no", "off"):
            return False
    return bool(default)


def validate_dns_servers(dns_list):
    """Return (ok, normalized_servers_or_error) for IPv4/IPv6 DNS server lists."""
    if not isinstance(dns_list, list) or not dns_list:
        return False, "DNS profile must contain at least one server."
    normalized = []
    for raw in dns_list:
        server = str(raw).strip()
        try:
            normalized.append(str(ip_address(server)))
        except ValueError:
            return False, f"Invalid DNS server address: {server}"
    return True, normalized


def validate_http_url(url, required=False):
    """Validate user-provided HTTP(S) URLs for DDNS endpoints."""
    url = str(url or "").strip()
    if not url:
        return (False, "URL is required.") if required else (True, "")
    if any(ord(ch) < 32 for ch in url):
        return False, "URL cannot contain control characters."
    parts = urlsplit(url)
    if parts.scheme.lower() not in ("http", "https") or not parts.netloc:
        return False, "URL must start with http:// or https:// and include a host."
    try:
        hostname = parts.hostname
        _ = parts.port
    except ValueError:
        return False, "URL contains an invalid port."
    if not hostname:
        return False, "URL must include a valid host."
    lowered = url.lower()
    if "example.com" in lowered or "your_token" in lowered:
        return False, "Replace the placeholder DDNS URL before saving."
    return True, url


def validate_proxy_server(proxy_server):
    """Validate simple host:port proxy profile values."""
    proxy_server = str(proxy_server or "").strip()
    if not proxy_server:
        return False, "Proxy server is required."
    if "://" in proxy_server:
        return False, "Use host:port without a URL scheme."
    if any(ch.isspace() for ch in proxy_server) or any(ch in proxy_server for ch in (";", "=", "@")):
        return False, "Proxy server must be a simple host:port value without credentials or per-protocol rules."

    if proxy_server.startswith("["):
        end = proxy_server.find("]")
        if end <= 1 or end + 1 >= len(proxy_server) or proxy_server[end + 1] != ":":
            return False, "IPv6 proxy addresses must use [address]:port."
        host = proxy_server[1:end]
        port = proxy_server[end + 2 :]
        try:
            parsed_ip = ip_address(host)
            if parsed_ip.version != 6:
                return False, "Bracketed proxy addresses must be IPv6."
        except ValueError:
            return False, "Invalid IPv6 proxy host."
        normalized_host = f"[{parsed_ip}]"
    else:
        if proxy_server.count(":") != 1:
            return False, "Proxy server must use host:port. Use [IPv6-address]:port for IPv6."
        host, port = proxy_server.rsplit(":", 1)
        host = host.strip()
        if not host:
            return False, "Proxy server must include a host."
        try:
            normalized_host = str(ip_address(host))
        except ValueError:
            if not _HOSTNAME_RE.match(host):
                return False, "Proxy host must be a valid hostname, IPv4 address, or bracketed IPv6 address."
            normalized_host = host.lower()
    if not port.isdigit():
        return False, "Proxy port must be numeric."
    port_number = int(port)
    if port_number < 1 or port_number > 65535:
        return False, "Proxy port must be between 1 and 65535."
    return True, f"{normalized_host}:{port_number}"


def sanitize_proxy_server(proxy_server):
    """Redact proxy credentials before logging or diagnostics."""
    value = str(proxy_server or "").strip()
    if not value:
        return ""
    redacted_parts = []
    for part in value.split(";"):
        prefix = ""
        body = part
        if "=" in part:
            prefix, body = part.split("=", 1)
            prefix += "="
        if "@" in body:
            body = "***@" + body.rsplit("@", 1)[1]
        redacted_parts.append(prefix + body)
    return ";".join(redacted_parts)


def sanitize_url(url, redact_path=False):
    """Redact sensitive query string values before logging or diagnostics."""
    if not url:
        return ""
    try:
        parts = urlsplit(str(url))
        netloc = parts.netloc
        if "@" in netloc:
            host_part = netloc.rsplit("@", 1)[1]
            netloc = f"***@{host_part}"
        path = parts.path
        if redact_path:
            path_parts = [part for part in path.split("/") if part]
            if path_parts:
                path = "/" + "/".join("***" for _part in path_parts)
        redacted = []
        for key, value in parse_qsl(parts.query, keep_blank_values=True):
            if redact_path or any(token in key.lower() for token in _SENSITIVE_KEY_TOKENS):
                redacted.append((key, "***"))
            else:
                redacted.append((key, value))
        query = urlencode(redacted, safe="*")
        return urlunsplit((parts.scheme, netloc, path, query, parts.fragment))
    except Exception:
        return "<redacted-url>"


def redact_value(value, key_hint=""):
    """Recursively redact secrets in dict/list payloads for logs and diagnostics."""
    key_hint = str(key_hint or "").lower()
    if any(token in key_hint for token in _SENSITIVE_KEY_TOKENS):
        if isinstance(value, str) and value.lower().startswith(("http://", "https://")):
            return sanitize_url(value, redact_path=True)
        return "***"
    if isinstance(value, dict):
        return {str(key): redact_value(item, key) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_value(item, key_hint) for item in value]
    if isinstance(value, tuple):
        return [redact_value(item, key_hint) for item in value]
    if isinstance(value, str):
        if value.lower().startswith(("http://", "https://")):
            return sanitize_url(value)
        if "@" in value and ":" in value:
            return sanitize_proxy_server(value)
    return value


def sanitize_config(cfg):
    """Return a copy of config safe for logs/diagnostics."""
    if not isinstance(cfg, dict):
        return {}
    sanitized = redact_value(json.loads(json.dumps(cfg, default=str)))
    if sanitized.get("ddns_update_url"):
        sanitized["ddns_update_url"] = sanitize_url(sanitized["ddns_update_url"], redact_path=True)
    return sanitized


def get_ddns_update_url(cfg):
    """DDNS update URL from config."""
    if not cfg or not isinstance(cfg, dict):
        return None
    url = cfg.get("ddns_update_url")
    if url is None:
        return None
    url = str(url).strip()
    return url or None


def run_at_startup_command():
    """Command line stored in HKCU Run for this process (frozen exe or python + script)."""
    if getattr(sys, "frozen", False):
        return f'"{os.path.abspath(sys.executable)}"'
    script = os.path.abspath(sys.argv[0])
    py = os.path.abspath(sys.executable)
    return f'"{py}" "{script}"'


def get_run_at_startup():
    """Whether this app is registered in HKCU ... CurrentVersion Run."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_READ)
        try:
            winreg.QueryValueEx(key, _RUN_VALUE_NAME)
            return True
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except OSError:
        return False


def set_run_at_startup(enabled):
    """Register or remove HKCU Run entry for logon startup."""
    try:
        key = winreg.CreateKeyEx(
            winreg.HKEY_CURRENT_USER,
            _RUN_KEY,
            0,
            winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE,
        )
        try:
            if enabled:
                winreg.SetValueEx(key, _RUN_VALUE_NAME, 0, winreg.REG_SZ, run_at_startup_command())
            else:
                try:
                    winreg.DeleteValue(key, _RUN_VALUE_NAME)
                except FileNotFoundError:
                    pass
        finally:
            winreg.CloseKey(key)
        return True, "Startup option updated."
    except OSError as e:
        return False, str(e)


def list_interface_aliases():
    """Windows interface names that have an IPv4 address (for manual DNS selection)."""
    names = []
    try:
        for interface_name, snics in psutil.net_if_addrs().items():
            for snic in snics:
                if snic.family == socket.AF_INET and snic.address and not snic.address.startswith("127."):
                    if interface_name not in names:
                        names.append(interface_name)
                    break
    except Exception:
        pass
    return sorted(names, key=str.lower)


def get_active_interface_alias():
    """
    Finds the active network interface name (e.g., 'Wi-Fi' or 'Ethernet')
    that has the active internet connection, avoiding VM/VPN adapters when possible.
    """
    ok, route_alias = run_powershell(
        "Get-NetRoute -DestinationPrefix '0.0.0.0/0' | "
        "Sort-Object RouteMetric,InterfaceMetric | "
        "Select-Object -First 1 -ExpandProperty InterfaceAlias"
    )
    if ok and route_alias and route_alias != "Success":
        return route_alias.strip().splitlines()[0]

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        active_ip = s.getsockname()[0]
        s.close()

        for interface_name, snics in psutil.net_if_addrs().items():
            for snic in snics:
                if snic.family == socket.AF_INET and snic.address == active_ip:
                    return interface_name
    except Exception:
        logger().debug("active_interface_fallback_failed", exc_info=True)
    return None


def _escape_ps_single_quoted(s):
    """Escape for PowerShell single-quoted string (double any single quote)."""
    return str(s).replace("'", "''")


def run_powershell(script):
    """Executes a PowerShell script silently."""
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=45,
        )
        return True, (r.stdout or "Success").strip() or "Success"
    except subprocess.CalledProcessError as e:
        err = (e.stderr or e.stdout or "").strip()
        return False, err or f"PowerShell exited with code {e.returncode}"
    except subprocess.TimeoutExpired:
        return False, "PowerShell command timed out."
    except OSError as e:
        return False, str(e)


def set_dns(dns_list, interface_alias=None):
    """Sets DNS for the given interface or the auto-detected active one."""
    valid, normalized_or_error = validate_dns_servers(dns_list)
    if not valid:
        return False, normalized_or_error
    dns_list = normalized_or_error
    interface = interface_alias or get_active_interface_alias()
    if not interface:
        return False, "Could not detect active internet interface."

    escaped = _escape_ps_single_quoted(interface)
    dns_str = ",".join([f'"{ip}"' for ip in dns_list])
    cmd = f"Set-DnsClientServerAddress -InterfaceAlias '{escaped}' -ServerAddresses ({dns_str})"
    ok, msg = run_powershell(cmd)
    logger().info("dns_set ok=%s interface=%s servers=%s", ok, interface, ",".join(map(str, dns_list)))
    if not ok:
        logger().warning("dns_set_failed interface=%s error=%s", interface, msg)
    return ok, msg


def clear_dns(interface_alias=None):
    """Sets DNS to automatic for the interface."""
    interface = interface_alias or get_active_interface_alias()
    if not interface:
        return False, "Could not detect active internet interface."

    escaped = _escape_ps_single_quoted(interface)
    cmd = f"Set-DnsClientServerAddress -InterfaceAlias '{escaped}' -ResetServerAddresses"
    ok, msg = run_powershell(cmd)
    logger().info("dns_clear ok=%s interface=%s", ok, interface)
    if not ok:
        logger().warning("dns_clear_failed interface=%s error=%s", interface, msg)
    return ok, msg


def get_dns_servers(interface_alias=None, address_family="IPv4"):
    """Return effective DNS servers for an interface and address family."""
    interface = interface_alias or get_active_interface_alias()
    if not interface:
        return []
    family = "IPv6" if str(address_family).upper() == "IPV6" else "IPv4"
    escaped = _escape_ps_single_quoted(interface)
    ok, out = run_powershell(
        f"(Get-DnsClientServerAddress -AddressFamily {family} -InterfaceAlias '{escaped}').ServerAddresses -join ','"
    )
    if not ok or not out or out == "Success":
        return []
    return [part.strip() for part in out.split(",") if part.strip()]


def get_dns_restore_state(interface_alias=None):
    """Capture DNS server state for both address families."""
    interface = interface_alias or get_active_interface_alias()
    if not interface:
        return {"interface": None, "dns_servers_v4": [], "dns_servers_v6": []}
    return {
        "interface": interface,
        "dns_servers_v4": get_dns_servers(interface, "IPv4"),
        "dns_servers_v6": get_dns_servers(interface, "IPv6"),
    }


def get_default_gateway(interface_alias=None):
    """Return the IPv4 default gateway for an interface."""
    interface = interface_alias or get_active_interface_alias()
    if not interface:
        return None
    escaped = _escape_ps_single_quoted(interface)
    ok, out = run_powershell(f"(Get-NetIPConfiguration -InterfaceAlias '{escaped}').IPv4DefaultGateway.NextHop")
    if ok and out and out != "Success":
        return out.strip().splitlines()[0]
    return None


def flush_dns_cache():
    """Clears the Windows DNS resolver cache (does not change adapter DNS)."""
    try:
        subprocess.run(
            ["ipconfig", "/flushdns"],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return True, "DNS resolver cache flushed."
    except subprocess.CalledProcessError as e:
        return False, e.stderr or str(e)
    except OSError as e:
        return False, str(e)


def renew_dhcp():
    """Renew DHCP leases on common adapters (best-effort)."""
    try:
        result = subprocess.run(
            ["ipconfig", "/renew"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=120,
        )
        output = (result.stderr or result.stdout or "").strip()
        if result.returncode != 0:
            return False, output or f"ipconfig /renew exited with code {result.returncode}."
        return True, output or "DHCP renew completed."
    except subprocess.TimeoutExpired:
        return False, "DHCP renew timed out."
    except OSError as e:
        return False, str(e)


def _internet_settings_key(access):
    return winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
        0,
        access,
    )


def _query_registry_value(key, name, default=None):
    try:
        value, value_type = winreg.QueryValueEx(key, name)
        return {"exists": True, "value": value, "type": value_type}
    except FileNotFoundError:
        return {"exists": False, "value": default, "type": None}


def _apply_registry_snapshot_value(key, name, item):
    if isinstance(item, dict) and item.get("exists"):
        winreg.SetValueEx(key, name, 0, item.get("type") or winreg.REG_SZ, item.get("value", ""))
        return
    try:
        winreg.DeleteValue(key, name)
    except FileNotFoundError:
        pass


def _notify_proxy_settings_changed():
    internet_option_settings_changed = 39
    internet_option_refresh = 37
    internet_set_option = ctypes.windll.wininet.InternetSetOptionW
    failures = []
    for option in (internet_option_settings_changed, internet_option_refresh):
        try:
            ctypes.set_last_error(0)
            if not internet_set_option(0, option, 0, 0):
                failures.append((option, ctypes.get_last_error()))
        except Exception as exc:
            failures.append((option, str(exc)))
    if failures:
        logger().warning("proxy_refresh_failed failures=%s", failures)
        return False, failures
    return True, []


def set_proxy(enable, proxy_server="", bypass_local=True):
    """Enables or disables the Windows system-wide proxy via Registry."""
    proxy_server = str(proxy_server or "").strip()
    if enable and not proxy_server:
        return False, "Choose a proxy server before enabling proxy."
    if enable:
        valid, normalized_or_error = validate_proxy_server(proxy_server)
        if not valid:
            return False, normalized_or_error
        proxy_server = normalized_or_error
    internet_settings = None
    try:
        internet_settings = _internet_settings_key(winreg.KEY_ALL_ACCESS)

        try:
            winreg.SetValueEx(internet_settings, "ProxyEnable", 0, winreg.REG_DWORD, 1 if enable else 0)

            if proxy_server:
                winreg.SetValueEx(internet_settings, "ProxyServer", 0, winreg.REG_SZ, proxy_server)
            if enable:
                override = _query_registry_value(internet_settings, "ProxyOverride")
                if bypass_local and not override["exists"]:
                    bypass = "<local>;*.local"
                    winreg.SetValueEx(internet_settings, "ProxyOverride", 0, winreg.REG_SZ, bypass)
        finally:
            if internet_settings:
                winreg.CloseKey(internet_settings)

        refresh_ok, failures = _notify_proxy_settings_changed()

        logger().info("proxy_set ok=%s enabled=%s server=%s", refresh_ok, bool(enable), sanitize_proxy_server(proxy_server if enable else ""))
        if not refresh_ok:
            return False, f"Proxy registry changed, but Windows refresh notification failed: {failures}"
        return True, "Proxy updated successfully."
    except OSError as e:
        logger().warning("proxy_set_failed enabled=%s error=%s", bool(enable), e)
        return False, f"Registry error: {e}"


def get_proxy_settings():
    """Return full WinINet proxy settings needed for a faithful restore point."""
    internet_settings = None
    try:
        internet_settings = _internet_settings_key(winreg.KEY_READ)
        enabled = _query_registry_value(internet_settings, "ProxyEnable", 0)
        server = _query_registry_value(internet_settings, "ProxyServer", "")
        override = _query_registry_value(internet_settings, "ProxyOverride", "")
        autoconfig = _query_registry_value(internet_settings, "AutoConfigURL", "")
        return {
            "proxy_enabled": bool(enabled.get("value", 0)),
            "proxy_server": server.get("value") or None,
            "registry": {
                "ProxyEnable": enabled,
                "ProxyServer": server,
                "ProxyOverride": override,
                "AutoConfigURL": autoconfig,
            },
        }
    except OSError:
        return {
            "proxy_enabled": False,
            "proxy_server": None,
            "registry": {},
        }
    finally:
        if internet_settings:
            winreg.CloseKey(internet_settings)


def restore_proxy_settings(snapshot):
    """Restore full WinINet proxy settings captured by get_proxy_settings()."""
    if not isinstance(snapshot, dict) or not isinstance(snapshot.get("registry"), dict):
        return set_proxy(bool((snapshot or {}).get("proxy_enabled")), (snapshot or {}).get("proxy_server") or "")
    internet_settings = None
    try:
        internet_settings = _internet_settings_key(winreg.KEY_ALL_ACCESS)
        registry = snapshot.get("registry") or {}
        for name in ("ProxyEnable", "ProxyServer", "ProxyOverride", "AutoConfigURL"):
            _apply_registry_snapshot_value(internet_settings, name, registry.get(name))
        refresh_ok, failures = _notify_proxy_settings_changed()
        if not refresh_ok:
            return False, f"Proxy registry restored, but Windows refresh notification failed: {failures}"
        return True, "Proxy settings restored."
    except OSError as e:
        return False, f"Registry error: {e}"
    finally:
        if internet_settings:
            winreg.CloseKey(internet_settings)


def get_proxy_state():
    """Returns (enabled: bool, server: str or None)."""
    settings = get_proxy_settings()
    return settings["proxy_enabled"], settings["proxy_server"]


def get_public_ip():
    """Fetches the current public IP."""
    try:
        with _http_lock:
            now = time.monotonic()
            cached = _public_ip_cache.get("value")
            if cached and now - float(_public_ip_cache.get("timestamp", 0.0)) <= 20:
                return cached
            if now < float(_public_ip_cache.get("next_retry", 0.0)):
                return cached
            response = _http_session.get("https://api.ipify.org?format=json", timeout=8)
            response.raise_for_status()
            ip = response.json().get("ip")
            if ip:
                ip = str(ip_address(str(ip).strip()))
            _public_ip_cache.update({"value": ip, "timestamp": now, "failures": 0, "next_retry": 0.0})
        return ip
    except (requests.RequestException, ValueError, KeyError):
        with _http_lock:
            failures = int(_public_ip_cache.get("failures", 0)) + 1
            backoff = min(300, 5 * (2 ** min(failures, 5)))
            _public_ip_cache.update({"failures": failures, "next_retry": now + backoff})
        logger().warning("public_ip_fetch_failed failures=%s next_retry_seconds=%s", failures, backoff, exc_info=True)
        return None


def update_ddns(url):
    """Hits the DDNS update URL."""
    valid, normalized_or_error = validate_http_url(url, required=True)
    if not valid:
        return False, normalized_or_error
    url = normalized_or_error
    try:
        with _http_lock:
            response = _http_session.get(url, timeout=10)
        if 200 <= response.status_code < 300:
            logger().info("ddns_update ok=True url=%s status=%s", sanitize_url(url, redact_path=True), response.status_code)
            return True, "DDNS updated successfully."
        logger().warning("ddns_update_failed url=%s status=%s", sanitize_url(url, redact_path=True), response.status_code)
        return False, f"Server returned status {response.status_code}"
    except requests.RequestException as e:
        logger().warning("ddns_update_failed url=%s error=%s", sanitize_url(url, redact_path=True), e)
        return False, f"Connection error: {e}"


def measure_latency(ip):
    """Measures ICMP latency to an IP in milliseconds."""
    if not ip or not re.match(r"^[\d.]+$", str(ip).strip()):
        return "n/a"
    try:
        delay = ping(str(ip).strip(), timeout=2)
        if delay is None or delay is False:
            return "Timeout"
        return f"{int(delay * 1000)} ms"
    except Exception:
        return "Error"
