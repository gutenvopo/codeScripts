"""Four-slide first-run walkthrough."""
from __future__ import annotations

import customtkinter as ctk
from ui.theme import *
from ui.widgets import NeonButton

SLIDES = [
    ("Welcome to SeedrFetch", "Paste a torrent or magnet link. Seedr's servers download it to the cloud, then you pull the finished files down to your PC."),
    ("Sign in", "Use email + password for the simplest route, or Device Code so no password is stored. Switch between tabs on the login screen."),
    ("How to download", "1. Paste a magnet or torrent link and choose Add to Seedr.\n2. Wait for the Active Transfers panel.\n3. Right-click a finished file or folder and choose Download here.\n4. Files save to the destination shown in the dashboard."),
    ("If something doesn't work", "Norton, Kaspersky, corporate firewalls, and some VPNs inspect HTTPS. SeedrFetch usually handles this automatically. For connection errors, open Settings > Run Diagnostics for the cause and fix."),
]


class Onboarding(ctk.CTkToplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app, self.index = app, 0
        self.title("Welcome to SeedrFetch")
        self.geometry("720x500")
        self.configure(fg_color=BG_DEEP)
        self.transient(app)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.finish)
        self.art = ctk.CTkFrame(self, height=150, fg_color=BG_PANEL, corner_radius=16)
        self.art.pack(fill="x", padx=45, pady=(40, 20))
        self.heading = ctk.CTkLabel(self, font=(FONT, 28, "bold"), text_color=ACCENT)
        self.heading.pack(pady=8)
        self.body = ctk.CTkLabel(self, wraplength=600, justify="left", text_color=TEXT_PRIMARY)
        self.body.pack(padx=50, pady=8)
        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.pack(side="bottom", fill="x", padx=45, pady=35)
        ctk.CTkButton(nav, text="Skip", fg_color="transparent", text_color=TEXT_MUTED,
                      command=self.finish).pack(side="left")
        self.back = ctk.CTkButton(nav, text="Back", fg_color=BG_ELEVATED, command=self.previous)
        self.back.pack(side="right", padx=6)
        self.next = NeonButton(nav, text="Next", command=self.advance)
        self.next.pack(side="right", padx=6)
        self.render()

    def render(self) -> None:
        for child in self.art.winfo_children(): child.destroy()
        title, text = SLIDES[self.index]
        self.heading.configure(text=title)
        self.body.configure(text=text)
        self.back.configure(state="disabled" if self.index == 0 else "normal")
        self.next.configure(text="Got it, let's go" if self.index == 3 else "Next")
        for offset, color in ((0, ACCENT_DIM), (1, ACCENT_2), (2, BORDER)):
            ctk.CTkFrame(self.art, width=150 - offset * 25, height=12,
                         fg_color=color, corner_radius=6).place(relx=.5, rely=.35 + offset * .15, anchor="center")
        if self.index == 3:
            ctk.CTkButton(self.art, text="Open Settings now", fg_color="transparent",
                          text_color=ACCENT, command=self.open_settings).place(relx=.5, rely=.85, anchor="center")

    def previous(self) -> None:
        self.index -= 1; self.render()

    def advance(self) -> None:
        if self.index == 3: self.finish()
        else: self.index += 1; self.render()

    def open_settings(self) -> None:
        self.finish(); self.app.show_view("settings")

    def finish(self) -> None:
        self.app.config.set("onboarded", True)
        self.grab_release(); self.destroy()
