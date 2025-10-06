from auth.auth import init_db, check_login, add_user, clear_users
import tkinter as tk
from tkinter import messagebox

def attempt_login(user, pwd):
    if (user != '') and (pwd != '') and check_login(user, pwd):
        messagebox.showinfo("Login", f"Welcome {user}!")
    else:
        messagebox.showerror("Login", "Invalid credentials")

def attempt_register(user, pwd):
    try:
        if (user != '') and (pwd != ''):
            add_user(user, pwd)
            messagebox.showinfo("Registration", f"{user} registered sucessful")
        else:
            messagebox.showerror("Registration", "Invalid credentials")
    except ValueError as e:
        messagebox.showerror("Registration", str(e))

def clearing_users():
    if messagebox.askyesno("Clear Users", "Are You Sure?"):
        clear_users()
        messagebox.showinfo("Clear Users", "Clear Users from Database")

def main():
    init_db()

    root = tk.Tk()
    tk.Label(root, text="Username").pack()
    username_entry = tk.Entry(root)
    username_entry.pack()

    tk.Label(root, text="Password").pack()
    password_entry = tk.Entry(root, show="*")
    password_entry.pack()

    tk.Button(root, text="Login", command=lambda: attempt_login(username_entry.get(), password_entry.get())).pack()
    tk.Button(root, text="Register", command=lambda: attempt_register(username_entry.get(), password_entry.get())).pack()
    tk.Button(root, text="Drop Database", command=clearing_users).pack() # Change 'Drop Database' to 'Clear Users'

    root.mainloop()

if __name__ == "__main__":
    main()