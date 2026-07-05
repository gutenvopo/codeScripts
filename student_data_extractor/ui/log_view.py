"""Live log view."""

from __future__ import annotations

import customtkinter as ctk


class LogView(ctk.CTkFrame):
    """Scrollable live log textbox."""

    COLORS = {
        "info": "#22c55e",
        "warning": "#f59e0b",
        "error": "#ef4444",
    }

    def __init__(self, master: ctk.CTkBaseClass) -> None:
        super().__init__(master, corner_radius=10)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            self,
            text="Live Log",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 6))

        self.textbox = ctk.CTkTextbox(self, height=160)
        self.textbox.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        for tag, color in self.COLORS.items():
            self.textbox.tag_config(tag, foreground=color)
        self.textbox.configure(state="disabled")

    def append(self, message: str, level: str = "info") -> None:
        """Append a color-coded log line."""

        self.textbox.configure(state="normal")
        self.textbox.insert("end", f"{message}\n", level)
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

    def clear(self) -> None:
        """Clear all log lines."""

        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.configure(state="disabled")
