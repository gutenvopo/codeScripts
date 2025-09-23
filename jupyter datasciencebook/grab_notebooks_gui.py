#!/usr/bin/env python3
import os, shutil, subprocess, tempfile, sys
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox

# === CONFIG: edit if you want a different repo/folder ===
REPO_URL    = "https://github.com/jakevdp/PythonDataScienceHandbook.git"
BRANCH      = "master"
FOLDER_PATH = "notebooks"  # folder inside the repo you want

def run(cmd):
    subprocess.run(cmd, check=True)

def main():
    # Basic checks
    try:
        subprocess.run(["git", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        print("Error: Git is not installed or not on PATH.", file=sys.stderr)
        sys.exit(1)

    root = tk.Tk()
    root.withdraw()

    # 1) Ask for destination directory (allows creating new folders in the dialog)
    dest_base = filedialog.askdirectory(title="Choose where to place the downloaded folder")
    if not dest_base:
        # User canceled
        sys.exit(0)

    # 2) Ask if you want to create/use a subfolder name
    default_sub = os.path.basename(FOLDER_PATH)
    sub_name = simpledialog.askstring(
        "Create (optional) subfolder",
        f"Enter a new subfolder name (or leave as '{default_sub}'):\n"
        "(Cancel = place directly in the chosen folder)",
        initialvalue=default_sub
    )

    if sub_name is None:  # Cancel → put files directly in dest_base
        dest_final = dest_base
    else:
        dest_final = os.path.join(dest_base, sub_name)

    # Confirm overwrite if exists and not empty
    if os.path.isdir(dest_final) and any(os.scandir(dest_final)):
        overwrite = messagebox.askyesno(
            "Folder not empty",
            f"'{dest_final}' already exists and is not empty.\n\nOverwrite files in it?",
            default=messagebox.NO
        )
        if not overwrite:
            sys.exit(0)

    tmpdir = tempfile.mkdtemp(prefix="gh_sparse_")
    try:
        # 3) Shallow clone without checkout
        run(["git", "clone", "--no-checkout", "--filter=blob:none", "--depth=1",
                "-b", BRANCH, REPO_URL, tmpdir])

        # 4) Enable sparse checkout and set the target folder
        run(["git", "-C", tmpdir, "sparse-checkout", "init", "--cone"])
        run(["git", "-C", tmpdir, "sparse-checkout", "set", FOLDER_PATH])

        # 5) Checkout just that folder
        run(["git", "-C", tmpdir, "checkout"])

        # 6) Copy results to destination
        src = os.path.join(tmpdir, FOLDER_PATH)

        # Make sure destination exists
        os.makedirs(dest_final, exist_ok=True)

        # Copy contents of src into dest_final (merge/overwrite as needed)
        for rootdir, dirs, files in os.walk(src):
            rel = os.path.relpath(rootdir, src)
            target_dir = os.path.join(dest_final, rel if rel != "." else "")
            os.makedirs(target_dir, exist_ok=True)
            for f in files:
                shutil.copy2(os.path.join(rootdir, f), os.path.join(target_dir, f))

        messagebox.showinfo("Done", f"Downloaded '{FOLDER_PATH}' to:\n{dest_final}")

    except subprocess.CalledProcessError as e:
        messagebox.showerror("Git error", f"Git command failed:\n{e}")
        sys.exit(1)
    except Exception as e:
        messagebox.showerror("Error", f"{type(e).__name__}: {e}")
        sys.exit(1)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

if __name__ == "__main__":
    main()