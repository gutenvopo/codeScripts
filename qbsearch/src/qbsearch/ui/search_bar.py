from __future__ import annotations

import customtkinter as ctk

from qbsearch.ui import theme

CATEGORIES = [
    "All",
    "Movies",
    "TV",
    "Music",
    "Games",
    "Software",
    "Books",
    "Anime",
    "Pictures",
    "Other",
]


class SearchBar(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkBaseClass, on_search, on_stop, on_settings) -> None:
        super().__init__(master, fg_color=theme.PANEL, height=64, corner_radius=0)
        self.grid_columnconfigure(0, weight=1)
        self.entry = ctk.CTkEntry(
            self,
            placeholder_text="Search torrents...",
            height=40,
            font=(theme.FONT, 14),
        )
        self.regex_var = ctk.BooleanVar(value=False)
        self.category_var = ctk.StringVar(value="All")
        self.regex = ctk.CTkSwitch(self, text="Regex", variable=self.regex_var)
        self.category = ctk.CTkOptionMenu(self, values=CATEGORIES, variable=self.category_var)
        self.search_button = ctk.CTkButton(
            self, text="Search", fg_color=theme.ACCENT, command=on_search
        )
        self.stop_button = ctk.CTkButton(
            self, text="Stop", fg_color=theme.ELEVATED, command=on_stop
        )
        self.settings_button = ctk.CTkButton(self, text="⚙", width=44, command=on_settings)

        self.entry.grid(row=0, column=0, padx=(16, 10), pady=12, sticky="ew")
        self.regex.grid(row=0, column=1, padx=8)
        self.category.grid(row=0, column=2, padx=8)
        self.search_button.grid(row=0, column=3, padx=8)
        self.stop_button.grid(row=0, column=4, padx=8)
        self.settings_button.grid(row=0, column=5, padx=(8, 16))
        self.stop_button.grid_remove()

    def set_running(self, running: bool) -> None:
        self.search_button.configure(state="disabled" if running else "normal")
        if running:
            self.stop_button.grid()
        else:
            self.stop_button.grid_remove()

    def query(self) -> str:
        return self.entry.get().strip()

    def category_value(self) -> str:
        value = self.category_var.get().lower()
        return "all" if value == "all" else value
