from __future__ import annotations

import customtkinter as ctk

from qbsearch.ui import theme


class EnginePanel(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkBaseClass) -> None:
        super().__init__(master, width=220, fg_color=theme.PANEL, corner_radius=0)
        self.grid_propagate(False)
        self.vars: dict[str, ctk.BooleanVar] = {}
        self.header = ctk.CTkLabel(self, text="Search Engines", font=(theme.FONT, 14, "bold"))
        self.header.pack(anchor="w", padx=14, pady=(14, 4))
        links = ctk.CTkFrame(self, fg_color="transparent")
        links.pack(fill="x", padx=12, pady=(0, 8))
        ctk.CTkButton(links, text="Select all", width=82, command=self.select_all).pack(side="left")
        ctk.CTkButton(
            links, text="None", width=64, fg_color=theme.ELEVATED, command=self.select_none
        ).pack(
            side="left",
            padx=8,
        )
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=8, pady=(0, 12))

    def set_plugins(self, plugins: list[dict[str, object]]) -> None:
        for child in self.scroll.winfo_children():
            child.destroy()
        self.vars.clear()
        for plugin in plugins:
            name = str(plugin.get("name") or plugin.get("fullName") or "")
            if not name:
                continue
            enabled = bool(plugin.get("enabled", True))
            var = ctk.BooleanVar(value=enabled)
            self.vars[name] = var
            row = ctk.CTkFrame(self.scroll, fg_color="transparent")
            row.pack(fill="x", pady=4)
            box = ctk.CTkCheckBox(
                row, text=name, variable=var, state="normal" if enabled else "disabled"
            )
            box.pack(anchor="w")
            url = str(plugin.get("url") or "")
            ctk.CTkLabel(row, text=url, text_color=theme.MUTED, font=(theme.FONT, 9)).pack(
                anchor="w", padx=26
            )

    def selected_plugins(self) -> str:
        selected = [name for name, var in self.vars.items() if var.get()]
        return ",".join(selected) if selected else "enabled"

    def select_all(self) -> None:
        for var in self.vars.values():
            var.set(True)

    def select_none(self) -> None:
        for var in self.vars.values():
            var.set(False)
