"""Cloud drive, torrent controls, and local download progress."""
from __future__ import annotations

import logging
import os
from pathlib import Path
import subprocess
import sys
from tkinter import TclError, filedialog, messagebox, ttk
import customtkinter as ctk

from core.errors import translate
from core.downloader import Downloader
from core.ssl_setup import make_session
from ui.theme import *
from ui.widgets import GlowFrame, InfoBanner, NeonButton, Tooltip

log = logging.getLogger(__name__)


def _folder_label(folder: dict) -> str:
    name = (folder.get("name") or "").strip()
    if name:
        return name
    fid = folder.get("id") or folder.get("folder_id") or "?"
    log.debug("folder name fallback used for id=%s payload_keys=%s", fid, list(folder.keys()))
    return f"(unnamed folder {fid})"


def _file_label(file: dict) -> str:
    name = (file.get("name") or "").strip()
    if name:
        return name
    fid = file.get("folder_file_id") or file.get("id") or "?"
    log.debug("file name fallback used for id=%s payload_keys=%s", fid, list(file.keys()))
    return f"(unnamed file {fid})"


def _make_iid(kind: str, seedr_id: int) -> str:
    """Stable Treeview iid combining item kind and Seedr id."""
    return "%s:%d" % (kind, seedr_id)


def _item_id(kind: str, item: dict) -> int | None:
    if kind == "file":
        value = item.get("folder_file_id") or item.get("id")
    else:
        value = item.get("id") or item.get("folder_id")
    try:
        return int(value)
    except (TypeError, ValueError):
        log.warning("tree item missing usable id kind=%s keys=%s", kind, list(item.keys()))
        return None


class DownloadRow(GlowFrame):
    def __init__(self, master, job: dict, callbacks: dict[str, object]):
        super().__init__(master)
        self.job_id = str(job["job_id"])
        self.callbacks = callbacks
        self.grid_columnconfigure(1, weight=1)
        self.icon = ctk.CTkLabel(self, text="◇", text_color=ACCENT, width=24)
        self.icon.grid(row=0, column=0, rowspan=2, padx=(10, 6), pady=8)
        self.name = ctk.CTkLabel(self, text="", anchor="w")
        self.name.grid(row=0, column=1, sticky="ew", padx=4, pady=(8, 2))
        self.status = ctk.CTkLabel(self, text="", text_color=TEXT_MUTED, anchor="e")
        self.status.grid(row=0, column=2, sticky="e", padx=8, pady=(8, 2))
        self.bar = ctk.CTkProgressBar(self, progress_color=ACCENT)
        self.bar.grid(row=1, column=1, sticky="ew", padx=4, pady=(2, 8))
        self.actions = ctk.CTkFrame(self, fg_color="transparent")
        self.actions.grid(row=1, column=2, sticky="e", padx=8, pady=(2, 8))
        self.update(job)

    def update(self, job: dict) -> None:
        name = _truncate_middle(str(job.get("suggested_filename") or job.get("display_name") or "download"), 48)
        state = str(job.get("state", "queued")).replace("_", " ").title()
        total = int(job.get("total_bytes") or 0)
        done = int(job.get("bytes") or 0)
        speed = float(job.get("speed") or 0.0)
        self.name.configure(text=name)
        if total:
            ratio = min(done / total, 1)
            status = "%s  %s / %s  %s/s" % (state, DashboardView._size(done),
                                            DashboardView._size(total), DashboardView._size(speed))
        elif state == "Downloading":
            ratio = 0
            status = "%s  %s  %s/s" % (state, DashboardView._size(done), DashboardView._size(speed))
        else:
            ratio = 0
            status = state
        if job.get("error"):
            status = "%s  %s" % (state, _truncate_middle(str(job["error"]), 54))
        self.status.configure(text=status)
        self.bar.set(ratio)
        self._render_actions(job)

    def _render_actions(self, job: dict) -> None:
        for child in self.actions.winfo_children():
            child.destroy()
        state = str(job.get("state", "queued"))
        if state not in {"completed", "failed", "cancelled"}:
            self._button("Cancel", lambda: self.callbacks["cancel"](self.job_id), DANGER)
            return
        if state == "completed":
            self._button("Open", lambda: self.callbacks["open"](job), BG_ELEVATED)
            self._button("Folder", lambda: self.callbacks["show"](job), BG_ELEVATED)
        else:
            self._button("Retry", lambda: self.callbacks["retry"](job), BG_ELEVATED)
        self._button("Dismiss", lambda: self.callbacks["dismiss"](self.job_id), BG_ELEVATED)

    def _button(self, text: str, command, color: str) -> None:
        ctk.CTkButton(self.actions, text=text, height=24, width=58, fg_color=color,
                      hover_color=BG_PANEL, command=command).pack(side="left", padx=2)


