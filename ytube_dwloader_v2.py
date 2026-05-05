"""
ytube_dwloader_v2

Change Log (v2 vs v1)
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


def main():
    root = tk.Tk()
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
