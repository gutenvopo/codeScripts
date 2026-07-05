"""Header view."""

from __future__ import annotations

import customtkinter as ctk


class Header(ctk.CTkFrame):
    """Application header with title and theme menu."""

    def __init__(self, master: ctk.CTkBaseClass, on_theme_change) -> None:
        super().__init__(master, corner_radius=10)
        self.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            self,
            text="Student Data Extractor",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        self.title_label.grid(row=0, column=0, sticky="w", padx=16, pady=14)

        self.theme_menu = ctk.CTkOptionMenu(
            self,
            values=["System", "Dark", "Light"],
            command=on_theme_change,
            width=120,
        )
        self.theme_menu.grid(row=0, column=1, sticky="e", padx=16, pady=14)

    def set_theme(self, value: str) -> None:
        """Select the displayed theme value."""

        self.theme_menu.set(value)
