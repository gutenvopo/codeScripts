"""
ytube_dwloader_v3

Change Log (v3)
- Duplicated from v2 as a new versioned file.
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
- Buttons: Start, Paste, Exit
- Start opens a new PowerShell window and runs yt-dlp with cookies + args
- Paste inserts clipboard contents into the entry
"""

import tkinter as tk
from tkinter import messagebox
import subprocess
import shutil
import shlex
import tempfile
from pathlib import Path
import sys
import ctypes


def main():
    root = tk.Tk()
    root.withdraw()

    try:
        app_id = "Kwa.ytube_dwloader.v3"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        pass

    script_dir = Path(__file__).resolve().parent
    ico_path = script_dir / "youtube_dldr_image.ico"
    png_path = script_dir / "youtube_dldr_image.png"

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
            corner = splash_img.get(0, 0)
            if isinstance(corner, tuple) and len(corner) >= 3:
                splash_bg = f"#{corner[0]:02x}{corner[1]:02x}{corner[2]:02x}"
            elif isinstance(corner, str) and corner.startswith("#") and len(corner) == 7:
                splash_bg = corner
            elif isinstance(corner, str):
                rgb = [int(value) for value in corner.split()[:3]]
                splash_bg = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

            splash.configure(bg=splash_bg)
            splash_frame.configure(bg=splash_bg)
            splash_icon.configure(bg=splash_bg)
            splash.wm_attributes("-transparentcolor", splash_bg)
        except Exception:
            pass

    screen_w = splash.winfo_screenwidth()
    screen_h = splash.winfo_screenheight()

    base_w = 220
    base_h = 120
    max_w = int(screen_w * 0.8)
    max_h = int(screen_h * 0.8)

    if splash_img is not None:
        target_w = splash_img.width()
        target_h = splash_img.height()
    else:
        target_w = base_w
        target_h = base_h

    target_w = min(target_w, max_w)
    target_h = min(target_h, max_h)
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

            parts = [ytdlp_path] + js_args + ["--cookies", r"C:\Users\kirwa\Documents\yt-dlp\ytube_cookies.txt"]

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
            ps_line = "& " + " ".join(ps_parts) + "\n"

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
        entry.insert(tk.END, clip)

    run_btn = tk.Button(btn_frame, text="Start", width=12, command=start_with_entry)
    run_btn.pack(side=tk.LEFT, padx=6)

    paste_btn = tk.Button(btn_frame, text="Paste", width=12, command=paste_from_clipboard)
    paste_btn.pack(side=tk.LEFT, padx=6)

    exit_btn = tk.Button(btn_frame, text="Exit", width=12, command=root.destroy)
    exit_btn.pack(side=tk.LEFT, padx=6)

    root.mainloop()


if __name__ == "__main__":
    main()
