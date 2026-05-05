import tkinter as tk
import winsound
import sys

def produce_output():
    # Play a Windows system sound (task complete/asterisk)
    try:
        winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
    except Exception:
        try:
            winsound.MessageBeep()
        except Exception:
            pass

    # Open a second small window that says "hello world"
    top = tk.Toplevel(root)
    top.title("hello")
    top.geometry("200x100")
    lbl = tk.Label(top, text="hello world", font=("Segoe UI", 12))
    lbl.pack(expand=True, pady=20)

    # Make sure the toplevel is on top briefly
    top.lift()
    top.attributes('-topmost', True)
    top.after(500, lambda: top.attributes('-topmost', False))

def on_exit():
    root.destroy()
    sys.exit(0)

if __name__ == '__main__':
    root = tk.Tk()
    root.title("windows button test for Kwa")
    root.geometry("320x120")

    frm = tk.Frame(root)
    frm.pack(expand=True)

    btn_prod = tk.Button(frm, text="Produce output", width=20, command=produce_output)
    btn_prod.grid(row=0, column=0, padx=10, pady=12)

    btn_exit = tk.Button(frm, text="Exit", width=10, command=on_exit)
    btn_exit.grid(row=0, column=1, padx=10, pady=12)

    root.mainloop()
