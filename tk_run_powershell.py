import tkinter as tk
from tkinter import messagebox
import subprocess
import tempfile
from pathlib import Path
import sys


r"""
Simple Tkinter GUI:
- Entry box for extra arguments (wide)
- Buttons: Start, Paste, Exit

Start opens a new PowerShell window and runs:
  yt-dlp --cookies C:\Users\kirwa\Documents\yt-dlp\ytube_cookies.txt <user text>

Paste inserts clipboard contents into the entry.
"""


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
            if sys.platform.startswith("win"):
                def ps_quote(value: str) -> str:
                    return "'" + value.replace("'", "''") + "'"

                parts = ["yt-dlp", "--cookies", r"C:\Users\kirwa\Documents\yt-dlp\ytube_cookies.txt"]
                if user_text:
                    parts.append(user_text)

                ps_parts = [ps_quote(part) for part in parts]
                ps_line = "& " + " ".join(ps_parts) + "\n"

                with tempfile.NamedTemporaryFile(mode="w", suffix=".ps1", delete=False, encoding="utf-8") as temp_file:
                    temp_file.write(ps_line)
                    temp_path = Path(temp_file.name)

                subprocess.Popen(
                    ["powershell.exe", "-NoExit", "-File", str(temp_path)],
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                )
            else:
                messagebox.showerror("Unsupported OS", "This script only opens PowerShell on Windows.")
        except FileNotFoundError:
            messagebox.showerror("Not found", "powershell.exe not found on PATH in this environment.")
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
