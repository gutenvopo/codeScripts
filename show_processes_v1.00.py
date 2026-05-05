"""
Simple Tkinter app to show Steam-related processes.

Usage:
	python show_processes_v1.00.py

Requires: psutil (install with `pip install psutil`)

Click the "Show Steam Processes" button to list process name, PID, and status
for processes whose name or command line contains the substring "steam".
"""
import threading
import psutil
import tkinter as tk
from tkinter import ttk
import ctypes
import time


def find_steam_processes():
	results = []
	for proc in psutil.process_iter(['pid', 'name', 'status', 'cmdline']):
		try:
			info = proc.info
			name = (info.get('name') or '').lower()
			cmd = ' '.join(info.get('cmdline') or []).lower()
			if 'steam' in name or 'steam' in cmd:
				results.append((info.get('name') or '<unknown>', info.get('pid'), info.get('status')))
		except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
			continue
	return results


def find_steam_process_objs():
	procs = []
	for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
		try:
			info = proc.info
			name = (info.get('name') or '').lower()
			cmd = ' '.join(info.get('cmdline') or []).lower()
			if 'steam' in name or 'steam' in cmd:
				procs.append(proc)
		except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
			continue
	return procs


# Windows: send WM_CLOSE to top-level windows owned by pid
def send_wm_close(pid):
	user32 = ctypes.windll.user32
	WM_CLOSE = 0x0010

	@ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
	def _enum_proc(hwnd, lParam):
		pid_c = ctypes.c_ulong()
		user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid_c))
		if pid_c.value == lParam:
			# only visible windows
			if user32.IsWindowVisible(hwnd):
				user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
		return True

	try:
		user32.EnumWindows(_enum_proc, pid)
	except Exception:
		pass


class SteamProcessApp(ttk.Frame):
	def __init__(self, master=None):
		super().__init__(master)
		self.master = master
		self.master.title('Steam Processes')
		self.pack(fill='both', expand=True)
		self.create_widgets()

	def create_widgets(self):
		top = ttk.Frame(self)
		top.pack(fill='x', padx=8, pady=8)

		self.show_btn = ttk.Button(top, text='Show Steam Processes', command=self.on_show)
		self.show_btn.pack(side='left')

		self.clear_btn = ttk.Button(top, text='Clear', command=self.clear_output)
		self.clear_btn.pack(side='left', padx=(8,0))

		self.stop_btn = ttk.Button(top, text='Stop All Steam Processes', command=self.on_stop_all)
		self.stop_btn.pack(side='left', padx=(8,0))

		self.output = tk.Text(self, wrap='none', height=20)
		self.output.pack(fill='both', expand=True, padx=8, pady=(0,8))
		self.output.configure(state='disabled')

		# add simple monospace font for better alignment
		try:
			import tkinter.font as tkfont
			font = tkfont.nametofont('TkFixedFont')
			self.output.configure(font=font)
		except Exception:
			pass

		# bottom exit button
		bottom = ttk.Frame(self)
		bottom.pack(fill='x', padx=8, pady=(0,8))
		self.exit_btn = ttk.Button(bottom, text='Exit', command=self.on_exit)
		self.exit_btn.pack(side='right')

	def clear_output(self):
		self.output.configure(state='normal')
		self.output.delete('1.0', tk.END)
		self.output.configure(state='disabled')

	def on_show(self):
		# run scanning in background thread to avoid UI blocking
		self.show_btn.configure(state='disabled')
		threading.Thread(target=self._scan_and_display, daemon=True).start()

	def on_stop_all(self):
		# disable buttons and run stop routine in background
		self.show_btn.configure(state='disabled')
		self.stop_btn.configure(state='disabled')
		threading.Thread(target=self._stop_all_and_report, daemon=True).start()


	def _stop_all_and_report(self):
		procs = find_steam_process_objs()
		if not procs:
			self.master.after(0, lambda: self._display_text('No steam-related processes found to stop.\n'))
			self.master.after(0, lambda: self._set_buttons_enabled(True))
			return

		lines = []
		lines.append('Attempting graceful shutdown (WM_CLOSE) where possible...')
		for proc in procs:
			try:
				lines.append(f'Sending WM_CLOSE to PID {proc.pid} ({proc.name()})')
				send_wm_close(proc.pid)
			except Exception as e:
				lines.append(f'Failed to send WM_CLOSE to PID {getattr(proc, "pid", "?")}: {e}')

		self.master.after(0, lambda: self._display_text('\n'.join(lines) + '\n'))

		for proc in procs:
			try:
				# give process some time to exit cleanly
				proc.wait(timeout=10)
				self.master.after(0, lambda p=proc: self._append_text(f'PID {p.pid} exited cleanly.\n'))
			except psutil.TimeoutExpired:
				try:
					self.master.after(0, lambda p=proc: self._append_text(f'PID {p.pid} did not exit; sending terminate()...\n'))
					proc.terminate()
					try:
						proc.wait(timeout=3)
						self.master.after(0, lambda p=proc: self._append_text(f'PID {p.pid} terminated.\n'))
					except psutil.TimeoutExpired:
						self.master.after(0, lambda p=proc: self._append_text(f'PID {p.pid} still alive; killing (force)...\n'))
						try:
							proc.kill()
							proc.wait(timeout=3)
							self.master.after(0, lambda p=proc: self._append_text(f'PID {p.pid} killed.\n'))
						except Exception as e:
							self.master.after(0, lambda e=e, p=proc: self._append_text(f'Failed to kill PID {p.pid}: {e}\n'))
				except (psutil.NoSuchProcess, psutil.ZombieProcess):
					self.master.after(0, lambda p=proc: self._append_text(f'PID {p.pid} not found (already exited).\n'))
			except psutil.AccessDenied:
				self.master.after(0, lambda p=proc: self._append_text(f'Access denied when handling PID {p.pid}.\n'))

		self.master.after(0, lambda: self._set_buttons_enabled(True))


	def _set_buttons_enabled(self, enabled: bool):
		state = 'normal' if enabled else 'disabled'
		self.show_btn.configure(state=state)
		self.stop_btn.configure(state=state)


	def _append_text(self, text):
		self.output.configure(state='normal')
		self.output.insert(tk.END, text)
		self.output.see(tk.END)
		self.output.configure(state='disabled')

	def on_exit(self):
		try:
			self.master.destroy()
		except Exception:
			pass


	def _scan_and_display(self):
		results = find_steam_processes()
		# prepare text
		if not results:
			text = 'No steam-related processes found.\n'
		else:
			lines = []
			lines.append(f"{'Name':24} PID     Status")
			lines.append('-' * 50)
			for name, pid, status in results:
				lines.append(f"{name:24} {pid:<7} {status}")
			text = '\n'.join(lines) + '\n'

		# update UI on main thread
		self.master.after(0, lambda: self._display_text(text))

	def _display_text(self, text):
		self.output.configure(state='normal')
		self.output.delete('1.0', tk.END)
		self.output.insert(tk.END, text)
		self.output.configure(state='disabled')
		self.show_btn.configure(state='normal')


def main():
	root = tk.Tk()
	root.geometry('600x400')
	app = SteamProcessApp(master=root)
	root.mainloop()


if __name__ == '__main__':
	main()

