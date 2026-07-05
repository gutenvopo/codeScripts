"""Discoverable in-app help."""
from __future__ import annotations

import customtkinter as ctk
from ui.theme import *
from ui.widgets import GlowFrame, NeonButton

SECTIONS = {
    "Getting Started": "Paste a magnet or torrent URL, let Seedr fetch it in the cloud, then right-click the finished file or folder to download it to your PC.",
    "Adding torrents": "Paste magnet:?xt=urn:btih:... or an https://.../file.torrent URL in the top bar, then choose Add to Seedr.",
    "Downloading files and folders": "Wait for the cloud transfer to finish. Right-click an item in the browser and choose Download here. Folder downloads arrive as ZIP files.",
    "Changing your download location": "Use Change beside the destination on the dashboard, or open Settings > Download destination.",
    "Managing storage": "The footer shows account usage. Right-click files, folders, or active torrents to delete them after confirmation.",
    "Switching auth methods": "Sign out in Settings, then sign in again using the other tab.",
    "Troubleshooting": "I can't sign in: verify your credentials, try Device Code, then run Diagnostics.\n\nConnection / SSL errors: antivirus and corporate tools can inspect HTTPS. SeedrFetch uses the Windows certificate store automatically. If that is not enough, open Settings > SSL & Network and select a custom CA bundle, or add an exception for *.seedr.cc in HTTPS scanning. Disabling verification is insecure and should only confirm the diagnosis.\n\nSlow or stalled downloads: Norton can reset TLS handshakes; add the HTTPS-scanning exception.\n\nLogs: ~/.seedrfetch/seedrfetch.log",
    "Keyboard shortcuts": "Ctrl+L focuses the link field. F5 refreshes the drive. Ctrl+, opens Settings. F1 opens Help.",
    "About": "SeedrFetch 1.0.0 - a desktop client for Seedr Premium. SeedrFetch is an independent client.",
}


class HelpView(ctk.CTkScrollableFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=BG_DEEP)
        ctk.CTkLabel(self, text="HELP", font=(FONT, 28, "bold"), text_color=ACCENT).pack(anchor="w", padx=24, pady=(24, 12))
        for title, body in SECTIONS.items():
            CollapsibleCard(self, title, body, expanded=title != "Troubleshooting").pack(fill="x", padx=24, pady=5)
        NeonButton(self, text="Show walkthrough again", command=app.show_onboarding).pack(anchor="w", padx=24, pady=20)


class CollapsibleCard(GlowFrame):
    def __init__(self, master, title: str, body: str, expanded: bool = True):
        super().__init__(master)
        self.body = ctk.CTkLabel(self, text=body, justify="left", anchor="w", wraplength=850,
                                 text_color=TEXT_MUTED)
        self.button = ctk.CTkButton(self, text=("-  " if expanded else "+  ") + title,
                                    anchor="w", fg_color="transparent", hover_color=BG_ELEVATED,
                                    font=(FONT, 15, "bold"), command=self.toggle)
        self.button.pack(fill="x", padx=10, pady=5)
        if expanded:
            self.body.pack(fill="x", padx=18, pady=(0, 14))

    def toggle(self) -> None:
        if self.body.winfo_manager():
            self.body.pack_forget()
            self.button.configure(text="+  " + self.button.cget("text")[3:])
        else:
            self.body.pack(fill="x", padx=18, pady=(0, 14))
            self.button.configure(text="-  " + self.button.cget("text")[3:])
