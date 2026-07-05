"""Two-path authentication screen."""
from __future__ import annotations

import threading
import webbrowser
import customtkinter as ctk

from core.errors import translate
from core.device_token_backend import DeviceTokenBackend
from core.rest_v1_backend import RestV1Backend
from ui.theme import *
from ui.widgets import GlowFrame, NeonButton, Tooltip


class LoginView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=BG_DEEP)
        self.app = app
        card = GlowFrame(self, width=560)
        card.pack(expand=True, padx=30, pady=30)
        ctk.CTkLabel(card, text="SIGN IN", font=(FONT, 28, "bold"), text_color=ACCENT).pack(pady=(28, 4))
        ctk.CTkLabel(card, text="Sign in to your Seedr account to start downloading.",
                     text_color=TEXT_MUTED).pack(pady=(0, 16))
        tabs = ctk.CTkTabview(card, fg_color=BG_PANEL, segmented_button_selected_color=ACCENT_DIM)
        tabs.pack(fill="both", expand=True, padx=26, pady=(0, 26))
        self._email_tab(tabs.add("Email + Password"))
        self._device_tab(tabs.add("Device Code"))

    def _email_tab(self, tab) -> None:
        ctk.CTkLabel(tab, text="Use the same email and password you use at seedr.cc.",
                     text_color=TEXT_MUTED).pack(pady=(18, 10))
        self.email = ctk.CTkEntry(tab, placeholder_text="Email address", width=390)
        self.email.pack(pady=7)
        self.password = ctk.CTkEntry(tab, placeholder_text="Password", show="*", width=390)
        self.password.pack(pady=7)
        self.remember = ctk.CTkCheckBox(tab, text="Remember me on this PC", border_color=ACCENT_DIM)
        self.remember.pack(pady=8)
        button = NeonButton(tab, text="Sign in", width=220, command=self._sign_in)
        button.pack(pady=(8, 18))
        Tooltip(button, "Connect securely using your Seedr email and password")

    def _device_tab(self, tab) -> None:
        guide = ("1. Click Generate code below.\n2. Open seedr.cc/devices in your browser.\n"
                 "3. Paste the code and authorize.\nSeedrFetch will detect authorization automatically.")
        ctk.CTkLabel(tab, text=guide, justify="left", text_color=TEXT_MUTED).pack(pady=(18, 10))
        self.code = ctk.CTkLabel(tab, text="------", font=(MONO, 26, "bold"), text_color=ACCENT)
        self.code.pack(pady=10)
        NeonButton(tab, text="Generate code", command=self._generate_code).pack(pady=6)
        ctk.CTkButton(tab, text="Open seedr.cc/devices", fg_color="transparent", text_color=ACCENT,
                      command=lambda: webbrowser.open("https://www.seedr.cc/devices")).pack(pady=(4, 18))

    def _sign_in(self) -> None:
        email, password = self.email.get().strip(), self.password.get()
        if not email or not password:
            self.app.toast("Enter both your email and password.", True)
            return
        self.app.run_worker(self._authenticate, email, password)

    def _authenticate(self, email: str, password: str) -> None:
        try:
            backend = RestV1Backend(email, password, self.app.config.data)
            backend.user_info()
            if self.remember.get():
                self.app.config.remember_credentials(email, password)
            self.app.post(self.app.logged_in, backend, email)
        except Exception as exc:
            self.app.logger.exception("Sign-in failed")
            self.app.post(self.app.toast, translate(exc), True)

    def _generate_code(self) -> None:
        self.app.run_worker(self._device_worker)

    def _device_worker(self) -> None:
        try:
            backend, data = DeviceTokenBackend.generate_code()
            code = data.get("user_code") or data.get("code") or "See browser"
            self.app.post(self.code.configure, text=code)
            token = backend.poll_authorization()
            if token:
                self.app.config.set("device_token", token)
                self.app.config.set("auth_method", "device")
                self.app.post(self.app.logged_in, backend, "Device")
        except Exception as exc:
            self.app.logger.exception("Device authorization failed")
            self.app.post(self.app.toast, translate(exc), True)
