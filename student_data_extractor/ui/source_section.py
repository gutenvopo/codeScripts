"""Folder selection view."""

from __future__ import annotations

import customtkinter as ctk


class SourceSection(ctk.CTkFrame):
    """Source folder picker and validation banner."""

    def __init__(self, master: ctk.CTkBaseClass, on_select) -> None:
        super().__init__(master, corner_radius=10)
        self.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self,
            text="Source",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(14, 6))

        self.select_button = ctk.CTkButton(self, text="📁 Select Folder", command=on_select)
        self.select_button.grid(row=1, column=0, sticky="w", padx=(16, 10), pady=(0, 8))

        self.path_var = ctk.StringVar()
        self.path_entry = ctk.CTkEntry(self, textvariable=self.path_var, state="readonly")
        self.path_entry.grid(row=1, column=1, sticky="ew", padx=(0, 16), pady=(0, 8))

        self.error_label = ctk.CTkLabel(self, text="", text_color="#d97706")
        self.error_label.grid(row=2, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 12))

    def set_path(self, value: str) -> None:
        """Display selected path."""

        self.path_var.set(value)

    def set_error(self, value: str) -> None:
        """Display inline validation feedback."""

        self.error_label.configure(text=value)

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable folder controls."""

        state = "normal" if enabled else "disabled"
        self.select_button.configure(state=state)
