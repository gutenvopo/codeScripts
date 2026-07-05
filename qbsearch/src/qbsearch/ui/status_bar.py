from __future__ import annotations

import customtkinter as ctk

from qbsearch.ui import theme


class StatusBar(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkBaseClass) -> None:
        super().__init__(master, height=28, fg_color=theme.PANEL, corner_radius=0)
        self.grid_columnconfigure(1, weight=1)
        self.connection = ctk.CTkLabel(self, text="● Disconnected", text_color=theme.DANGER)
        self.status = ctk.CTkLabel(self, text="Ready", text_color=theme.MUTED)
        self.progress = ctk.CTkProgressBar(self, width=160, mode="indeterminate")
        self.connection.grid(row=0, column=0, padx=12, sticky="w")
        self.status.grid(row=0, column=1, padx=12)
        self.progress.grid(row=0, column=2, padx=12)
        self.progress.stop()
        self.progress.set(0)

    def set_connected(self, text: str, connected: bool) -> None:
        color = theme.SUCCESS if connected else theme.DANGER
        prefix = "●" if connected else "●"
        self.connection.configure(text=f"{prefix} {text}", text_color=color)

    def set_status(self, text: str) -> None:
        self.status.configure(text=text)

    def set_running(self, running: bool) -> None:
        if running:
            self.progress.start()
        else:
            self.progress.stop()
            self.progress.set(1)
