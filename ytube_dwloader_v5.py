"""
ytube_dwloader_v5

Change Log (v5)
- Duplicated from v4 as a new versioned file.
- Preserved splash image behavior, transparency-key sampling, and startup flow.
- Kept default yt-dlp download behavior and PowerShell launch workflow.
- Switched button order so Paste appears before Start.
- Updated Paste behavior to replace entry text with the latest clipboard content.

Previous Change Log (v4)
- Duplicated from v3 as a new versioned file.
- Updated splash to image-only mode.
- Added dynamic edge-color sampling (most common border color) for splash transparency key selection.
- Tuned splash sizing to image dimensions to avoid clipping artifacts.
- Built standalone executable with PyInstaller spec for v4.
- Output artifact: `dist/ytube_dwloader_v4.exe`.

Previous Change Log (v3)
- Added startup splash screen support.
- Fixed splash visibility on Windows by forcing mapping/lift at startup.
- Updated splash sizing to scale from image dimensions with screen-safe bounds.
- Refined splash layout to remove visible border/padding artifacts.
- Switched splash to image-only mode (removed text labels).
- Added dynamic transparency-key handling using image corner color to reduce background box artifacts.

Previous Change Log (v2 vs v1)
- Added JS runtime auto-detection for yt-dlp (`node` preferred, fallback to `deno`).
- Added user prompt when no JS runtime is found, with option to continue.
- Added default download behavior when no extra args are entered:
    best MP4 video + M4A audio with MP4 merge output.
- Improved PowerShell command safety by quoting each argument individually.
- Runs yt-dlp through a generated temporary `.ps1` script in a new PowerShell window.
- Added clearer dependency checks and user-facing error dialogs for missing tools.
- Maintained simple GUI workflow (Start, Paste, Exit) focused on Windows use.

Summary
- Entry box for extra arguments (wide)
- Buttons: Paste, Start, Exit
- Start opens a new PowerShell window and runs yt-dlp with cookies + args
- Paste clears existing text and inserts the latest clipboard contents
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import subprocess
import shutil
import shlex
import tempfile
from pathlib import Path
import sys
import ctypes
from collections import Counter


def resource_path(filename: str) -> Path:
    base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base_dir / filename


def main():
    root = tk.Tk()
    root.withdraw()

    try:
        app_id = "Kwa.ytube_dwloader.v5"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        pass

    ico_path = resource_path("youtube_dldr_image.ico")
    png_path = resource_path("youtube_dldr_image.png")

    try:
        if ico_path.exists():
            root.iconbitmap(default=str(ico_path))
        elif png_path.exists():
            icon_photo = tk.PhotoImage(file=str(png_path))
            root.iconphoto(True, icon_photo)
            root._icon_photo_ref = icon_photo
    except Exception:
        pass

    splash = tk.Toplevel(root)
    splash.title("Starting...")
    splash.resizable(False, False)
    splash.overrideredirect(True)
    splash.attributes("-topmost", True)
    splash_bg = root.cget("bg")
    splash.configure(bg=splash_bg)

    try:
        if ico_path.exists():
            splash.iconbitmap(default=str(ico_path))
        elif png_path.exists():
            splash.iconphoto(True, root._icon_photo_ref)
    except Exception:
        pass

    splash_frame = tk.Frame(splash, bg=splash_bg, bd=0, highlightthickness=0)
    splash_frame.pack(expand=True, fill=tk.BOTH)

    splash_img = None
    splash_icon = None
    if png_path.exists():
        try:
            splash_img = tk.PhotoImage(file=str(png_path))
            splash_icon = tk.Label(splash_frame, image=splash_img, bg=splash_bg, bd=0, highlightthickness=0)
            splash_icon.image = splash_img
            splash_icon.pack()
        except Exception:
            pass

    if splash_img is not None and splash_icon is not None:
        try:
            def to_hex(color_value):
                if isinstance(color_value, tuple) and len(color_value) >= 3:
                    return f"#{color_value[0]:02x}{color_value[1]:02x}{color_value[2]:02x}"
                if isinstance(color_value, str) and color_value.startswith("#") and len(color_value) == 7:
                    return color_value.lower()
                if isinstance(color_value, str):
                    rgb = [int(value) for value in color_value.split()[:3]]
                    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
                return None

            image_w = splash_img.width()
            image_h = splash_img.height()
            edge_colors = []

            for x in range(image_w):
                top_color = to_hex(splash_img.get(x, 0))
                bottom_color = to_hex(splash_img.get(x, image_h - 1))
                if top_color:
                    edge_colors.append(top_color)
                if bottom_color:
                    edge_colors.append(bottom_color)

            for y in range(1, image_h - 1):
                left_color = to_hex(splash_img.get(0, y))
                right_color = to_hex(splash_img.get(image_w - 1, y))
                if left_color:
                    edge_colors.append(left_color)
                if right_color:
                    edge_colors.append(right_color)

            if edge_colors:
                splash_bg = Counter(edge_colors).most_common(1)[0][0]

            splash.configure(bg=splash_bg)
            splash_frame.configure(bg=splash_bg)
            splash_icon.configure(bg=splash_bg)
            splash.wm_attributes("-transparentcolor", splash_bg)
        except Exception:
            pass

    base_w = 220
    base_h = 120

    if splash_img is not None:
        target_w = splash_img.width()
        target_h = splash_img.height()
    else:
        target_w = base_w
        target_h = base_h
    splash.geometry(f"{target_w}x{target_h}")

    splash.update_idletasks()
    x = (splash.winfo_screenwidth() - splash.winfo_width()) // 2
    y = (splash.winfo_screenheight() - splash.winfo_height()) // 2
    splash.geometry(f"+{x}+{y}")
    splash.deiconify()
    splash.lift()
    splash.focus_force()
    splash.update()

    def close_splash():
        try:
            splash.destroy()
        finally:
            root.deiconify()

    root.after(2000, close_splash)

    root.title("Run PowerShell")
    root.geometry("420x140")
    root.resizable(False, False)

    frm = tk.Frame(root, padx=12, pady=12)
    frm.pack(expand=True, fill=tk.BOTH)

    lbl = tk.Label(frm, text="Enter additional arguments:")
    lbl.pack(anchor=tk.W)

    entry = tk.Entry(frm, width=70)
    entry.pack(fill=tk.X, pady=(6, 8))

    btn_frame = tk.Frame(frm)
    btn_frame.pack()

    def start_with_entry():
        user_text = entry.get().strip()

        try:
            if not sys.platform.startswith("win"):
                messagebox.showerror("Unsupported OS", "This script only opens PowerShell on Windows.")
                return

            pwsh_path = shutil.which("pwsh") or shutil.which("pwsh.exe")
            if not pwsh_path:
                messagebox.showerror("Not found", "pwsh.exe (PowerShell 7) not found on PATH in this environment.")
                return

            ytdlp_path = shutil.which("yt-dlp") or shutil.which("yt-dlp.exe")
            if not ytdlp_path:
                messagebox.showerror("Not found", "yt-dlp not found on PATH in this environment.")
                return

            node_path = shutil.which("node") or shutil.which("node.exe")
            deno_path = shutil.which("deno") or shutil.which("deno.exe")

            js_args = []
            if node_path:
                js_args = ["--js-runtimes", f"node:{node_path}"]
            elif deno_path:
                js_args = ["--js-runtimes", "deno"]
            else:
                cont = messagebox.askyesno(
                    "No JS runtime found",
                    "No supported JS runtime (node or deno) was found on PATH.\nSome formats may be missing. Continue without a JS runtime?",
                )
                if not cont:
                    return

            def ps_quote(value: str) -> str:
                return "'" + value.replace("'", "''") + "'"

            default_downloads = Path.home() / "Downloads"
            initial_dir = str(default_downloads if default_downloads.exists() else Path.home())
            download_dir = filedialog.askdirectory(
                title="Select download folder",
                initialdir=initial_dir,
                mustexist=True,
            )
            if not download_dir:
                return

            parts = [ytdlp_path] + js_args + ["--cookies", r"C:\Users\kirwa\Documents\yt-dlp\ytube_cookies.txt", "-P", download_dir]

            # Default to downloading the best video+audio and merging to MP4
            default_args = [
                "-f",
                "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best",
                "--merge-output-format",
                "mp4",
            ]

            if user_text:
                try:
                    extra_parts = shlex.split(user_text)
                except Exception:
                    extra_parts = [user_text]
                parts.extend(extra_parts)
            else:
                parts.extend(default_args)

            ps_parts = [ps_quote(part) for part in parts]
            quoted_download_dir = ps_quote(download_dir)
            ps_line = (
                "& " + " ".join(ps_parts) + "\n"
                + f"if (Test-Path {quoted_download_dir}) {{ Start-Process explorer.exe {quoted_download_dir} }}\n"
            )

            with tempfile.NamedTemporaryFile(mode="w", suffix=".ps1", delete=False, encoding="utf-8") as temp_file:
                temp_file.write(ps_line)
                temp_path = Path(temp_file.name)

            subprocess.Popen(
                [pwsh_path, "-NoExit", "-File", str(temp_path)],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
        except Exception as error:
            messagebox.showerror("Error", f"Failed to open PowerShell: {error}")

    def paste_from_clipboard():
        try:
            clip = root.clipboard_get()
        except Exception:
            clip = ""
        entry.delete(0, tk.END)
        entry.insert(0, clip)

    paste_btn = tk.Button(btn_frame, text="Paste", width=12, command=paste_from_clipboard)
    paste_btn.pack(side=tk.LEFT, padx=6)

    run_btn = tk.Button(btn_frame, text="Start", width=12, command=start_with_entry)
    run_btn.pack(side=tk.LEFT, padx=6)

    exit_btn = tk.Button(btn_frame, text="Exit", width=12, command=root.destroy)
    exit_btn.pack(side=tk.LEFT, padx=6)

    root.mainloop()


if __name__ == "__main__":
    main()
