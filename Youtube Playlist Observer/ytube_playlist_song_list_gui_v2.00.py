"""
YouTube Playlist Song List GUI v2.00
================================================================================

WHAT THIS APP DOES
1. Lets you paste any YouTube playlist URL into a Tkinter desktop GUI.
2. Lets you choose specific playlist positions such as:
      all
      1, 3, 7
      5-12
      1, 4, 10-15
3. Reads playlist metadata with yt-dlp without downloading any videos.
4. Exports the selected playlist entries to a Markdown `.md` file.

REQUIREMENT
Install yt-dlp for the Python you use to run this file:

    python -m pip install yt-dlp

Optional:
For private, age-restricted, or region-sensitive playlists, export YouTube cookies
and select the cookies `.txt` file inside this app.
================================================================================
"""

import json
import queue
import shutil
import subprocess
import sys
import threading
import traceback
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext
import tkinter as tk


APP_TITLE = "YouTube Playlist Song List v2.00"
SCRIPT_DIR = Path(__file__).resolve().parent
RWAKI_DEV_V3_PYTHON = SCRIPT_DIR.parent / "rwakiDev_v3" / "Scripts" / "python.exe"
DEFAULT_OUTPUT_PATH = SCRIPT_DIR / "youtube_playlist_song_list.md"

THEME = {
    "bg": "#080b12",
    "chrome": "#05070d",
    "panel": "#101826",
    "panel_2": "#0c1320",
    "input": "#070b12",
    "line": "#203247",
    "text": "#e7f6ff",
    "muted": "#88a1b7",
    "accent": "#28f0ff",
    "accent_2": "#7c5cff",
    "success": "#20d07a",
    "warning": "#ffcc66",
    "danger": "#ff5d73",
}


def install_yt_dlp_for_python(python_path, log_callback=None):
    if log_callback:
        log_callback(f"yt-dlp is missing for this Python: {python_path}")
        log_callback("Installing yt-dlp for the selected Python environment...")

    command = [str(python_path), "-m", "pip", "install", "yt-dlp"]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if completed.returncode != 0:
        output = "\n".join(
            part.strip()
            for part in [completed.stdout, completed.stderr]
            if part.strip()
        )
        raise RuntimeError(
            "Could not install yt-dlp automatically.\n\n"
            "Run this exact command in PowerShell:\n\n"
            f'"{python_path}" -m pip install yt-dlp\n\n'
            f"Installer output:\n{output}"
        )

    if log_callback:
        log_callback("yt-dlp installed successfully.")


def install_yt_dlp_for_current_python(log_callback=None):
    install_yt_dlp_for_python(sys.executable, log_callback)


def preferred_metadata_python():
    if RWAKI_DEV_V3_PYTHON.exists():
        return RWAKI_DEV_V3_PYTHON
    return Path(sys.executable)


