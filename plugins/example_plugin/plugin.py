import customtkinter as ctk


def on_start(api):
    api.emit_event("started", "Example plugin started")
    api.register_periodic_task("heartbeat", 300, _heartbeat)


def register_ui(api):
    def build(parent):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=16, pady=16)
        ctk.CTkLabel(frame, text="Example Plugin", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w")
        state_label = ctk.CTkLabel(frame, text="No snapshot yet.", justify="left")
        state_label.pack(anchor="w", pady=(12, 8))

        def refresh():
            state = api.network_state()
            if state:
                state_label.configure(
                    text=(
                        f"Interface: {state.interface or 'Unknown'}\n"
                        f"Public IP: {state.public_ip or 'Unavailable'}\n"
                        f"Proxy: {'on' if state.proxy_enabled else 'off'}"
                    )
                )
            api.emit_event("ui_refresh", "Example plugin UI refreshed")

        ctk.CTkButton(frame, text="Refresh snapshot", command=refresh).pack(anchor="w")
        refresh()

    api.register_tab("Example Plugin", build)


def _heartbeat(api):
    state = api.network_state()
    api.emit_event("heartbeat", "Example scheduled task ran", {"public_ip": getattr(state, "public_ip", None)})
