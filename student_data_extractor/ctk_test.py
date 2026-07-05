import customtkinter as ctk
print("import ok")
app = ctk.CTk()
print("CTk created")
app.geometry("300x200")
ctk.CTkLabel(app, text="It works").pack(pady=50)
print("about to mainloop")
app.mainloop()
print("mainloop returned")