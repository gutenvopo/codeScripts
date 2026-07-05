"""Application root, persistent navigation, and thread result queue."""
from __future__ import annotations

import logging
import contextvars
import queue
import threading
import customtkinter as ctk

from core.config import Config
from core.device_token_backend import DeviceTokenBackend
from core.errors import translate
from core.rest_v1_backend import RestV1Backend
from core.logging_setup import log_operation, set_log_level
from ui.dashboard_view import DashboardView
from ui.help_view import HelpView
from ui.login_view import LoginView
from ui.onboarding import Onboarding
from ui.settings_view import SettingsView
from ui.theme import *
from ui.widgets import InfoBanner, Toast, Tooltip


class App(ctk.CTk):
    def __init__(self, config: Config, logger: logging.Logger):
        super().__init__()
        self.config, self.logger = config, logger
        set_log_level(config.get("log_level", "DEBUG"))
        self.report_callback_exception = self._report_callback_exception
        self.backend, self.identity = None, ""
        self.messages: queue.Queue = queue.Queue()
        self.last_diagnostics = []
        self.title("SeedrFetch"); self.geometry("1180x760"); self.minsize(920, 620)
        self.configure(fg_color=BG_DEEP)
        ctk.set_appearance_mode("dark")
        self._navigation()
        self.container = ctk.CTkFrame(self, fg_color=BG_DEEP); self.container.pack(fill="both", expand=True)
        self.security_banner = None
        self.refresh_security_banner()
        self.after(100, self.drain)
        self.bind("<F1>", lambda _e: self.show_view("help")); self.bind("<Control-comma>", lambda _e: self.show_view("settings"))
        self._restore_session()
        if not config.get("onboarded"): self.after(350, self.show_onboarding)

    def _navigation(self) -> None:
        bar = ctk.CTkFrame(self, height=56, fg_color=BG_PANEL, corner_radius=0); bar.pack(fill="x")
        ctk.CTkLabel(bar, text="SEEDRFETCH", font=(FONT, 20, "bold"), text_color=ACCENT).pack(side="left", padx=20, pady=14)
        self.avatar = ctk.CTkLabel(bar, text="S", width=34, height=34, fg_color=BG_ELEVATED, corner_radius=17, text_color=ACCENT_2)
        self.avatar.pack(side="right", padx=(5, 18))
        exit_button = ctk.CTkButton(bar, text="EXIT", width=54, fg_color=DANGER,
                                    hover_color=BG_DANGER, command=self.destroy)
        exit_button.pack(side="right", padx=4)
        settings = ctk.CTkButton(bar, text="SET", width=48, fg_color="transparent", text_color=ACCENT, command=lambda: self.show_view("settings"))
        settings.pack(side="right", padx=2)
        help_button = ctk.CTkButton(bar, text="?", width=40, fg_color="transparent", text_color=ACCENT, font=(FONT, 19, "bold"), command=lambda: self.show_view("help"))
        help_button.pack(side="right", padx=2)
        Tooltip(exit_button, "Close SeedrFetch")
        Tooltip(settings, "Settings and network diagnostics"); Tooltip(help_button, "Help and getting started")

    def _restore_session(self) -> None:
        try:
            if self.config.get("auth_method") == "rest" and self.config.credentials():
                email, password = self.config.credentials()
                self.backend = RestV1Backend(email, password, self.config.data); self.identity = email
                self.show_view("dashboard"); return
            if self.config.get("auth_method") == "device" and self.config.get("device_token"):
                self.backend = DeviceTokenBackend(self.config.get("device_token"), settings=self.config.data)
                self.identity = "Signed in via device code"; self.show_view("dashboard"); return
        except Exception: self.logger.exception("Could not restore session")
        self.show_view("login")

    def show_view(self, name: str) -> None:
        for child in self.container.winfo_children(): child.destroy()
        cls = {"login": LoginView, "dashboard": DashboardView, "help": HelpView, "settings": SettingsView}[name]
        cls(self.container, self).pack(fill="both", expand=True)

    def logged_in(self, backend, identity: str) -> None:
        self.backend, self.identity = backend, identity
        self.avatar.configure(text=(identity[:1] or "S").upper()); self.show_view("dashboard")

    def sign_out(self) -> None:
        self.config.sign_out(); self.backend = None; self.identity = ""; self.avatar.configure(text="S"); self.show_view("login")

    def run_worker(self, function, *args) -> None:
        def tracked() -> None:
            with log_operation(function.__name__.strip("_").replace("_worker", "")):
                function(*args)
        context = contextvars.copy_context()
        threading.Thread(target=context.run, args=(tracked,), daemon=True).start()

    def post(self, function, *args, **kwargs) -> None:
        self.messages.put((function, args, kwargs))

    def drain(self) -> None:
        try:
            while True:
                function, args, kwargs = self.messages.get_nowait(); function(*args, **kwargs)
        except queue.Empty: pass
        self.after(100, self.drain)

    def toast(self, message, danger: bool = False, duration: int = 5000) -> None:
        Toast(self, message, danger, duration)

    def _report_callback_exception(self, exc_type, exc, tb) -> None:
        logging.getLogger("ui").error("Tk callback exception", exc_info=(exc_type, exc, tb))
        try:
            user_error = translate(exc)
            self.toast(user_error.title, True)
        except Exception:
            self.toast("Something went wrong - check the logs.", True)

    def refresh_security_banner(self) -> None:
        if self.security_banner and self.security_banner.winfo_exists(): self.security_banner.destroy()
        self.security_banner = None
        if self.config.get("disable_ssl_verify"):
            self.security_banner = InfoBanner(self, "WARNING: SSL verification is disabled. Your connection is not protected.", danger=True)
            self.security_banner.pack(fill="x", before=self.container if hasattr(self, "container") else None)

    def show_onboarding(self) -> None:
        Onboarding(self)
