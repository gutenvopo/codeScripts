"""Action buttons view."""

from __future__ import annotations

import customtkinter as ctk


class ActionBar(ctk.CTkFrame):
    """Start and cancel buttons."""

    def __init__(self, master: ctk.CTkBaseClass, on_start, on_cancel) -> None:
        super().__init__(master, fg_color="transparent")
        self.start_button = ctk.CTkButton(
            self,
            text="▶ Start Extraction",
            command=on_start,
            height=40,
            font=ctk.CTkFont(weight="bold"),
        )
        self.start_button.grid(row=0, column=0, padx=(0, 10), pady=6)

        self.cancel_button = ctk.CTkButton(
            self,
            text="⏹ Cancel",
            command=on_cancel,
            height=40,
            fg_color="#6b7280",
            hover_color="#4b5563",
            state="disabled",
        )
        self.cancel_button.grid(row=0, column=1, padx=0, pady=6)

    def set_running(self, running: bool) -> None:
        """Update action states."""

        self.start_button.configure(state="disabled" if running else "normal")
        self.cancel_button.configure(state="normal" if running else "disabled")
