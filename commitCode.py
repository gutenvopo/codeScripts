import subprocess
import sys
import tkinter as tk
from tkinter import simpledialog, messagebox

def main():
    # Stage all changes
    subprocess.run(["git", "add", "."], check=True)

    # Prompt for commit message using a GUI dialog
    root = tk.Tk()
    root.withdraw()
    commit_message = simpledialog.askstring("Commit Message", "Enter your commit message:")

    if not commit_message:
        messagebox.showerror("Error", "Commit message cannot be empty. Aborting.")
        sys.exit(1)

    # Commit the changes
    subprocess.run(["git", "commit", "-m", commit_message], check=True)

    # Push the changes to the main branch
    subprocess.run(["git", "push", "origin", "main"], check=True)

if __name__ == "__main__":
    main()