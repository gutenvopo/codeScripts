from __future__ import annotations

import threading

import customtkinter as ctk

from qbsearch.api.qbittorrent import QbtClient
from qbsearch.config import AppSettings, save_password, save_settings
from qbsearch.ui import theme


class SettingsDialog(ctk.CTkToplevel):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        settings: AppSettings,
        password: str,
        on_saved,
        client_factory=QbtClient,
        welcome: bool = False,
    ) -> None:
        super().__init__(master)
        self.title("qbSearch Settings")
        self.geometry("520x560")
        self.transient(master)
        self.grab_set()
        self.settings = settings
        self.on_saved = on_saved
        self.client_factory = client_factory
        self.grid_columnconfigure(1, weight=1)
        title = "Welcome to qbSearch - let's connect to your qBittorrent" if welcome else "Settings"
        ctk.CTkLabel(self, text=title, font=(theme.FONT, 17, "bold")).grid(
            row=0,
            column=0,
            columnspan=2,
            padx=18,
            pady=(18, 14),
            sticky="w",
        )
        self.host = self._entry("Host", settings.host, 1)
        self.port = self._entry("Port", str(settings.port), 2)
        self.username = self._entry("Username", settings.username, 3)
        self.password = self._entry("Password", password, 4, show="•")
        self.save_path = self._entry("Default save path", settings.default_save_path, 5)
        self.category = self._entry("Default category", settings.default_category, 6)
        self.paused = ctk.BooleanVar(value=settings.add_paused_by_default)
        ctk.CTkCheckBox(
            self, text="Open in qBittorrent paused by default", variable=self.paused
        ).grid(
            row=7,
            column=1,
            padx=18,
            pady=8,
            sticky="w",
        )
        self.theme_var = ctk.StringVar(value=settings.theme)
        ctk.CTkLabel(self, text="Theme").grid(row=8, column=0, padx=18, pady=8, sticky="w")
        ctk.CTkOptionMenu(self, values=["System", "Dark", "Light"], variable=self.theme_var).grid(
            row=8,
            column=1,
            padx=18,
            pady=8,
            sticky="ew",
        )
        self.message = ctk.CTkLabel(self, text="", text_color=theme.MUTED)
        self.message.grid(row=9, column=0, columnspan=2, padx=18, pady=8, sticky="w")
        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.grid(row=10, column=0, columnspan=2, padx=18, pady=18, sticky="e")
        ctk.CTkButton(
            buttons, text="Test connection", fg_color=theme.ELEVATED, command=self.test
        ).pack(
            side="left",
            padx=8,
        )
        ctk.CTkButton(buttons, text="Save", command=self.save).pack(side="left")

    def _entry(self, label: str, value: str, row: int, show: str | None = None) -> ctk.CTkEntry:
        ctk.CTkLabel(self, text=label).grid(row=row, column=0, padx=18, pady=8, sticky="w")
        entry = ctk.CTkEntry(self, show=show)
        entry.insert(0, value)
        entry.grid(row=row, column=1, padx=18, pady=8, sticky="ew")
        return entry

    def test(self) -> None:
        self.message.configure(text="Testing connection...", text_color=theme.MUTED)
        threading.Thread(target=self._test_worker, daemon=True).start()

    def _test_worker(self) -> None:
        try:
            client = self.client_factory()
            client.login(
                self.host.get(), int(self.port.get()), self.username.get(), self.password.get()
            )
            plugins = client.list_plugins()
            client.close()
        except Exception as exc:  # noqa: BLE001
            message = str(exc)
            self.after(0, lambda: self.message.configure(text=message, text_color=theme.DANGER))
            return
        self.after(
            0,
            lambda: self.message.configure(
                text=f"Connected. Found {len(plugins)} search plugins.",
                text_color=theme.SUCCESS,
            ),
        )

    def save(self) -> None:
        self.settings.host = self.host.get().strip() or "localhost"
        self.settings.port = int(self.port.get() or "8080")
        self.settings.username = self.username.get().strip() or "admin"
        self.settings.default_save_path = self.save_path.get().strip()
        self.settings.default_category = self.category.get().strip()
        self.settings.add_paused_by_default = self.paused.get()
        self.settings.theme = self.theme_var.get()
        save_settings(self.settings)
        save_password(self.settings, self.password.get())
        self.on_saved(self.settings)
        self.destroy()
