import customtkinter as ctk
import tkinter.messagebox as messagebox
import threading
import time
import core

# Set the modern theme
ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class NetworkManagerGUI(ctk.CTk):
    def __init__(self, config, on_close_callback):
        super().__init__()
        self.config = config
        self.on_close_callback = on_close_callback
        
        self.title("Network & DNS Manager Pro")
        self.geometry("450x620")
        self.resizable(False, False)
        
        # Intercept the 'X' button to minimize to tray instead of closing
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.setup_ui()
        
        # Background thread for live Ping and IP updates
        self.update_status_thread = threading.Thread(target=self.status_loop, daemon=True)
        self.update_status_thread.start()

    def setup_ui(self):
        title_font = ctk.CTkFont(size=18, weight="bold")
        label_font = ctk.CTkFont(size=14)

        # --- DNS Section ---
        dns_frame = ctk.CTkFrame(self)
        dns_frame.pack(pady=15, padx=20, fill="x")
        
        ctk.CTkLabel(dns_frame, text="DNS Profiles", font=title_font).pack(pady=(10, 5))
        
        self.dns_var = ctk.StringVar(value="Shecan")
        dns_profiles = list(self.config.get("dns_profiles", {}).keys())
        self.dns_dropdown = ctk.CTkOptionMenu(dns_frame, variable=self.dns_var, values=dns_profiles)
        self.dns_dropdown.pack(pady=10)
        
        btn_frame_dns = ctk.CTkFrame(dns_frame, fg_color="transparent")
        btn_frame_dns.pack(pady=5)
        
        ctk.CTkButton(btn_frame_dns, text="Apply DNS", width=140, command=self.apply_dns).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame_dns, text="Set to Auto", width=140, command=self.clear_dns, fg_color="gray").pack(side="right", padx=5)
        
        self.ping_label = ctk.CTkLabel(dns_frame, text="Ping: Checking...", text_color="gray")
        self.ping_label.pack(pady=(5, 10))

        # --- Proxy Section ---
        proxy_frame = ctk.CTkFrame(self)
        proxy_frame.pack(pady=15, padx=20, fill="x")
        
        ctk.CTkLabel(proxy_frame, text="System Proxy", font=title_font).pack(pady=(10, 5))
        
        proxy_profiles = self.config.get("proxy_profiles", ["127.0.0.1:8080"])
        self.proxy_var = ctk.StringVar(value=proxy_profiles[0])
        self.proxy_dropdown = ctk.CTkOptionMenu(proxy_frame, variable=self.proxy_var, values=proxy_profiles)
        self.proxy_dropdown.pack(pady=10)

        btn_frame_proxy = ctk.CTkFrame(proxy_frame, fg_color="transparent")
        btn_frame_proxy.pack(pady=5)
        
        ctk.CTkButton(btn_frame_proxy, text="Enable Proxy", width=140, command=self.enable_proxy, fg_color="#2FA572", hover_color="#106A43").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame_proxy, text="Disable Proxy", width=140, command=self.disable_proxy, fg_color="#E74C3C", hover_color="#C0392B").pack(side="right", padx=5)
        ctk.CTkLabel(proxy_frame, text="").pack(pady=2) # Spacing

        # --- DDNS Section ---
        ddns_frame = ctk.CTkFrame(self)
        ddns_frame.pack(pady=15, padx=20, fill="x")
        
        ctk.CTkLabel(ddns_frame, text="Shecan Pro DDNS", font=title_font).pack(pady=(10, 5))
        
        self.ip_label = ctk.CTkLabel(ddns_frame, text="Public IP: Checking...", font=label_font)
        self.ip_label.pack(pady=5)

        ctk.CTkButton(ddns_frame, text="Force Sync DDNS", command=self.force_update_ddns).pack(pady=(5, 15))

    # --- Actions ---
    def apply_dns(self):
        profile = self.dns_var.get()
        ips = self.config["dns_profiles"][profile]
        success, msg = core.set_dns(ips)
        self.show_toast("Success" if success else "Error", msg)

    def clear_dns(self):
        success, msg = core.clear_dns()
        self.show_toast("Success" if success else "Error", msg)

    def enable_proxy(self):
        proxy = self.proxy_var.get()
        success, msg = core.set_proxy(True, proxy)
        self.show_toast("Success" if success else "Error", msg)

    def disable_proxy(self):
        success, msg = core.set_proxy(False)
        self.show_toast("Success" if success else "Error", msg)

    def force_update_ddns(self):
        url = self.config.get("shecan_update_url")
        success, msg = core.update_ddns(url)
        self.show_toast("Success" if success else "Error", msg)

    # --- Background Loop ---
    def status_loop(self):
        while True:
            # Update IP
            ip = core.get_public_ip()
            ip_text = f"Public IP: {ip}" if ip else "Public IP: Offline"
            
            # Update Ping
            profile = self.dns_var.get()
            primary_dns = self.config["dns_profiles"][profile][0]
            ping_res = core.measure_latency(primary_dns)
            ping_text = f"Ping ({profile}): {ping_res}"

            # Safely update GUI
            self.after(0, self.update_labels, ip_text, ping_text)
            time.sleep(5)

    def update_labels(self, ip_text, ping_text):
        self.ip_label.configure(text=ip_text)
        self.ping_label.configure(text=ping_text)

    def show_toast(self, title, msg):
        if title == "Success":
            messagebox.showinfo(title, msg)
        else:
            messagebox.showerror(title, msg)

    def on_closing(self):
        self.withdraw()  # Hide the window
        self.on_close_callback()