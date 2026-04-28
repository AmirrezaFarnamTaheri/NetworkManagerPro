import copy
import json
import os
import subprocess
import threading
import time
import tkinter as tk

import customtkinter as ctk
from PIL import Image

import core
import diagnostics
import traffic_collector

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

APP_VERSION = core.APP_VERSION
SPACING = {"page": 16, "section": 12, "row": 8}
COLORS = {
    "success": "#1F9D66",
    "warning": "#D97706",
    "error": "#DC2626",
    "muted": "#64748B",
    "brand": "#0F766E",
    "brand_dark": "#115E59",
}


class NetworkManagerGUI(ctk.CTk):
    def __init__(self, config, on_close_callback, config_path=None, monitor=None, event_store=None):
        super().__init__()
        self.config = config
        self.config_path = config_path or core.config_path()
        self.on_close_callback = on_close_callback
        self.monitor = monitor
        self.event_store = event_store
        self._alive = True
        self._config_lock = core.config_lock()
        self._plugin_tabs = []
        self._last_restore_snapshot = None
        self._busy_count = 0
        self._running_task_keys = set()
        self._last_plugins_refresh = 0.0

        self.title(core.APP_DISPLAY_NAME)
        self.geometry("1080x760")
        self.minsize(840, 620)
        self._set_icon()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.setup_ui()
        self.after(1000, self._refresh_from_monitor)

    def _set_icon(self):
        icon = core.resource_path("assets", "app.ico")
        if os.path.isfile(icon):
            try:
                self.iconbitmap(icon)
            except tk.TclError:
                core.logger().debug("window_icon_failed", exc_info=True)

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        title_font = ctk.CTkFont(size=22, weight="bold")
        label_font = ctk.CTkFont(size=14, weight="bold")
        body_font = ctk.CTkFont(size=13)
        small_font = ctk.CTkFont(size=12)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(14, 4))
        header.grid_columnconfigure(1, weight=1)

        brand = ctk.CTkFrame(header, fg_color="transparent")
        brand.grid(row=0, column=0, sticky="w")
        self.logo_image = self._load_logo()
        if self.logo_image:
            ctk.CTkLabel(brand, text="", image=self.logo_image).pack(side="left", padx=(0, 10))
        brand_text = ctk.CTkFrame(brand, fg_color="transparent")
        brand_text.pack(side="left")
        ctk.CTkLabel(brand_text, text=core.APP_DISPLAY_NAME, font=title_font, anchor="w").pack(anchor="w")
        ctk.CTkLabel(
            brand_text,
            text="DNS, proxy, DDNS, diagnostics, and traffic awareness in one safe control plane",
            font=small_font,
            text_color=COLORS["muted"],
            anchor="w",
        ).pack(anchor="w")

        self.admin_badge = ctk.CTkLabel(
            header,
            text="Admin" if core.is_admin() else "No admin",
            font=small_font,
            text_color=COLORS["success"] if core.is_admin() else COLORS["warning"],
        )
        self.admin_badge.grid(row=0, column=2, sticky="e", padx=(8, 0))

        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 8))
        top_bar.grid_columnconfigure(2, weight=1)
        ctk.CTkLabel(top_bar, text="Appearance", font=small_font).grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.theme_var = ctk.StringVar(value=ctk.get_appearance_mode())
        ctk.CTkSegmentedButton(
            top_bar,
            values=["System", "Dark", "Light"],
            variable=self.theme_var,
            command=self._on_theme_change,
            font=small_font,
        ).grid(row=0, column=1, sticky="w")

        self.activity_label = ctk.CTkLabel(
            top_bar,
            text="Ready",
            font=small_font,
            text_color=COLORS["muted"],
        )
        self.activity_label.grid(row=0, column=2, sticky="e", padx=(10, 12))

        self.toast_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        self.toast_frame.grid(row=0, column=3, sticky="e")

        self.tabs = ctk.CTkTabview(self)
        self.tabs.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 12))

        for name in (
            "Dashboard",
            "DNS",
            "Proxy",
            "DDNS",
            "Tools",
            "History",
            "Traffic",
            "Plugins",
            "Settings Monitor",
            "Settings",
            "Help",
            "About",
        ):
            self.tabs.add(name)

        self._build_dashboard_tab(self.tabs.tab("Dashboard"), label_font, body_font, small_font)
        self._build_dns_tab(self.tabs.tab("DNS"), label_font, small_font)
        self._build_proxy_tab(self.tabs.tab("Proxy"), label_font, body_font, small_font)
        self._build_ddns_tab(self.tabs.tab("DDNS"), label_font, body_font, small_font)
        self._build_tools_tab(self.tabs.tab("Tools"), label_font, small_font)
        self._build_history_tab(self.tabs.tab("History"), label_font, body_font, small_font)
        self._build_traffic_tab(self.tabs.tab("Traffic"), label_font, body_font, small_font)
        self._build_plugins_tab(self.tabs.tab("Plugins"), label_font, body_font, small_font)
        self._build_settings_monitor_tab(self.tabs.tab("Settings Monitor"), label_font, body_font, small_font)
        self._build_settings_tab(self.tabs.tab("Settings"), label_font, small_font)
        self._build_help_tab(self.tabs.tab("Help"), label_font, body_font, small_font)
        self._build_about_tab(self.tabs.tab("About"), title_font, small_font)

        self._refresh_proxy_status()
        self._refresh_history()

    def register_plugin_tab(self, plugin_id, title, builder):
        def _register():
            base_title = f"Plugin: {title}"
            existing = {name for _plugin_id, name in self._plugin_tabs}
            existing.update(
                [
                    "Dashboard",
                    "DNS",
                    "Proxy",
                    "DDNS",
                    "Tools",
                    "History",
                    "Traffic",
                    "Plugins",
                    "Settings Monitor",
                    "Settings",
                    "Help",
                    "About",
                ]
            )
            tab_title = base_title
            suffix = 2
            while tab_title in existing:
                tab_title = f"{base_title} ({suffix})"
                suffix += 1
            created = False
            try:
                self.tabs.add(tab_title)
                created = True
                parent = self.tabs.tab(tab_title)
                builder(parent)
                self._plugin_tabs.append((plugin_id, tab_title))
            except Exception as exc:
                if created:
                    try:
                        self.tabs.delete(tab_title)
                    except Exception:
                        core.logger().debug("plugin_tab_remove_failed title=%s", tab_title, exc_info=True)
                core.logger().warning("plugin_ui_failed id=%s title=%s", plugin_id, title, exc_info=True)
                self.show_toast("Error", f"Plugin UI failed: {exc}")

        self.after(0, _register)

    def _load_logo(self):
        for name in ("tray_64.png", "tray_48.png"):
            path = core.resource_path("assets", name)
            if os.path.isfile(path):
                try:
                    img = Image.open(path)
                    return ctk.CTkImage(light_image=img, dark_image=img, size=(34, 34))
                except OSError:
                    core.logger().debug("logo_load_failed path=%s", path, exc_info=True)
        return None

    def _on_theme_change(self, mode):
        ctk.set_appearance_mode(mode)

    def _on_dns_profile_write(self, *_args):
        self._status_dns_profile = self.dns_var.get()

    def _page(self, parent):
        frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=SPACING["page"], pady=SPACING["page"])
        frame.grid_columnconfigure(0, weight=1)
        return frame

    def _status_card(self, parent, title, value="Loading..."):
        card = ctk.CTkFrame(parent, corner_radius=8)
        card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=12), text_color=COLORS["muted"]).grid(
            row=0, column=0, sticky="w", padx=12, pady=(10, 2)
        )
        label = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=15, weight="bold"), anchor="w", justify="left")
        label.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))
        return card, label

    def _build_dashboard_tab(self, parent, label_font, body_font, small_font):
        page = self._page(parent)
        hero = ctk.CTkFrame(page, corner_radius=14, fg_color=(("#E6FFFA", "#123331")))
        hero.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        hero.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(hero, text="Network command center", font=ctk.CTkFont(size=20, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=16, pady=(14, 4)
        )
        ctk.CTkLabel(
            hero,
            text="Start here: confirm status, apply a DNS profile, turn proxy off quickly, or export diagnostics when something feels off.",
            font=body_font,
            text_color=COLORS["muted"],
            justify="left",
            anchor="w",
            wraplength=820,
        ).grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 14))

        ctk.CTkLabel(page, text="Current network state", font=label_font).grid(row=1, column=0, sticky="w")
        grid = ctk.CTkFrame(page, fg_color="transparent")
        grid.grid(row=2, column=0, sticky="ew", pady=(10, 8))
        for col in range(3):
            grid.grid_columnconfigure(col, weight=1)
        cards = [
            ("Public IP", "dashboard_public_ip"),
            ("Active Interface", "dashboard_interface"),
            ("DNS Servers", "dashboard_dns"),
            ("Gateway", "dashboard_gateway"),
            ("Proxy", "dashboard_proxy"),
            ("DDNS", "dashboard_ddns"),
            ("Monitor Health", "dashboard_health"),
        ]
        self.dashboard_labels = {}
        for index, (title, key) in enumerate(cards):
            card, label = self._status_card(grid, title)
            card.grid(row=index // 3, column=index % 3, sticky="ew", padx=6, pady=6)
            self.dashboard_labels[key] = label

        actions = ctk.CTkFrame(page, fg_color="transparent")
        actions.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        ctk.CTkButton(actions, text="Apply DNS", command=self.apply_dns).pack(side="left", padx=(0, 8))
        ctk.CTkButton(actions, text="DNS Auto", command=self.clear_dns, fg_color="gray").pack(side="left", padx=8)
        ctk.CTkButton(actions, text="Disable Proxy", command=self.disable_proxy, fg_color="#E74C3C").pack(side="left", padx=8)
        ctk.CTkButton(actions, text="Force DDNS", command=self.force_update_ddns).pack(side="left", padx=8)
        ctk.CTkButton(actions, text="Restore", command=self.restore_previous_settings, fg_color="#6B7280").pack(
            side="left", padx=8
        )

        checklist = ctk.CTkFrame(page, corner_radius=8)
        checklist.grid(row=4, column=0, sticky="ew", pady=(18, 0))
        checklist.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(checklist, text="First-run checklist", font=label_font).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 6))
        self.checklist_label = ctk.CTkLabel(checklist, text="", font=body_font, justify="left", anchor="w")
        self.checklist_label.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))

        insights = ctk.CTkFrame(page, corner_radius=8)
        insights.grid(row=5, column=0, sticky="ew", pady=(12, 0))
        insights.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(insights, text="Network insights", font=label_font).grid(
            row=0, column=0, sticky="w", padx=12, pady=(10, 6)
        )
        self.insights_label = ctk.CTkLabel(
            insights,
            text="Waiting for the first monitor snapshot...",
            font=body_font,
            justify="left",
            anchor="w",
            wraplength=880,
        )
        self.insights_label.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))

    def _build_dns_tab(self, parent, label_font, small_font):
        page = self._page(parent)
        page.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(page, text="Interface", font=label_font).grid(row=0, column=0, sticky="w")
        self.interface_var = ctk.StringVar(value="(Auto - active default route)")
        self.interface_menu = ctk.CTkOptionMenu(page, variable=self.interface_var, values=self._interface_values())
        self.interface_menu.grid(row=1, column=0, sticky="ew", pady=4)
        ctk.CTkButton(page, text="Refresh interfaces", command=self._refresh_interfaces, font=small_font).grid(
            row=2, column=0, sticky="e", pady=4
        )

        dns_profiles = self._dns_profile_names()
        ctk.CTkLabel(page, text="DNS profile", font=label_font).grid(row=3, column=0, sticky="w", pady=(12, 0))
        self.dns_var = ctk.StringVar(value=dns_profiles[0])
        self.dns_dropdown = ctk.CTkOptionMenu(page, variable=self.dns_var, values=dns_profiles)
        self.dns_dropdown.grid(row=4, column=0, sticky="ew", pady=6)
        self._status_dns_profile = self.dns_var.get()
        self.dns_var.trace_add("write", self._on_dns_profile_write)

        btn_row = ctk.CTkFrame(page, fg_color="transparent")
        btn_row.grid(row=5, column=0, sticky="w", pady=8)
        self.apply_dns_button = ctk.CTkButton(btn_row, text="Apply DNS", width=150, command=self.apply_dns)
        self.apply_dns_button.pack(side="left", padx=(0, 8))
        self.clear_dns_button = ctk.CTkButton(btn_row, text="Set to Auto", width=150, command=self.clear_dns, fg_color="gray")
        self.clear_dns_button.pack(side="left", padx=8)
        ctk.CTkButton(btn_row, text="Delete profile", width=150, command=self.delete_dns_profile, fg_color="#6B7280").pack(
            side="left", padx=8
        )

        self.ping_label = ctk.CTkLabel(page, text="Ping: n/a", text_color=COLORS["muted"], font=small_font)
        self.ping_label.grid(row=6, column=0, sticky="w", pady=(8, 4))
        self.admin_hint = ctk.CTkLabel(
            page,
            text="DNS changes require administrator rights. Relaunch as admin if these controls are disabled.",
            font=small_font,
            text_color=COLORS["warning"],
            justify="left",
            anchor="w",
        )
        self.admin_hint.grid(row=7, column=0, sticky="ew", pady=8)
        ctk.CTkLabel(
            page,
            text="Tip: leave Interface on Auto unless Windows chooses a VPN, VM, or inactive adapter. Restore captures the previous DNS before changes.",
            font=small_font,
            text_color=COLORS["muted"],
            justify="left",
            anchor="w",
            wraplength=760,
        ).grid(row=8, column=0, sticky="ew", pady=(4, 0))

        custom = ctk.CTkFrame(page, corner_radius=10)
        custom.grid(row=9, column=0, sticky="ew", pady=(18, 0))
        custom.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(custom, text="Custom DNS profile", font=label_font).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(12, 6)
        )
        ctk.CTkLabel(custom, text="Name", font=small_font).grid(row=1, column=0, sticky="w", padx=12, pady=4)
        self.custom_dns_name_var = ctk.StringVar(value="Custom")
        ctk.CTkEntry(custom, textvariable=self.custom_dns_name_var, placeholder_text="Profile name").grid(
            row=1, column=1, sticky="ew", padx=(0, 12), pady=4
        )
        ctk.CTkLabel(custom, text="Servers", font=small_font).grid(row=2, column=0, sticky="w", padx=12, pady=4)
        self.custom_dns_servers_var = ctk.StringVar(value="")
        ctk.CTkEntry(custom, textvariable=self.custom_dns_servers_var, placeholder_text="1.1.1.1, 1.0.0.1").grid(
            row=2, column=1, sticky="ew", padx=(0, 12), pady=4
        )
        custom_actions = ctk.CTkFrame(custom, fg_color="transparent")
        custom_actions.grid(row=3, column=1, sticky="e", padx=12, pady=(6, 12))
        ctk.CTkButton(custom_actions, text="Save profile", command=self.save_custom_dns_profile, font=small_font).pack(
            side="left", padx=(0, 8)
        )
        ctk.CTkButton(custom_actions, text="Apply once", command=self.apply_custom_dns, font=small_font).pack(side="left")
        if not core.is_admin():
            self.apply_dns_button.configure(state="disabled")
            self.clear_dns_button.configure(state="disabled")
        else:
            self.admin_hint.grid_remove()

    def _interface_values(self):
        return ["(Auto - active default route)"] + core.list_interface_aliases()

    def _dns_profile_names(self):
        profiles_map = self.config.get("dns_profiles", {})
        if not isinstance(profiles_map, dict):
            profiles_map = {}
        names = list(profiles_map.keys())
        return names or ["(no profiles in config)"]

    def _refresh_interfaces(self):
        vals = self._interface_values()
        self.interface_menu.configure(values=vals)
        if self.interface_var.get() not in vals:
            self.interface_var.set(vals[0])

    def _selected_interface(self):
        v = self.interface_var.get()
        return None if v.startswith("(Auto") else v

    def _build_proxy_tab(self, parent, label_font, body_font, small_font):
        page = self._page(parent)
        ctk.CTkLabel(page, text="System proxy", font=label_font).grid(row=0, column=0, sticky="w")
        proxy_profiles = self.config.get("proxy_profiles")
        if not isinstance(proxy_profiles, list) or not proxy_profiles:
            proxy_profiles = ["127.0.0.1:8080"]
        self.proxy_var = ctk.StringVar(value=proxy_profiles[0])
        self.proxy_dropdown = ctk.CTkOptionMenu(page, variable=self.proxy_var, values=proxy_profiles)
        self.proxy_dropdown.grid(row=1, column=0, sticky="ew", pady=8)

        btn_row = ctk.CTkFrame(page, fg_color="transparent")
        btn_row.grid(row=2, column=0, sticky="w", pady=8)
        ctk.CTkButton(btn_row, text="Enable proxy", width=150, command=self.enable_proxy, fg_color="#2FA572").pack(
            side="left", padx=(0, 8)
        )
        ctk.CTkButton(btn_row, text="Disable proxy", width=150, command=self.disable_proxy, fg_color="#E74C3C").pack(
            side="left", padx=8
        )
        ctk.CTkButton(btn_row, text="Delete profile", width=150, command=self.delete_proxy_profile, fg_color="#6B7280").pack(
            side="left", padx=8
        )

        self.proxy_status = ctk.CTkLabel(page, text="Proxy: ...", font=body_font)
        self.proxy_status.grid(row=3, column=0, sticky="w", pady=(16, 4))
        ctk.CTkButton(page, text="Refresh proxy status", command=self._refresh_proxy_status, font=small_font).grid(
            row=4, column=0, sticky="w", pady=4
        )
        ctk.CTkLabel(
            page,
            text="Proxy changes affect the current Windows user. Apps with their own proxy settings may ignore this switch.",
            font=small_font,
            text_color=COLORS["muted"],
            justify="left",
            anchor="w",
            wraplength=760,
        ).grid(row=5, column=0, sticky="ew", pady=(10, 0))

        custom = ctk.CTkFrame(page, corner_radius=10)
        custom.grid(row=6, column=0, sticky="ew", pady=(18, 0))
        custom.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(custom, text="Add proxy profile", font=label_font).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(12, 6)
        )
        ctk.CTkLabel(custom, text="Server", font=small_font).grid(row=1, column=0, sticky="w", padx=12, pady=4)
        self.custom_proxy_var = ctk.StringVar(value="")
        ctk.CTkEntry(custom, textvariable=self.custom_proxy_var, placeholder_text="127.0.0.1:8080").grid(
            row=1, column=1, sticky="ew", padx=(0, 12), pady=4
        )
        ctk.CTkButton(custom, text="Save proxy", command=self.save_custom_proxy_profile, font=small_font).grid(
            row=2, column=1, sticky="e", padx=12, pady=(6, 12)
        )

    def _build_ddns_tab(self, parent, label_font, body_font, small_font):
        page = self._page(parent)
        ctk.CTkLabel(page, text="Dynamic DNS", font=label_font).grid(row=0, column=0, sticky="w")
        self.ip_label = ctk.CTkLabel(page, text="Public IP: ...", font=body_font)
        self.ip_label.grid(row=1, column=0, sticky="w", pady=6)

        ctk.CTkLabel(page, text="Update URL (GET)", font=label_font).grid(row=2, column=0, sticky="w", pady=(8, 2))
        self.ddns_url_var = ctk.StringVar(value=core.get_ddns_update_url(self.config) or "")
        self.ddns_url_entry = ctk.CTkEntry(page, textvariable=self.ddns_url_var, placeholder_text="https://...")
        self.ddns_url_entry.grid(row=3, column=0, sticky="ew", pady=4)
        ctk.CTkButton(page, text="Save DDNS URL", command=self.save_ddns_url, font=small_font).grid(row=4, column=0, sticky="w", pady=4)
        ctk.CTkButton(page, text="Force sync DDNS", command=self.force_update_ddns).grid(row=5, column=0, sticky="w", pady=10)
        ctk.CTkLabel(
            page,
            text="The URL is redacted in logs and diagnostics. Auto-DDNS stays off until a valid URL is saved.",
            font=small_font,
            text_color=COLORS["muted"],
            justify="left",
            anchor="w",
        ).grid(row=6, column=0, sticky="ew", pady=8)

    def _build_tools_tab(self, parent, label_font, small_font):
        page = self._page(parent)
        ctk.CTkLabel(page, text="Maintenance", font=label_font).grid(row=0, column=0, sticky="w", pady=(0, 8))
        ctk.CTkButton(page, text="Flush DNS cache", command=self.flush_dns, width=220).grid(row=1, column=0, sticky="w", pady=6)
        ctk.CTkButton(page, text="Renew DHCP", command=self.renew_dhcp, width=220).grid(row=2, column=0, sticky="w", pady=6)
        ctk.CTkButton(page, text="Copy diagnostics", command=self.copy_diagnostics, width=220).grid(row=3, column=0, sticky="w", pady=6)
        ctk.CTkButton(page, text="Export diagnostics bundle", command=self.export_diagnostics, width=220).grid(
            row=4, column=0, sticky="w", pady=6
        )
        ctk.CTkButton(page, text="Restore previous settings", command=self.restore_previous_settings, width=220).grid(
            row=5, column=0, sticky="w", pady=6
        )

    def _build_history_tab(self, parent, label_font, body_font, small_font):
        page = self._page(parent)
        toolbar = ctk.CTkFrame(page, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(toolbar, text="Event history", font=label_font).pack(side="left")
        ctk.CTkButton(toolbar, text="Refresh", command=self._refresh_history, font=small_font, width=90).pack(side="right")
        self.history_box = ctk.CTkTextbox(page, height=420, font=ctk.CTkFont(family="Consolas", size=12))
        self.history_box.grid(row=1, column=0, sticky="nsew", pady=(10, 0))

    def _build_traffic_tab(self, parent, label_font, body_font, small_font):
        page = self._page(parent)
        ctk.CTkLabel(page, text="Traffic manager", font=label_font).grid(row=0, column=0, sticky="w")
        self.traffic_box = ctk.CTkTextbox(page, height=420, font=ctk.CTkFont(family="Consolas", size=12))
        self.traffic_box.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        ctk.CTkButton(page, text="Refresh processes", command=self._refresh_traffic, font=small_font).grid(
            row=2, column=0, sticky="w", pady=10
        )
        self._refresh_traffic()

    def _build_plugins_tab(self, parent, label_font, body_font, small_font):
        page = self._page(parent)
        page.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(page, text="Plugin center", font=label_font).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            page,
            text="Trusted local plugins can add tabs, scheduled checks, and history events. Enable them by adding their id to plugins.enabled in config.json.",
            font=body_font,
            text_color=COLORS["muted"],
            justify="left",
            anchor="w",
            wraplength=760,
        ).grid(row=1, column=0, sticky="ew", pady=(6, 10))
        actions = ctk.CTkFrame(page, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="w")
        ctk.CTkButton(actions, text="Refresh plugins", command=lambda: self._refresh_plugins(force=True), font=small_font).pack(side="left", padx=(0, 8))
        ctk.CTkButton(actions, text="Open plugins folder", command=lambda: self._open_folder(core.plugins_dir()), font=small_font).pack(
            side="left"
        )
        self.plugins_box = ctk.CTkTextbox(page, height=360, font=ctk.CTkFont(family="Consolas", size=12))
        self.plugins_box.grid(row=3, column=0, sticky="nsew", pady=(12, 0))
        self._refresh_plugins()

    def _build_settings_monitor_tab(self, parent, label_font, body_font, small_font):
        page = self._page(parent)
        ctk.CTkLabel(page, text="Settings monitor", font=label_font).grid(row=0, column=0, sticky="w")
        self.settings_monitor_label = ctk.CTkLabel(page, text="Waiting for monitor data...", font=body_font, justify="left", anchor="w")
        self.settings_monitor_label.grid(row=1, column=0, sticky="ew", pady=(10, 0))

    def _build_settings_tab(self, parent, label_font, small_font):
        page = self._page(parent)
        if not isinstance(self.config.get("settings"), dict):
            self.config["settings"] = {}
        st = self.config["settings"]
        ctk.CTkLabel(page, text="Startup", font=label_font).grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.startup_var = ctk.BooleanVar(value=core.get_run_at_startup())
        ctk.CTkSwitch(page, text="Run at Windows logon", variable=self.startup_var, command=self._on_startup_toggle, font=small_font).grid(
            row=1, column=0, sticky="w", pady=6
        )
        self.tray_close_var = ctk.BooleanVar(value=core.parse_bool(st.get("minimize_to_tray_on_close", True), True))
        ctk.CTkSwitch(page, text="Minimize to tray on close", variable=self.tray_close_var, font=small_font).grid(
            row=2, column=0, sticky="w", pady=6
        )
        self.auto_ddns_var = ctk.BooleanVar(value=core.parse_bool(st.get("auto_update_ddns", False), False))
        ctk.CTkSwitch(page, text="Auto-update DDNS when public IP changes", variable=self.auto_ddns_var).grid(
            row=3, column=0, sticky="w", pady=6
        )
        ctk.CTkLabel(page, text="Check interval (seconds)", font=small_font).grid(row=4, column=0, sticky="w", pady=(12, 2))
        try:
            interval_default = int(st.get("check_interval_seconds", 60))
        except (TypeError, ValueError):
            interval_default = 60
        self.interval_var = ctk.StringVar(value=str(interval_default))
        ctk.CTkEntry(page, textvariable=self.interval_var, width=140).grid(row=5, column=0, sticky="w", pady=4)
        ctk.CTkButton(page, text="Save settings", command=self.save_settings).grid(row=6, column=0, sticky="w", pady=16)

    def _build_help_tab(self, parent, label_font, body_font, small_font):
        page = self._page(parent)
        ctk.CTkLabel(page, text="Quick help", font=label_font).grid(row=0, column=0, sticky="w")
        quickstart = (
            "1. Dashboard: check current state and use quick actions.\n"
            "2. DNS: choose Auto interface and apply a trusted profile.\n"
            "3. Proxy: enable a saved proxy or disable it when connectivity breaks.\n"
            "4. Tools: export diagnostics before asking for help.\n"
            "5. History: review what changed and when."
        )
        ctk.CTkLabel(page, text=quickstart, font=body_font, justify="left", anchor="w").grid(
            row=1, column=0, sticky="ew", pady=(8, 14)
        )
        ctk.CTkLabel(page, text="Paths", font=label_font).grid(row=2, column=0, sticky="w")
        help_text = (
            f"Config: {self.config_path}\n"
            f"Logs: {core.logs_dir()}\n"
            f"History: {core.history_events_path()}\n"
            f"Plugins: {core.plugins_dir()}\n\n"
            "Use Dashboard for live status, History for recent actions and detected changes, "
            "and Tools for diagnostics export."
        )
        ctk.CTkLabel(page, text=help_text, font=body_font, justify="left", anchor="w").grid(row=3, column=0, sticky="ew", pady=10)
        buttons = ctk.CTkFrame(page, fg_color="transparent")
        buttons.grid(row=4, column=0, sticky="w")
        ctk.CTkButton(buttons, text="Open config folder", command=lambda: self._open_folder(os.path.dirname(self.config_path))).pack(side="left", padx=(0, 8))
        ctk.CTkButton(buttons, text="Open logs", command=lambda: self._open_folder(core.logs_dir())).pack(side="left", padx=8)
        docs = ctk.CTkFrame(page, fg_color="transparent")
        docs.grid(row=5, column=0, sticky="w", pady=(10, 0))
        for label, filename in (
            ("Quickstart", "QUICKSTART.md"),
            ("Usage Guide", "USAGE.md"),
            ("Troubleshooting", "TROUBLESHOOTING.md"),
            ("Config Reference", "CONFIG.md"),
        ):
            ctk.CTkButton(docs, text=label, command=lambda f=filename: self._open_doc(f), font=small_font).pack(
                side="left", padx=(0, 8), pady=4
            )

    def _build_about_tab(self, parent, title_font, small_font):
        page = self._page(parent)
        ctk.CTkLabel(page, text=f"Version {APP_VERSION}", font=title_font).grid(row=0, column=0, sticky="w", pady=(0, 8))
        ctk.CTkLabel(
            page,
            text="Windows DNS profiles, system proxy, DDNS updates, monitoring history, diagnostics, and v1 plugins.",
            font=small_font,
            justify="left",
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", pady=4)

    def _refresh_from_monitor(self):
        if not self._alive:
            return
        state = self.monitor.snapshot() if self.monitor else None
        if state:
            self._apply_state(state)
        self._sync_profile_menus()
        self._refresh_plugins()
        self.after(3000, self._refresh_from_monitor)

    def _apply_state(self, state):
        ip_text = state.public_ip or "Offline / unreachable"
        dns_text = ", ".join(state.dns_servers) if state.dns_servers else "Automatic or unavailable"
        proxy_text = "ON" if state.proxy_enabled else "OFF"
        if state.proxy_enabled and state.proxy_server:
            proxy_text += f" - {core.sanitize_proxy_server(state.proxy_server)}"
        values = {
            "dashboard_public_ip": ip_text,
            "dashboard_interface": state.interface or "Unknown",
            "dashboard_dns": dns_text,
            "dashboard_gateway": state.gateway or "Unknown",
            "dashboard_proxy": proxy_text,
            "dashboard_ddns": state.ddns_last_result,
            "dashboard_health": state.monitor_error or "Healthy",
        }
        for key, value in values.items():
            self.dashboard_labels[key].configure(text=value)
        self.ip_label.configure(text=f"Public IP: {ip_text}")
        self.ping_label.configure(text=f"Ping: {state.latency}")
        self.proxy_status.configure(text=f"Proxy: {proxy_text}")
        self.settings_monitor_label.configure(
            text=(
                f"Effective DNS: {dns_text}\n"
                f"Proxy: {proxy_text}\n"
                "Attribution: Unknown unless a plugin or future ETW collector supplies a process."
            )
        )
        self.checklist_label.configure(
            text=(
                f"Admin rights: {'yes' if core.is_admin() else 'no'}\n"
                f"Config exists: {'yes' if os.path.exists(self.config_path) else 'no'}\n"
                f"DDNS URL set: {'yes' if core.get_ddns_update_url(self.config) else 'no'}\n"
                f"Last monitor update: {int(state.timestamp)}\n"
                f"Monitor health: {state.monitor_error or 'healthy'}"
            )
        )
        if hasattr(self, "insights_label"):
            self.insights_label.configure(text=self._network_insights(state))

    def _network_insights(self, state):
        notes = []
        if state.monitor_error:
            notes.append(f"Monitor needs attention: {state.monitor_error}")
        if not state.interface:
            notes.append("No active interface detected. Check adapter status or VPN routing.")
        if not state.public_ip:
            notes.append("Public IP lookup is offline or rate-limited; DDNS sync is paused until it recovers.")
        if not state.dns_servers:
            notes.append("DNS appears automatic or unavailable. Apply a profile if name resolution is unreliable.")
        if state.proxy_enabled:
            notes.append(f"Proxy is enabled ({state.proxy_server or 'server unknown'}). Disable it first when web apps cannot connect.")
        if state.latency in ("Timeout", "Error"):
            notes.append("The selected DNS profile is not responding to ping; try another profile or refresh the interface.")
        if not notes:
            notes.append("Everything looks steady. Keep this dashboard open while changing DNS, proxy, or DDNS settings.")
        return "\n".join(f"- {note}" for note in notes)

    def _refresh_proxy_status(self):
        on, server = core.get_proxy_state()
        text = f"Proxy: {'ON' if on else 'OFF'}"
        if on and server:
            text += f" - {core.sanitize_proxy_server(server)}"
        if hasattr(self, "proxy_status"):
            self.proxy_status.configure(text=text)

    def _refresh_history(self):
        if not hasattr(self, "history_box"):
            return
        events = self.event_store.recent(120) if self.event_store else []
        text = ""
        for event in events:
            try:
                stamp = f"{float(event.get('timestamp', 0)):.0f}"
            except (TypeError, ValueError):
                stamp = ""
            text += f"{stamp}  {event.get('type', ''):<24} {event.get('summary', '')}\n"
        self.history_box.configure(state="normal")
        self.history_box.delete("1.0", "end")
        self.history_box.insert("1.0", text or "No events yet.")
        self.history_box.configure(state="disabled")

    def _refresh_traffic(self):
        if not hasattr(self, "traffic_box"):
            return

        def _work():
            totals = traffic_collector.system_totals()
            rows = [
                "System totals",
                f"  down: {traffic_collector.format_bytes(totals['bytes_recv'])}    up: {traffic_collector.format_bytes(totals['bytes_sent'])}",
                f"  packets down: {totals['packets_recv']:,}    packets up: {totals['packets_sent']:,}",
                "",
                "Top processes by active connections",
                "   PID  EST  CONN  Name                 Remotes",
            ]
            for proc in traffic_collector.collect_connections():
                remotes = ", ".join(proc.remotes)
                rows.append(f"{proc.pid:>6}  {proc.established:>3}  {proc.connections:>4}  {proc.name[:20]:<20} {remotes}")
            return "\n".join(rows)

        def _done(text):
            self.traffic_box.configure(state="normal")
            self.traffic_box.delete("1.0", "end")
            self.traffic_box.insert("1.0", text)
            self.traffic_box.configure(state="disabled")

        self._run_task("Refreshing traffic", _work, _done, key="traffic")

    def _refresh_plugins(self, force=False):
        if not hasattr(self, "plugins_box"):
            return
        now = time.monotonic()
        if not force and self._last_plugins_refresh and now - self._last_plugins_refresh < 30:
            return
        self._last_plugins_refresh = now
        enabled = set()
        plugins_cfg = self.config.get("plugins") if isinstance(self.config, dict) else {}
        if isinstance(plugins_cfg, dict) and isinstance(plugins_cfg.get("enabled"), list):
            enabled = {str(item) for item in plugins_cfg.get("enabled")}

        rows = [
            f"User plugins folder: {core.plugins_dir()}",
            f"Bundled plugins folder: {core.bundled_plugins_dir()}",
            "",
            "ID                         Enabled  Name / Version / Entry",
        ]
        manifests = self._discover_plugin_manifests()
        if not manifests:
            rows.append("(No plugin manifests found.)")
        for manifest_path, manifest, error in manifests:
            if error:
                rows.append(f"{os.path.basename(os.path.dirname(manifest_path)):<26} ERROR    {error}")
                continue
            plugin_id = str(manifest.get("id", ""))
            status = "yes" if plugin_id in enabled else "no"
            label = f"{manifest.get('name', 'Unnamed')} {manifest.get('version', '')} -> {manifest.get('entrypoint', '')}"
            rows.append(f"{plugin_id:<26} {status:<7} {label}")
        self.plugins_box.configure(state="normal")
        self.plugins_box.delete("1.0", "end")
        self.plugins_box.insert("1.0", "\n".join(rows))
        self.plugins_box.configure(state="disabled")

    def _discover_plugin_manifests(self):
        manifests = []
        seen_roots = set()
        for root in (core.plugins_dir(), core.bundled_plugins_dir()):
            if root in seen_roots:
                continue
            seen_roots.add(root)
            if not os.path.isdir(root):
                continue
            try:
                names = sorted(os.listdir(root))
            except OSError as exc:
                manifests.append((root, {}, str(exc)))
                continue
            for name in names:
                manifest_path = os.path.join(root, name, "plugin.json")
                if not os.path.isfile(manifest_path):
                    continue
                try:
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        manifests.append((manifest_path, json.load(f), None))
                except (OSError, json.JSONDecodeError) as exc:
                    manifests.append((manifest_path, {}, str(exc)))
        return manifests

    def _capture_restore_snapshot(self):
        snapshot = self._current_restore_snapshot(self._selected_interface())
        self._last_restore_snapshot = snapshot
        self._record_event("settings.snapshot", "Restore point captured", snapshot)
        return snapshot

    def _current_restore_snapshot(self, selected_interface=None):
        interface = selected_interface or core.get_active_interface_alias()
        proxy_settings = core.get_proxy_settings()
        dns_state = core.get_dns_restore_state(interface)
        return {
            "interface": interface,
            "dns_servers": dns_state.get("dns_servers_v4", []),
            "dns_servers_v4": dns_state.get("dns_servers_v4", []),
            "dns_servers_v6": dns_state.get("dns_servers_v6", []),
            "proxy_enabled": proxy_settings.get("proxy_enabled", False),
            "proxy_server": proxy_settings.get("proxy_server"),
            "proxy_settings": proxy_settings,
        }

    def _store_restore_snapshot(self, snapshot):
        self._last_restore_snapshot = snapshot
        self._record_event("settings.snapshot", "Restore point captured", snapshot)

    def _store_restore_snapshot_if_success(self, snapshot, success):
        if success:
            self._store_restore_snapshot(snapshot)
        else:
            self._record_event(
                "settings.snapshot_skipped",
                "Restore point not updated because operation failed",
                {"snapshot": snapshot},
            )

    def _sync_profile_menus(self):
        with self._config_lock:
            if self.monitor:
                monitored_config = self.monitor.config_snapshot()
                if isinstance(monitored_config, dict):
                    self.config = monitored_config
            else:
                disk = core.load_config(self.config_path)
                if isinstance(disk, dict):
                    self.config = disk
            dm = self.config.get("dns_profiles") or {}
            dns_keys = list(dm.keys()) if isinstance(dm, dict) else []
            proxy_vals = self.config.get("proxy_profiles")
            if not isinstance(proxy_vals, list) or not proxy_vals:
                proxy_vals = ["127.0.0.1:8080"]
        dns_keys = dns_keys or ["(no profiles in config)"]
        if hasattr(self, "dns_dropdown"):
            cur_dns = self.dns_var.get()
            self.dns_dropdown.configure(values=dns_keys)
            if cur_dns not in dns_keys:
                self.dns_var.set(dns_keys[0])
        if hasattr(self, "proxy_dropdown"):
            cur_px = self.proxy_var.get()
            self.proxy_dropdown.configure(values=proxy_vals)
            if cur_px not in proxy_vals:
                self.proxy_var.set(proxy_vals[0])

    def _record_event(self, event_type, summary, details=None):
        if self.event_store:
            self.event_store.append(event_type, summary, details or {})
        self._refresh_history()

    def _on_startup_toggle(self):
        ok, msg = core.set_run_at_startup(self.startup_var.get())
        if not ok:
            self.startup_var.set(not self.startup_var.get())
            self.show_toast("Error", msg)
        else:
            self.show_toast("Success", msg)
        self._record_event("startup.changed", msg, {"enabled": self.startup_var.get(), "ok": ok})

    def save_ddns_url(self):
        url = (self.ddns_url_var.get() or "").strip()
        valid, normalized_or_error = core.validate_http_url(url)
        if not valid:
            self.show_toast("Error", normalized_or_error)
            return
        url = normalized_or_error
        with self._config_lock:
            if not isinstance(self.config.get("settings"), dict):
                self.config["settings"] = {}
            if url:
                self.config["ddns_update_url"] = url
            else:
                self.config.pop("ddns_update_url", None)
                self.config["settings"]["auto_update_ddns"] = False
                if hasattr(self, "auto_ddns_var"):
                    self.auto_ddns_var.set(False)
            cfg = copy.deepcopy(self.config)
        try:
            core.save_config(cfg, self.config_path)
            if self.monitor:
                self.monitor.update_config(cfg)
            self.show_toast("Success", "DDNS URL saved.")
            self._record_event("ddns.url_saved", "DDNS URL saved", {"url": core.sanitize_url(url, redact_path=True)})
        except OSError as e:
            self.show_toast("Error", str(e))

    def save_custom_dns_profile(self):
        name = (self.custom_dns_name_var.get() or "").strip()
        servers = self._parse_server_list(self.custom_dns_servers_var.get())
        if not name:
            self.show_toast("Error", "Enter a DNS profile name.")
            return
        valid, normalized_or_error = core.validate_dns_servers(servers)
        if not valid:
            self.show_toast("Error", normalized_or_error)
            return
        with self._config_lock:
            profiles = self.config.get("dns_profiles")
            if not isinstance(profiles, dict):
                profiles = {}
                self.config["dns_profiles"] = profiles
            profiles[name] = normalized_or_error
            cfg = copy.deepcopy(self.config)
        try:
            core.save_config(cfg, self.config_path)
            if self.monitor:
                self.monitor.update_config(cfg)
            self.dns_var.set(name)
            self._sync_profile_menus()
            self.show_toast("Success", f"DNS profile saved: {name}")
            self._record_event("dns.profile_saved", "DNS profile saved", {"profile": name, "servers": normalized_or_error})
        except OSError as e:
            self.show_toast("Error", str(e))

    def delete_dns_profile(self):
        profile = self.dns_var.get()
        with self._config_lock:
            profiles = self.config.get("dns_profiles")
            if not isinstance(profiles, dict) or profile not in profiles:
                self.show_toast("Error", "Choose a DNS profile to delete.")
                return
            if len(profiles) <= 1:
                self.show_toast("Notice", "Keep at least one DNS profile.")
                return
            removed = profiles.pop(profile)
            cfg = copy.deepcopy(self.config)
        try:
            core.save_config(cfg, self.config_path)
            if self.monitor:
                self.monitor.update_config(cfg)
            self._sync_profile_menus()
            self.show_toast("Success", f"DNS profile deleted: {profile}")
            self._record_event("dns.profile_deleted", "DNS profile deleted", {"profile": profile, "servers": removed})
        except OSError as e:
            self.show_toast("Error", str(e))

    def apply_custom_dns(self):
        servers = self._parse_server_list(self.custom_dns_servers_var.get())
        valid, normalized_or_error = core.validate_dns_servers(servers)
        if not valid:
            self.show_toast("Error", normalized_or_error)
            return
        interface = self._selected_interface()

        def _work():
            snapshot = self._current_restore_snapshot(interface)
            success, msg = core.set_dns(normalized_or_error, interface)
            return snapshot, success, msg

        def _done(result):
            snapshot, success, msg = result
            self._store_restore_snapshot_if_success(snapshot, success)
            self.show_toast("Success" if success else "Error", msg)
            self._record_event("dns.apply_custom", msg, {"ok": success, "servers": normalized_or_error})

        self._run_task("Applying custom DNS", _work, _done, key="dns")

    def save_custom_proxy_profile(self):
        valid, normalized_or_error = core.validate_proxy_server(self.custom_proxy_var.get())
        if not valid:
            self.show_toast("Error", normalized_or_error)
            return
        with self._config_lock:
            profiles = self.config.get("proxy_profiles")
            if not isinstance(profiles, list):
                profiles = []
                self.config["proxy_profiles"] = profiles
            if normalized_or_error not in profiles:
                profiles.append(normalized_or_error)
            cfg = copy.deepcopy(self.config)
        try:
            core.save_config(cfg, self.config_path)
            if self.monitor:
                self.monitor.update_config(cfg)
            self.proxy_var.set(normalized_or_error)
            self._sync_profile_menus()
            self.show_toast("Success", f"Proxy profile saved: {normalized_or_error}")
            self._record_event("proxy.profile_saved", "Proxy profile saved", {"server": normalized_or_error})
        except OSError as e:
            self.show_toast("Error", str(e))

    def delete_proxy_profile(self):
        proxy = self.proxy_var.get()
        with self._config_lock:
            profiles = self.config.get("proxy_profiles")
            if not isinstance(profiles, list) or proxy not in profiles:
                self.show_toast("Error", "Choose a proxy profile to delete.")
                return
            if len(profiles) <= 1:
                self.show_toast("Notice", "Keep at least one proxy profile.")
                return
            profiles.remove(proxy)
            cfg = copy.deepcopy(self.config)
        try:
            core.save_config(cfg, self.config_path)
            if self.monitor:
                self.monitor.update_config(cfg)
            self._sync_profile_menus()
            self.show_toast("Success", f"Proxy profile deleted: {proxy}")
            self._record_event("proxy.profile_deleted", "Proxy profile deleted", {"server": proxy})
        except OSError as e:
            self.show_toast("Error", str(e))

    def _parse_server_list(self, text):
        return [part.strip() for part in str(text or "").replace(";", ",").replace(" ", ",").split(",") if part.strip()]

    def apply_dns(self):
        profile = self.dns_var.get()
        with self._config_lock:
            profiles = self.config.get("dns_profiles") or {}
        if not isinstance(profiles, dict) or profile not in profiles:
            self.show_toast("Error", "Invalid DNS profile.")
            return
        servers = list(profiles[profile])
        interface = self._selected_interface()

        def _work():
            snapshot = self._current_restore_snapshot(interface)
            success, msg = core.set_dns(servers, interface)
            return snapshot, success, msg

        def _done(result):
            snapshot, success, msg = result
            self._store_restore_snapshot_if_success(snapshot, success)
            self.show_toast("Success" if success else "Error", msg)
            self._record_event("dns.apply", msg, {"ok": success, "profile": profile})

        self._run_task(f"Applying {profile}", _work, _done, key="dns")

    def clear_dns(self):
        interface = self._selected_interface()

        def _work():
            snapshot = self._current_restore_snapshot(interface)
            success, msg = core.clear_dns(interface)
            return snapshot, success, msg

        def _done(result):
            snapshot, success, msg = result
            self._store_restore_snapshot_if_success(snapshot, success)
            self.show_toast("Success" if success else "Error", msg)
            self._record_event("dns.clear", msg, {"ok": success})

        self._run_task("Resetting DNS", _work, _done, key="dns")

    def enable_proxy(self):
        proxy = self.proxy_var.get()
        interface = self._selected_interface()

        def _work():
            snapshot = self._current_restore_snapshot(interface)
            success, msg = core.set_proxy(True, proxy)
            return snapshot, success, msg

        def _done(result):
            snapshot, success, msg = result
            self._store_restore_snapshot_if_success(snapshot, success)
            self.show_toast("Success" if success else "Error", msg)
            self._record_event("proxy.enable", msg, {"ok": success, "server": core.sanitize_proxy_server(proxy)})
            self._refresh_proxy_status()

        self._run_task("Enabling proxy", _work, _done, key="proxy")

    def disable_proxy(self):
        interface = self._selected_interface()

        def _work():
            snapshot = self._current_restore_snapshot(interface)
            success, msg = core.set_proxy(False)
            return snapshot, success, msg

        def _done(result):
            snapshot, success, msg = result
            self._store_restore_snapshot_if_success(snapshot, success)
            self.show_toast("Success" if success else "Error", msg)
            self._record_event("proxy.disable", msg, {"ok": success})
            self._refresh_proxy_status()

        self._run_task("Disabling proxy", _work, _done, key="proxy")

    def restore_previous_settings(self):
        snapshot = self._last_restore_snapshot
        if not snapshot:
            self.show_toast("Notice", "No restore point is available yet.")
            return

        def _work():
            dns_servers = []
            if "dns_servers_v4" in snapshot or "dns_servers_v6" in snapshot:
                dns_servers = list(snapshot.get("dns_servers_v4") or []) + list(snapshot.get("dns_servers_v6") or [])
            else:
                dns_servers = snapshot.get("dns_servers") or []
            interface = snapshot.get("interface")
            if dns_servers:
                dns_ok, dns_msg = core.set_dns(dns_servers, interface)
            else:
                dns_ok, dns_msg = core.clear_dns(interface)
            proxy_ok, proxy_msg = core.restore_proxy_settings(snapshot.get("proxy_settings") or snapshot)
            ok = dns_ok and proxy_ok
            msg = "Previous DNS/proxy settings restored." if ok else f"Restore had issues. DNS: {dns_msg}; Proxy: {proxy_msg}"
            return ok, msg

        def _done(result):
            ok, msg = result
            self.show_toast("Success" if ok else "Error", msg)
            self._record_event("settings.restore", msg, {"ok": ok, "snapshot": snapshot})
            self._refresh_proxy_status()

        self._run_task("Restoring settings", _work, _done, key="restore")

    def force_update_ddns(self):
        def _work():
            url = core.get_ddns_update_url(self.config)
            valid, normalized_or_error = core.validate_http_url(url, required=True)
            if not valid:
                return False, normalized_or_error
            if self.monitor:
                return self.monitor.force_ddns_sync()
            return core.update_ddns(normalized_or_error)

        def _done(result):
            success, msg = result
            self.show_toast("Success" if success else "Error", msg)
            self._refresh_history()

        self._run_task("Syncing DDNS", _work, _done, key="ddns")

    def flush_dns(self):
        def _done(result):
            success, msg = result
            self.show_toast("Success" if success else "Error", msg)
            self._record_event("dns.flush", msg, {"ok": success})

        self._run_task("Flushing DNS cache", core.flush_dns_cache, _done, key="dns_tools")

    def renew_dhcp(self):
        def _done(result):
            success, msg = result
            self.show_toast("Success" if success else "Notice", msg)
            self._record_event("dhcp.renew", msg, {"ok": success})

        self._run_task("Renewing DHCP", core.renew_dhcp, _done, key="dhcp")

    def save_settings(self):
        try:
            interval = max(15, min(86400, int(self.interval_var.get().strip())))
        except ValueError:
            self.show_toast("Error", "Interval must be a number of seconds.")
            return
        with self._config_lock:
            if not isinstance(self.config.get("settings"), dict):
                self.config["settings"] = {}
            auto_ddns = self.auto_ddns_var.get()
            if auto_ddns and not core.get_ddns_update_url(self.config):
                auto_ddns = False
                self.auto_ddns_var.set(False)
                self.show_toast("Notice", "Auto-DDNS was disabled because no update URL is configured.")
            self.config["settings"]["auto_update_ddns"] = auto_ddns
            self.config["settings"]["check_interval_seconds"] = interval
            self.config["settings"]["minimize_to_tray_on_close"] = self.tray_close_var.get()
            cfg = copy.deepcopy(self.config)
        try:
            core.save_config(cfg, self.config_path)
            if self.monitor:
                self.monitor.update_config(cfg)
            self.show_toast("Success", "Settings saved.")
            self._record_event("settings.saved", "Settings saved", {"interval": interval})
        except OSError as e:
            self.show_toast("Error", str(e))

    def copy_diagnostics(self):
        text = diagnostics.copyable_diagnostics(self.config, self.monitor.snapshot() if self.monitor else None)
        self.clipboard_clear()
        self.clipboard_append(text)
        self.show_toast("Success", "Diagnostics copied.")

    def export_diagnostics(self):
        def _work():
            return diagnostics.export_bundle(self.config, self.monitor.snapshot() if self.monitor else None)

        def _done(path):
            self.show_toast("Success", f"Diagnostics exported: {path}")

        self._run_task("Exporting diagnostics", _work, _done, key="diagnostics")

    def _open_folder(self, path):
        os.makedirs(path, exist_ok=True)
        try:
            subprocess.Popen(["explorer", path])
        except OSError as exc:
            self.show_toast("Error", str(exc))

    def _open_doc(self, filename):
        path = core.resource_path("docs", filename)
        if not os.path.isfile(path):
            self.show_toast("Error", f"Missing document: {filename}")
            return
        try:
            os.startfile(path)
        except OSError as exc:
            self.show_toast("Error", str(exc))

    def show_toast(self, title, msg):
        color = COLORS["success"] if title == "Success" else COLORS["warning"] if title == "Notice" else COLORS["error"]
        toast = ctk.CTkFrame(self.toast_frame, fg_color=color, corner_radius=8)
        toast.pack(side="top", anchor="e", pady=2)
        ctk.CTkLabel(toast, text=f"{title}: {msg}", text_color="white", font=ctk.CTkFont(size=12), wraplength=360).pack(
            padx=10, pady=6
        )
        def _destroy_toast():
            try:
                if toast.winfo_exists():
                    toast.destroy()
            except tk.TclError:
                pass

        self.after(4500, _destroy_toast)

    def _run_task(self, label, work, on_done=None, key=None):
        task_key = key or label
        if task_key in self._running_task_keys:
            self.show_toast("Notice", f"{label} is already running.")
            return
        self._running_task_keys.add(task_key)
        self._set_activity(label)

        def _worker():
            try:
                result = work()
                error = None
            except Exception as exc:
                core.logger().warning("ui_task_failed label=%s error=%s", label, exc, exc_info=True)
                result = None
                error = exc

            def _finish():
                try:
                    self._clear_activity()
                    if error:
                        self.show_toast("Error", str(error))
                        return
                    if on_done:
                        try:
                            on_done(result)
                        except Exception as exc:
                            core.logger().warning("ui_task_done_failed label=%s error=%s", label, exc, exc_info=True)
                            self.show_toast("Error", f"{label} finished but UI update failed: {exc}")
                finally:
                    self._running_task_keys.discard(task_key)

            if self._alive:
                self.after(0, _finish)
            else:
                self._running_task_keys.discard(task_key)

        threading.Thread(target=_worker, name=f"UIAction-{label}", daemon=True).start()

    def _set_activity(self, label):
        self._busy_count += 1
        if hasattr(self, "activity_label"):
            self.activity_label.configure(text=f"{label}...")

    def _clear_activity(self):
        self._busy_count = max(0, self._busy_count - 1)
        if hasattr(self, "activity_label") and self._busy_count == 0:
            self.activity_label.configure(text="Ready")

    def on_closing(self):
        with self._config_lock:
            minimize = core.parse_bool((self.config.get("settings") or {}).get("minimize_to_tray_on_close", True), True)
        if minimize:
            self.withdraw()
            self.on_close_callback()
            return
        self._alive = False
        if self.monitor:
            self.monitor.stop()
        self.quit()