def ensure_yt_dlp_in_python(python_path, log_callback=None):
    check = subprocess.run(
        [str(python_path), "-c", "import yt_dlp"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if check.returncode != 0:
        install_yt_dlp_for_python(python_path, log_callback)


def parse_positions(raw_text, total_count):
    text = raw_text.strip().lower()
    if not text or text == "all":
        return list(range(1, total_count + 1))

    positions = set()
    for chunk in text.split(","):
        item = chunk.strip()
        if not item:
            continue

        if "-" in item:
            start_text, end_text = [part.strip() for part in item.split("-", 1)]
            if not start_text.isdigit() or not end_text.isdigit():
                raise ValueError(f"Invalid range: {item}")
            start = int(start_text)
            end = int(end_text)
            if start > end:
                raise ValueError(f"Range starts after it ends: {item}")
            positions.update(range(start, end + 1))
        else:
            if not item.isdigit():
                raise ValueError(f"Invalid position: {item}")
            positions.add(int(item))

    valid_positions = sorted(pos for pos in positions if 1 <= pos <= total_count)
    if not valid_positions:
        raise ValueError("No selected positions exist in this playlist.")
    return valid_positions


def clean_markdown_cell(value):
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()


def safe_windows_filename(name, fallback="YouTube Playlist"):
    cleaned = "".join(
        "_" if char in '<>:"/\\|?*' or ord(char) < 32 else char
        for char in str(name or "").strip()
    )
    cleaned = " ".join(cleaned.split()).strip(" .")
    return cleaned or fallback


def markdown_path_for_playlist(output_path, playlist_info):
    requested_path = Path(output_path)
    playlist_title = playlist_info.get("title") or "YouTube Playlist"
    filename = f"{safe_windows_filename(playlist_title)}.md"

    if requested_path.exists() and requested_path.is_dir():
        return requested_path / filename

    return requested_path.parent / filename


def entry_title(entry):
    return (
        entry.get("title")
        or entry.get("fulltitle")
        or entry.get("alt_title")
        or "Untitled"
    )


def entry_url(entry):
    url = entry.get("webpage_url") or entry.get("url") or ""
    if url and not url.startswith(("http://", "https://")):
        return f"https://www.youtube.com/watch?v={url}"
    return url


def load_playlist_with_python_module(url, cookies_path=None):
    import yt_dlp

    options = {
        "extract_flat": True,
        "ignoreerrors": True,
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }
    if cookies_path:
        options["cookiefile"] = cookies_path

    with yt_dlp.YoutubeDL(options) as ydl:
        return ydl.extract_info(url, download=False)


def load_playlist_with_executable(url, cookies_path=None, python_path=None):
    if python_path:
        command = [str(python_path), "-m", "yt_dlp"]
    else:
        yt_dlp_path = shutil.which("yt-dlp")
        if not yt_dlp_path:
            raise RuntimeError(
                "yt-dlp is not installed. Install it with:\n\n"
                "python -m pip install yt-dlp"
            )
        command = [yt_dlp_path]

    command.extend([
        "--flat-playlist",
        "--dump-single-json",
        "--ignore-errors",
        "--no-warnings",
    ])
    if cookies_path:
        command.extend(["--cookies", cookies_path])
    command.append(url)

    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return json.loads(completed.stdout)


def load_playlist(url, cookies_path=None, log_callback=None):
    metadata_python = preferred_metadata_python()

    if metadata_python == RWAKI_DEV_V3_PYTHON:
        if log_callback:
            log_callback(f"Using environment: {metadata_python}")
        ensure_yt_dlp_in_python(metadata_python, log_callback)
        return load_playlist_with_executable(url, cookies_path, metadata_python)

    try:
        return load_playlist_with_python_module(url, cookies_path)
    except ModuleNotFoundError:
        install_yt_dlp_for_current_python(log_callback)
        return load_playlist_with_python_module(url, cookies_path)


def build_markdown(playlist_info, selected_entries):
    playlist_title = playlist_info.get("title") or "YouTube Playlist"
    source_url = playlist_info.get("webpage_url") or playlist_info.get("original_url") or ""
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        f"# {playlist_title}",
        "",
        f"- Generated: {generated_at}",
        f"- Source: {source_url}" if source_url else "- Source: Not provided",
        f"- Selected entries: {len(selected_entries)}",
        "",
        "| Position | Song Name | URL |",
        "|---:|---|---|",
    ]

    for position, entry in selected_entries:
        title = clean_markdown_cell(entry_title(entry))
        url = clean_markdown_cell(entry_url(entry))
        link = f"[Open]({url})" if url else ""
        lines.append(f"| {position} | {title} | {link} |")

    lines.append("")
    return "\n".join(lines)


class PlaylistSongListApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("980x720")
        self.root.minsize(820, 620)
        self.root.configure(bg=THEME["bg"])
        self.root.overrideredirect(True)
        self.root.bind("<Map>", self._restore_chrome)

        self.output_queue = queue.Queue()
        self.worker_thread = None
        self.last_markdown_path = None
        self.cookies_path = tk.StringVar(value="")
        self.output_path = tk.StringVar(value=str(DEFAULT_OUTPUT_PATH))
        self.saved_file_location = tk.StringVar(value="No file created yet.")

        self._build_ui()
        self._poll_queue()

    def _label(self, parent, text, **kwargs):
        label = tk.Label(
            parent,
            text=text,
            bg=kwargs.pop("bg", THEME["panel"]),
            fg=kwargs.pop("fg", THEME["text"]),
            font=kwargs.pop("font", ("Segoe UI", 10, "bold")),
            **kwargs,
        )
        return label

    def _entry(self, parent, **kwargs):
        entry = tk.Entry(
            parent,
            bg=THEME["input"],
            fg=THEME["text"],
            insertbackground=THEME["accent"],
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=THEME["line"],
            highlightcolor=THEME["accent"],
            font=("Consolas", 10),
            **kwargs,
        )
        return entry

    def _button(self, parent, text, command, kind="secondary", **kwargs):
        colors = {
            "primary": (THEME["accent"], "#031014", THEME["accent"]),
            "success": (THEME["success"], "#04130c", THEME["success"]),
            "danger": (THEME["danger"], "#16050a", THEME["danger"]),
            "secondary": (THEME["panel_2"], THEME["text"], THEME["line"]),
        }
        bg, fg, border = colors[kind]
        button = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=THEME["accent_2"],
            activeforeground="white",
            disabledforeground="#4f6275",
            relief=tk.FLAT,
            bd=0,
            highlightthickness=1,
            highlightbackground=border,
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            padx=12,
            pady=7,
            **kwargs,
        )
        return button

    def _panel(self, parent, **kwargs):
        return tk.Frame(
            parent,
            bg=THEME["panel"],
            highlightthickness=1,
            highlightbackground=THEME["line"],
            **kwargs,
        )

    def _build_chrome_button(self, parent, text, command, danger=False):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=THEME["danger"] if danger else THEME["chrome"],
            fg="white" if danger else THEME["text"],
            activebackground=THEME["danger"] if danger else THEME["accent_2"],
            activeforeground="white",
            relief=tk.FLAT,
            bd=0,
            width=4,
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
        )

    def _start_move(self, event):
        self._drag_offset_x = event.x
        self._drag_offset_y = event.y

    def _drag_window(self, event):
        x = event.x_root - self._drag_offset_x
        y = event.y_root - self._drag_offset_y
        self.root.geometry(f"+{x}+{y}")

    def _minimize_window(self):
        self.root.overrideredirect(False)
        self.root.iconify()

    def _restore_chrome(self, _event=None):
        if self.root.state() == "normal":
            self.root.after(10, lambda: self.root.overrideredirect(True))

    def _build_ui(self):
        shell = tk.Frame(
            self.root,
            bg=THEME["chrome"],
            highlightthickness=1,
            highlightbackground=THEME["accent"],
        )
        shell.pack(fill=tk.BOTH, expand=True)

        title_bar = tk.Frame(shell, bg=THEME["chrome"], height=38)
        title_bar.pack(fill=tk.X)
        title_bar.bind("<Button-1>", self._start_move)
        title_bar.bind("<B1-Motion>", self._drag_window)

        title_accent = tk.Frame(title_bar, bg=THEME["accent"], width=5)
        title_accent.pack(side=tk.LEFT, fill=tk.Y)

        title_text = tk.Label(
            title_bar,
            text="  YOUTUBE PLAYLIST OBSERVER  //  v2.00",
            bg=THEME["chrome"],
            fg=THEME["accent"],
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        )
        title_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        title_text.bind("<Button-1>", self._start_move)
        title_text.bind("<B1-Motion>", self._drag_window)

        self._build_chrome_button(title_bar, "X", self.root.destroy, danger=True).pack(
            side=tk.RIGHT, fill=tk.Y
        )
        self._build_chrome_button(title_bar, "_", self._minimize_window).pack(
            side=tk.RIGHT, fill=tk.Y
        )

        rim = tk.Frame(shell, bg=THEME["accent_2"], height=1)
        rim.pack(fill=tk.X)

        main = tk.Frame(shell, bg=THEME["bg"], padx=20, pady=18)
        main.pack(fill=tk.BOTH, expand=True)

        header = tk.Frame(main, bg=THEME["bg"])
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        self._label(
            header,
            "YOUTUBE PLAYLIST OBSERVER",
            bg=THEME["bg"],
            fg=THEME["accent"],
            font=("Segoe UI", 18, "bold"),
        ).pack(anchor="w")
        self._label(
            header,
            "Dark metadata console for exporting playlist tracks to Markdown",
            bg=THEME["bg"],
            fg=THEME["muted"],
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(3, 0))

        form = self._panel(main, padx=16, pady=14)
        form.grid(row=1, column=0, sticky="ew")

        self._label(form, text="Playlist URL").grid(row=0, column=0, sticky="w")
        self.url_entry = self._entry(form)
        self.url_entry.grid(row=1, column=0, sticky="ew", pady=(5, 14), ipady=7)
        self._button(form, "Paste Playlist", self.paste_playlist_url).grid(
            row=1, column=1, sticky="ew", padx=(10, 0), pady=(5, 14)
        )
        self._button(form, "Clear Playlist", self.clear_playlist_url).grid(
            row=1, column=2, sticky="ew", padx=(10, 0), pady=(5, 14)
        )

        self._label(form, text="Positions").grid(row=2, column=0, sticky="w")
        self.positions_entry = self._entry(form)
        self.positions_entry.insert(0, "all")
        self.positions_entry.grid(row=3, column=0, sticky="ew", pady=(5, 14), ipady=7)

        self._label(
            form,
            text="Examples: all, 1, 3, 10-20, 1, 5, 12-15",
            fg=THEME["muted"],
            font=("Segoe UI", 9),
        ).grid(
            row=3, column=1, columnspan=2, sticky="w", padx=(12, 0), pady=(5, 14)
        )

        self._label(form, text="Output Markdown File").grid(row=4, column=0, sticky="w")
        output_entry = self._entry(form, textvariable=self.output_path)
        output_entry.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(5, 14), ipady=7)
        self._button(form, "Choose...", self.choose_output_file).grid(
            row=5, column=2, sticky="ew", padx=(10, 0), pady=(5, 14)
        )

        self._label(form, text="Cookies File (optional)").grid(row=6, column=0, sticky="w")
        cookies_entry = self._entry(form, textvariable=self.cookies_path)
        cookies_entry.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(5, 0), ipady=7)
        self._button(form, "Choose...", self.choose_cookies_file).grid(
            row=7, column=2, sticky="ew", padx=(10, 0), pady=(5, 0)
        )

        form.columnconfigure(0, weight=1)
        form.columnconfigure(1, weight=1)

        button_row = tk.Frame(main, bg=THEME["bg"])
        button_row.grid(row=2, column=0, sticky="ew", pady=(16, 14))

        self.start_button = self._button(
            button_row,
            "Create Markdown",
            self.start_export,
            kind="primary",
            width=18,
        )
        self.start_button.pack(side=tk.LEFT)

        self._button(button_row, "Clear Log", self.clear_log, width=12).pack(
            side=tk.LEFT, padx=(10, 0)
        )
        self.open_markdown_button = self._button(
            button_row,
            "Open in VS Code",
            self.open_markdown_file,
            width=15,
            state=tk.DISABLED,
        )
        self.open_markdown_button.pack(side=tk.LEFT, padx=(10, 0))
        self.open_folder_button = self._button(
            button_row,
            "Open Folder",
            self.open_markdown_folder,
            width=13,
            state=tk.DISABLED,
        )
        self.open_folder_button.pack(side=tk.LEFT, padx=(10, 0))
        self._button(button_row, "Exit", self.root.destroy, kind="danger", width=10).pack(
            side=tk.RIGHT
        )

        output_panel = self._panel(main, padx=16, pady=12)
        output_panel.grid(row=3, column=0, sticky="ew", pady=(0, 14))

        self._label(output_panel, text="Created File Location").grid(row=0, column=0, sticky="w")
        self.location_link = tk.Label(
            output_panel,
            textvariable=self.saved_file_location,
            anchor="w",
            bg=THEME["panel"],
            fg=THEME["accent"],
            cursor="hand2",
            font=("Consolas", 9, "underline"),
        )
        self.location_link.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        self.location_link.bind("<Button-1>", self.open_markdown_file_from_link)
        output_panel.columnconfigure(0, weight=1)

        log_panel = self._panel(main, padx=12, pady=12)
        log_panel.grid(row=4, column=0, sticky="nsew")
        self._label(
            log_panel,
            text="Activity Log",
            fg=THEME["warning"],
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(0, 8))
        self.log_box = scrolledtext.ScrolledText(
            log_panel,
            height=16,
            wrap=tk.WORD,
            bg="#05070c",
            fg="#bdefff",
            insertbackground=THEME["accent"],
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=THEME["line"],
            highlightcolor=THEME["accent"],
            font=("Consolas", 10),
        )
        self.log_box.pack(fill=tk.BOTH, expand=True)

        main.columnconfigure(0, weight=1)
        main.rowconfigure(4, weight=1)

        self.log("Ready. Paste a YouTube playlist URL and choose your positions.")

    def choose_output_file(self):
        chosen = filedialog.asksaveasfilename(
            title="Save Markdown File",
            defaultextension=".md",
            filetypes=[("Markdown files", "*.md"), ("All files", "*.*")],
            initialfile="youtube_playlist_song_list.md",
        )
        if chosen:
            self.output_path.set(chosen)

    def choose_cookies_file(self):
        chosen = filedialog.askopenfilename(
            title="Choose Cookies File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if chosen:
            self.cookies_path.set(chosen)

    def paste_playlist_url(self):
        try:
            clipboard_text = self.root.clipboard_get().strip()
        except tk.TclError:
            messagebox.showwarning(APP_TITLE, "The clipboard is empty or does not contain text.")
            return

        if not clipboard_text:
            messagebox.showwarning(APP_TITLE, "The clipboard is empty.")
            return

        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, clipboard_text)
        self.log("Pasted playlist URL from clipboard.")

    def clear_playlist_url(self):
        self.url_entry.delete(0, tk.END)
        self.url_entry.focus_set()
        self.log("Cleared playlist URL box.")

    def open_markdown_file(self):
        if not self.last_markdown_path or not self.last_markdown_path.exists():
            messagebox.showwarning(APP_TITLE, "No Markdown file has been created yet.")
            return

        code_command = shutil.which("code") or shutil.which("code.cmd")
        if not code_command:
            messagebox.showerror(
                APP_TITLE,
                "VS Code command was not found on PATH.\n\n"
                "Install the VS Code shell command or open the Markdown file manually:\n\n"
                f"{self.last_markdown_path}",
            )
            return

        try:
            subprocess.Popen([code_command, str(self.last_markdown_path)])
            self.log(f"Opened Markdown file in VS Code: {self.last_markdown_path}")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, f"Could not open VS Code:\n\n{exc}")

    def open_markdown_file_from_link(self, _event=None):
        self.open_markdown_file()

    def open_markdown_folder(self):
        if not self.last_markdown_path or not self.last_markdown_path.exists():
            messagebox.showwarning(APP_TITLE, "No Markdown file has been created yet.")
            return

        try:
            subprocess.Popen(
                ["explorer.exe", "/select,", str(self.last_markdown_path)]
            )
            self.log(f"Opened file location: {self.last_markdown_path.parent}")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, f"Could not open the file location:\n\n{exc}")

    def set_running(self, is_running):
        self.start_button.config(
            state=tk.DISABLED if is_running else tk.NORMAL,
            text="Working..." if is_running else "Create Markdown",
            bg=THEME["panel_2"] if is_running else THEME["accent"],
            fg=THEME["muted"] if is_running else "#031014",
        )

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_box.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_box.see(tk.END)

    def clear_log(self):
        self.log_box.delete("1.0", tk.END)

    def start_export(self):
        url = self.url_entry.get().strip()
        positions_text = self.positions_entry.get().strip()
        output_path = self.output_path.get().strip()
        cookies_path = self.cookies_path.get().strip() or None

        if not url:
            messagebox.showwarning(APP_TITLE, "Please paste a YouTube playlist URL.")
            return
        if not output_path:
            messagebox.showwarning(APP_TITLE, "Please choose an output Markdown file.")
            return

        self.set_running(True)
        self.worker_thread = threading.Thread(
            target=self.export_worker,
            args=(url, positions_text, output_path, cookies_path),
            daemon=True,
        )
        self.worker_thread.start()

    def export_worker(self, url, positions_text, output_path, cookies_path):
        try:
            self.output_queue.put(("log", "Reading playlist metadata..."))
            playlist_info = load_playlist(
                url,
                cookies_path,
                lambda message: self.output_queue.put(("log", message)),
            )
            entries = [entry for entry in playlist_info.get("entries", []) if entry]

            if not entries:
                raise RuntimeError(
                    "No playlist entries were found. Check the URL, playlist privacy, "
                    "or try selecting a cookies file."
                )

            positions = parse_positions(positions_text, len(entries))
            selected_entries = [(pos, entries[pos - 1]) for pos in positions]
            markdown = build_markdown(playlist_info, selected_entries)

            path = markdown_path_for_playlist(output_path, playlist_info)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(markdown, encoding="utf-8")

            self.output_queue.put(
                (
                    "done",
                    f"Saved {len(selected_entries)} entries to:\n{path}",
                    str(path),
                )
            )
        except Exception as exc:
            details = traceback.format_exc()
            self.output_queue.put(("error", f"{exc}\n\nDetails:\n{details}"))

    def _poll_queue(self):
        try:
            while True:
                item = self.output_queue.get_nowait()
                kind, message = item[0], item[1]
                if kind == "log":
                    self.log(message)
                elif kind == "done":
                    self.last_markdown_path = Path(item[2])
                    self.saved_file_location.set(str(self.last_markdown_path))
                    self.open_markdown_button.config(state=tk.NORMAL)
                    self.open_folder_button.config(state=tk.NORMAL)
                    self.log(message)
                    self.set_running(False)
                    messagebox.showinfo(APP_TITLE, message)
                elif kind == "error":
                    self.log(message)
                    self.set_running(False)
                    messagebox.showerror(APP_TITLE, message)
        except queue.Empty:
            pass

        self.root.after(100, self._poll_queue)


def main():
    root = tk.Tk()
    app = PlaylistSongListApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
