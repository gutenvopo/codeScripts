import os
import shutil
import threading
import tkinter as tk
from tkinter import messagebox


STEAM_PATH = r"C:\Program Files (x86)\Steam"
ALLOWED_NAMES = {"steamapps", "userdata", "steam.exe"}


def append_output(text_widget, msg):
	text_widget.config(state='normal')
	text_widget.insert(tk.END, msg + "\n")
	text_widget.see(tk.END)
	text_widget.config(state='disabled')


def gather_deletions(root_path):
	to_delete = []
	try:
		for name in os.listdir(root_path):
			if name.lower() in ALLOWED_NAMES:
				continue
			full = os.path.join(root_path, name)
			to_delete.append(full)
	except Exception:
		to_delete = []
	return to_delete


def perform_deletion(output_widget, start_button):
	start_button.config(state='disabled')
	append_output(output_widget, f"Scanning {STEAM_PATH}...")

	if not os.path.exists(STEAM_PATH) or not os.path.isdir(STEAM_PATH):
		append_output(output_widget, f"Path not found: {STEAM_PATH}")
		start_button.config(state='normal')
		return

	# Basic sanity check: require steam.exe to exist in the folder
	if not os.path.exists(os.path.join(STEAM_PATH, 'steam.exe')):
		append_output(output_widget, "Warning: steam.exe not found in target folder. Aborting to avoid accidental deletions.")
		start_button.config(state='normal')
		return

	to_delete = gather_deletions(STEAM_PATH)
	if not to_delete:
		append_output(output_widget, "Nothing to delete (no matching files/folders found).")
		append_output(output_widget, "All Done")
		start_button.config(state='normal')
		return

	append_output(output_widget, "Items found for deletion:")
	for p in to_delete:
		append_output(output_widget, f"  {p}")

	proceed = messagebox.askyesno("Confirm Deletion", f"Found {len(to_delete)} items to delete under\n{STEAM_PATH}\n\nThis will permanently remove those files/folders. Continue?")
	if not proceed:
		append_output(output_widget, "Operation cancelled by user.")
		start_button.config(state='normal')
		return

	append_output(output_widget, "Starting deletion. Administrator rights may be required; errors will be reported below.")
	deleted_any = False
	for p in to_delete:
		try:
			if os.path.islink(p) or os.path.isfile(p):
				os.remove(p)
				append_output(output_widget, f"Deleted file: {p}")
			elif os.path.isdir(p):
				shutil.rmtree(p)
				append_output(output_widget, f"Deleted folder: {p}")
			else:
				append_output(output_widget, f"Skipped (unknown type): {p}")
			deleted_any = True
		except Exception as e:
			append_output(output_widget, f"Error deleting {p}: {e}")

	append_output(output_widget, "All Done")
	start_button.config(state='normal')


def on_start(output_widget, start_button):
	t = threading.Thread(target=perform_deletion, args=(output_widget, start_button), daemon=True)
	t.start()


def run_dns_flush(output_widget):
	"""Launch Steam's flush config URI to clear Steam's DNS/cache."""
	try:
		append_output(output_widget, "Launching Steam DNS flush (steam://flushconfig) ...")
		os.startfile("steam://flushconfig")
		append_output(output_widget, "Command sent to Steam client.")
	except Exception as e:
		append_output(output_widget, f"Failed to launch steam://flushconfig: {e}")
		messagebox.showerror("Error", f"Could not run DNS flush: {e}")


def build_ui():
	root = tk.Tk()
	root.title("steam Fixer")
	root.geometry("800x400")

	frame = tk.Frame(root)
	frame.pack(fill='both', expand=True, padx=8, pady=8)

	output = tk.Text(frame, wrap='none', height=18, state='disabled')
	output.pack(side='left', fill='both', expand=True)

	scrollbar = tk.Scrollbar(frame, command=output.yview)
	scrollbar.pack(side='right', fill='y')
	output.config(yscrollcommand=scrollbar.set)

	btn_frame = tk.Frame(root)
	btn_frame.pack(fill='x', padx=8, pady=(0,8))

	start_btn = tk.Button(btn_frame, text='Start Fix', width=12, command=lambda: on_start(output, start_btn))
	start_btn.pack(side='left')

	flush_btn = tk.Button(btn_frame, text='Run DNS Flush (After File Deletion)', width=28, command=lambda: run_dns_flush(output))
	flush_btn.pack(side='left', padx=(8,0))

	exit_btn = tk.Button(btn_frame, text='Exit', width=12, command=root.destroy)
	exit_btn.pack(side='right')

	append_output(output, f"Target folder: {STEAM_PATH}")
	append_output(output, "Note: This tool will delete files/folders under the target folder except for 'steamapps', 'userdata' and 'steam.exe'.")
	append_output(output, "Please ensure you have a backup and run with appropriate permissions.")

	root.mainloop()


if __name__ == '__main__':
	build_ui()