def _truncate_middle(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    keep = max((limit - 3) // 2, 1)
    return "%s...%s" % (text[:keep], text[-keep:])


class DashboardView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=BG_DEEP)
        self.app, self.items, self.rows = app, {}, {}
        self._nav_stack: list[int | None] = []
        self._current_folder_id: int | None = None
        self._current_folder_payload: dict | None = None
        self._fullname_folder_ids: dict[str, int | None] = {"/": None}
        self._refresh_job = None
        self.download_jobs: dict[str, dict] = {}
        self.downloader = Downloader(
            backend=self.app.backend,
            session_factory=lambda: make_session(self.app.config.data),
            on_event=self._enqueue_dl_event,
        )
        self._top(); self._content(); self._footer()
        self.navigate_to(None, push_history=False)

    def _top(self) -> None:
        bar = GlowFrame(self); bar.pack(fill="x", padx=18, pady=(16, 8))
        self.link = ctk.CTkEntry(bar, placeholder_text="magnet:?xt=... or https://.../file.torrent")
        self.link.pack(side="left", fill="x", expand=True, padx=(14, 8), pady=12)
        paste = ctk.CTkButton(bar, text="Paste", width=78, fg_color=BG_ELEVATED,
                              text_color=ACCENT, command=self.paste_link)
        paste.pack(side="left", padx=(0, 8), pady=12)
        button = NeonButton(bar, text="Add to Seedr", width=140, command=self.add_link)
        button.pack(side="left", padx=(0, 12), pady=12)
        Tooltip(self.link, "Paste a magnet:?xt=... link or an https://... .torrent URL")
        Tooltip(paste, "Replace the current link with text from the clipboard")
        Tooltip(button, "Sends the link to your Seedr cloud storage where it will start downloading")
        self.app.bind("<Control-l>", lambda _e: self.link.focus_set())
        self.app.bind("<F5>", lambda _e: self.refresh())
        self.app.bind("<Alt-Left>", lambda _e: self.navigate_back())
        self.app.bind("<Alt-Up>", lambda _e: self.navigate_up())
        self.app.bind("<BackSpace>", self._backspace_navigation)

    def paste_link(self) -> None:
        try:
            clipboard_text = self.clipboard_get()
        except TclError:
            self.app.toast("The clipboard does not contain text.", True)
            return
        self.link.delete(0, "end")
        self.link.insert(0, clipboard_text)
        self.link.focus_set()

    def _content(self) -> None:
        content = ctk.CTkFrame(self, fg_color="transparent"); content.pack(fill="both", expand=True, padx=18, pady=5)
        content.grid_columnconfigure(0, weight=3); content.grid_columnconfigure(1, weight=2); content.grid_rowconfigure(0, weight=1)
        browser = GlowFrame(content); browser.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        nav = ctk.CTkFrame(browser, fg_color="transparent"); nav.pack(fill="x", padx=12, pady=9)
        self.btn_back = ctk.CTkButton(nav, text="←", width=38, fg_color=BG_ELEVATED,
                                      hover_color=BG_PANEL, command=self.navigate_back)
        self.btn_back.pack(side="left", padx=(0, 6))
        self.btn_up = ctk.CTkButton(nav, text="↑", width=38, fg_color=BG_ELEVATED,
                                    hover_color=BG_PANEL, command=self.navigate_up)
        self.btn_up.pack(side="left", padx=(0, 10))
        self.breadcrumb = ctk.CTkFrame(nav, fg_color="transparent")
        self.breadcrumb.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(nav, text="Refresh", width=80, fg_color=BG_ELEVATED, command=self.refresh).pack(side="right")
        self.empty = InfoBanner(browser, "Your Seedr drive is empty. Paste a magnet or .torrent link above to get started.")
        style = ttk.Style(); style.theme_use("clam")
        style.configure("Seedr.Treeview", background=BG_PANEL, fieldbackground=BG_PANEL,
                        foreground=TEXT_PRIMARY, rowheight=30, borderwidth=0)
        style.map("Seedr.Treeview", background=[("selected", ACCENT_DIM)])
        self.tree = ttk.Treeview(browser, columns=("type", "size"), show="tree headings", style="Seedr.Treeview")
        self.tree.heading("#0", text="Name"); self.tree.heading("type", text="Type"); self.tree.heading("size", text="Size")
        self.tree.column("type", width=90); self.tree.column("size", width=110)
        self.tree.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.tree.bind("<Double-1>", self.open_item); self.tree.bind("<Button-3>", self.context_menu)
        side = ctk.CTkFrame(content, fg_color="transparent"); side.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        self.transfer_box = GlowFrame(side); self.transfer_box.pack(fill="both", expand=True, pady=(0, 5))
        ctk.CTkLabel(self.transfer_box, text="ACTIVE TRANSFERS", font=(FONT, 14, "bold"), text_color=ACCENT).pack(anchor="w", padx=12, pady=10)
        self.transfer_text = ctk.CTkLabel(self.transfer_box, text="No active cloud transfers", text_color=TEXT_MUTED)
        self.transfer_text.pack(padx=12, pady=12)
        self.download_box = GlowFrame(side); self.download_box.pack(fill="both", expand=True, pady=(5, 0))
        ctk.CTkLabel(self.download_box, text="LOCAL DOWNLOADS", font=(FONT, 14, "bold"), text_color=ACCENT).pack(anchor="w", padx=12, pady=10)

    def _footer(self) -> None:
        footer = ctk.CTkFrame(self, fg_color=BG_PANEL, height=44); footer.pack(fill="x", side="bottom")
        self.storage = ctk.CTkLabel(footer, text="Storage: --", text_color=TEXT_MUTED); self.storage.pack(side="left", padx=18, pady=10)
        self.destination = ctk.CTkLabel(footer, text=self.app.config.get("download_destination"), text_color=TEXT_MUTED)
        self.destination.pack(side="right", padx=8)
        change = ctk.CTkButton(footer, text="Change...", width=80, fg_color="transparent", text_color=ACCENT, command=self.change_destination)
        change.pack(side="right"); Tooltip(change, "Where completed downloads are saved on this PC")

    def refresh(self) -> None:
        self.navigate_to(self._current_folder_id, push_history=False)

    def navigate_to(self, folder_id: int | None, push_history: bool = True) -> None:
        if push_history and self._current_folder_id != folder_id:
            self._nav_stack.append(self._current_folder_id)
        self._start_folder_load(folder_id)

    def navigate_up(self) -> None:
        if self._current_folder_payload is None:
            return
        parent = self._current_folder_payload.get("parent")
        if parent in (None, -1, 0) and self._current_folder_id is None:
            return
        target = None if parent in (None, -1, 0) else int(parent)
        self.navigate_to(target)

    def navigate_back(self) -> None:
        if not self._nav_stack:
            return
        previous = self._nav_stack.pop()
        self.navigate_to(previous, push_history=False)

    def _start_folder_load(self, folder_id: int | None) -> None:
        if self.app.backend:
            self.app.run_worker(self._folder_load_worker, folder_id)

    def _folder_load_worker(self, folder_id: int | None) -> None:
        try:
            data = self.app.backend.get_folder(folder_id) if folder_id is not None else self.app.backend.get_drive()
            self.app.post(self._on_folder_loaded, data, folder_id)
        except Exception as exc:
            self.app.logger.exception("Drive refresh failed"); self.app.post(self.app.toast, translate(exc), True)

    def _on_folder_loaded(self, payload: dict, requested_id: int | None) -> None:
        self._current_folder_payload = payload
        self._current_folder_id = requested_id
        self._cache_folder_ids(payload, requested_id)
        self._render_tree(payload)
        self._render_breadcrumb(payload)
        self._update_nav_buttons()

    def _render_tree(self, data: dict) -> None:
        self.items.clear()
        for child in self.tree.get_children(""):
            self.tree.delete(child)
        folders = data.get("folders") or data.get("folder") or []
        files = data.get("files") or []
        torrents = data.get("torrents") or []
        for kind, values in (("folder", folders), ("file", files), ("torrent", torrents)):
            for item in values if isinstance(values, list) else []:
                item_id = _item_id(kind, item)
                if item_id is None:
                    continue
                iid = _make_iid(kind, item_id)
                if kind == "folder":
                    name = _folder_label(item)
                elif kind == "file":
                    name = _file_label(item)
                else:
                    name = item.get("name") or item.get("title") or f"Torrent {item.get('id', '')}"
                size = item.get("size") or item.get("size_bytes") or 0
                self.tree.insert("", "end", iid=iid, text=name, values=(kind.title(), self._size(size)))
                self.items[iid] = (kind, item)
        self.empty.pack(fill="x", padx=12, pady=5, before=self.tree) if not self.items else self.empty.pack_forget()
        if torrents: self.transfer_text.configure(text=f"{len(torrents)} active transfer(s)")
        else: self.transfer_text.configure(text="No active cloud transfers")
        used = data.get("space_used") or data.get("used_space")
        total = data.get("space_max") or data.get("total_space")
        if used is not None: self.storage.configure(text=f"Storage: {self._size(used)} / {self._size(total or 0)}")
        if self._refresh_job:
            self.after_cancel(self._refresh_job)
        self._refresh_job = self.after(5000, self.refresh)

    def render_drive(self, data: dict) -> None:
        self._on_folder_loaded(data, self._current_folder_id)

    def _render_breadcrumb(self, payload: dict) -> None:
        for child in self.breadcrumb.winfo_children():
            child.destroy()
        path = (payload.get("fullname") or "").strip("/")
        parts = [part for part in path.split("/") if part]
        segments = [("My Seedr Drive", None, "/")]
        current = ""
        for part in parts:
            current = f"{current}/{part}" if current else f"/{part}"
            segments.append((part, self._fullname_folder_ids.get(current), current))
        if not parts:
            self.crumb = ctk.CTkLabel(self.breadcrumb, text="My Seedr Drive",
                                      font=(FONT, 16, "bold"), text_color=TEXT_PRIMARY)
            self.crumb.pack(side="left")
            return
        for index, (label, folder_id, _full) in enumerate(segments):
            if index:
                ctk.CTkLabel(self.breadcrumb, text="▸", text_color=TEXT_MUTED).pack(side="left", padx=4)
            if index == len(segments) - 1:
                self.crumb = ctk.CTkLabel(self.breadcrumb, text=label, font=(FONT, 16, "bold"),
                                          text_color=TEXT_PRIMARY)
                self.crumb.pack(side="left")
            else:
                button = ctk.CTkButton(self.breadcrumb, text=label, height=28, fg_color="transparent",
                                       hover_color=BG_ELEVATED, text_color=ACCENT, corner_radius=6,
                                       command=lambda fid=folder_id: self.navigate_to(fid))
                button.pack(side="left")

    def _update_nav_buttons(self) -> None:
        self.btn_back.configure(state="normal" if self._nav_stack else "disabled")
        self.btn_up.configure(state="disabled" if self._current_folder_id is None else "normal")

    def _cache_folder_ids(self, payload: dict, requested_id: int | None) -> None:
        fullname = (payload.get("fullname") or "").strip()
        if fullname:
            self._fullname_folder_ids[fullname] = requested_id
        base = fullname.rstrip("/")
        folders = payload.get("folders") or payload.get("folder") or []
        for folder in folders if isinstance(folders, list) else []:
            name = (folder.get("name") or "").strip()
            folder_id = folder.get("id") or folder.get("folder_id")
            if name and folder_id is not None:
                self._fullname_folder_ids[f"{base}/{name}" if base else f"/{name}"] = int(folder_id)

    @staticmethod
    def _size(value) -> str:
        try: number = float(value)
        except (TypeError, ValueError): return str(value)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if number < 1024 or unit == "TB": return f"{number:.1f} {unit}"
            number /= 1024
        return "0 B"

    def add_link(self) -> None:
        value = self.link.get()
        self.app.run_worker(self._add_worker, value)

    def _add_worker(self, value: str) -> None:
        try:
            self.app.backend.add_link(value)
            self.app.post(self.link.delete, 0, "end"); self.app.post(self.app.toast, "Added to Seedr. The transfer will appear shortly.")
            self.app.post(self.refresh)
        except ValueError as exc:
            self.app.post(self.app.toast, str(exc), True)
        except Exception as exc:
            self.app.logger.exception("Add torrent failed"); self.app.post(self.app.toast, translate(exc), True)

    def open_item(self, _event=None) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        entry = self._lookup_item(selected[0], "open_item")
        if entry and entry[0] == "folder":
            item = entry[1]
            folder_id = item.get("id") or item.get("folder_id")
            if folder_id is not None:
                self.navigate_to(int(folder_id))

    def _backspace_navigation(self, _event=None):
        focused = self.focus_get()
        if focused and focused.winfo_class() in {"Entry", "Text"}:
            return None
        self.navigate_back()
        return "break"

    def context_menu(self, event) -> None:
        iid = self.tree.identify_row(event.y)
        if not iid:
            return
        self.tree.selection_set(iid)
        entry = self._lookup_item(iid, "context_menu")
        if entry is None:
            return
        kind, _item = entry
        menu = ctk.CTkToplevel(self); menu.overrideredirect(True); menu.geometry(f"+{event.x_root}+{event.y_root}")
        if kind != "torrent":
            ctk.CTkButton(menu, text="Download here", fg_color=BG_ELEVATED,
                          command=lambda: (menu.destroy(), self.download(iid))).pack(fill="x")
        ctk.CTkButton(menu, text="Delete", fg_color=DANGER,
                      command=lambda: (menu.destroy(), self.delete(iid))).pack(fill="x")
        menu.bind("<FocusOut>", lambda _e: menu.destroy()); menu.focus_set()

    def download(self, iid: str) -> None:
        entry = self._lookup_item(iid, "download")
        if entry is None:
            self.app.toast("Couldn't find that item - try refreshing the folder.", True)
            return
        kind, item = entry
        if kind == "torrent": self.app.toast("Wait for this cloud transfer to finish first.", True); return
        try:
            job_id = self._submit_download(kind, item)
            log.info("submitted download iid=%s kind=%s job_id=%s", iid, kind, job_id)
        except Exception as exc:
            self.app.logger.exception("Download setup failed"); self.app.toast(translate(exc), True)

    def _submit_download(self, kind: str, item: dict) -> str:
        dest_dir = Path(self.app.config.get("download_destination"))
        if kind == "file":
            item_id = int(item.get("folder_file_id") or item.get("id"))
            name = _file_label(item)
            job_id = self.downloader.submit_file(item_id, name, dest_dir, name)
        else:
            item_id = int(item.get("id") or item.get("folder_id"))
            name = _folder_label(item)
            job_id = self.downloader.submit_folder(item_id, name, dest_dir, "%s.zip" % name)
        self.app.toast("Local download queued.")
        return job_id

    def _enqueue_dl_event(self, job) -> None:
        self.app.post(self._on_download_update, job.to_dict())

    def _on_download_update(self, job: dict) -> None:
        job_id = str(job["job_id"])
        previous = self.download_jobs.get(job_id, {})
        self.download_jobs[job_id] = job
        row = self.rows.get(job_id)
        if not row:
            callbacks = {
                "cancel": self.downloader.cancel,
                "open": self._open_download,
                "show": self._show_download,
                "retry": self._retry_download,
                "dismiss": self._dismiss_download,
            }
            row = DownloadRow(self.download_box, job, callbacks)
            row.pack(fill="x", padx=8, pady=4)
            self.rows[job_id] = row
        else:
            row.update(job)
        if previous.get("state") != job.get("state") and job.get("state") == "completed":
            self.app.toast("Download complete.", duration=8000)
        elif previous.get("state") != job.get("state") and job.get("state") == "failed":
            self.app.toast("Download failed: %s" % job.get("error", "Unknown error"), True)

    def _open_download(self, job: dict) -> None:
        path = Path(job["final_path"])
        self._open_path(path if path.exists() else path.parent)

    def _show_download(self, job: dict) -> None:
        path = Path(job["final_path"])
        if sys.platform == "win32":
            target = str(path if path.exists() else path.parent)
            subprocess.Popen(["explorer", "/select,", target])
            return
        self._open_path(path.parent)

    def _retry_download(self, job: dict) -> None:
        self._dismiss_download(str(job["job_id"]))
        if job["kind"] == "folder":
            self.downloader.submit_folder(int(job["seedr_id"]), str(job["display_name"]),
                                          Path(job["dest_dir"]), str(job["suggested_filename"]))
        else:
            self.downloader.submit_file(int(job["seedr_id"]), str(job["display_name"]),
                                        Path(job["dest_dir"]), str(job["suggested_filename"]))

    def _dismiss_download(self, job_id: str) -> None:
        row = self.rows.pop(job_id, None)
        if row:
            row.destroy()
        self.download_jobs.pop(job_id, None)

    def _open_path(self, path: Path) -> None:
        if sys.platform == "win32":
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])

    def delete(self, iid: str) -> None:
        entry = self._lookup_item(iid, "delete")
        if entry is None:
            self.app.toast("Couldn't find that item - try refreshing the folder.", True)
            return
        kind, item = entry
        if not messagebox.askyesno("Delete from Seedr", f"Delete {item.get('name', kind)} permanently from your Seedr drive?"): return
        item_id = _item_id(kind, item)
        if item_id is None:
            self.app.toast("Couldn't find that item - try refreshing the folder.", True)
            return
        self.app.run_worker(self._delete_worker, kind, item_id)

    def _delete_worker(self, kind: str, item_id: int) -> None:
        try:
            getattr(self.app.backend, f"delete_{kind}")(item_id); self.app.post(self.app.toast, "Deleted from Seedr."); self.app.post(self.refresh)
        except Exception as exc: self.app.post(self.app.toast, translate(exc), True)

    def change_destination(self) -> None:
        value = filedialog.askdirectory(initialdir=self.app.config.get("download_destination"))
        if value: self.app.config.set("download_destination", value); self.destination.configure(text=value)

    def _lookup_item(self, iid: str, action: str):
        entry = self.items.get(iid)
        if entry is None:
            log.warning("%s called with unknown iid=%s. items has %d entries, sample=%s",
                        action, iid, len(self.items), list(self.items.keys())[:5])
        return entry
