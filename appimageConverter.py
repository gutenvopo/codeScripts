import tkinter as tk
from tkinter import simpledialog

root = tk.Tk()
root.withdraw()  # Hide the main window

name = simpledialog.askstring("Input", "What is your name?")
if name:
    print(f"Your name is: {name}")
else:
    print("No name provided.")