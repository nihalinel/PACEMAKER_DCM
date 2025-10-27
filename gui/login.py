from auth.auth import init_db, check_login, add_user, clear_users
import tkinter as tk
from tkinter import messagebox

# Attempt to login with entered username and password
def attempt_login(user, pwd, root):
    # if neither username or password entry fields are empty
    # and there is a matching username and password
    if (user != '') and (pwd != '') and check_login(user, pwd):
        messagebox.showinfo("Login", f"Welcome {user}!")
        root.destroy()  # Close login window
        launch_patient_select(user)  # Launch main DCM interface
    else:
        messagebox.showerror("Login", "Invalid credentials")

def launch_patient_select(username):
    main_root = tk.Tk()
    from gui.patient_select import PatientSelectApp
    PatientSelectApp(main_root, username)
    main_root.mainloop()

# Attempt to register new user with entered username and password
def attempt_register(user, pwd):
    try:
        # if neither username or pass entry fields are empty
        if (user != '') and (pwd != ''):
            add_user(user, pwd)
            messagebox.showinfo("Registration", f"{user} registered sucessful")
        else:
            messagebox.showerror("Registration", "Invalid credentials")
    # if a ValueError is raise {max users, duplicate user}
    except ValueError as e:
        messagebox.showerror("Registration", str(e))

# Clear all users from users.db
def clearing_users():
    # confirmation messagebox
    if messagebox.askyesno("Clear Users", "Are You Sure?"):
        clear_users()
        messagebox.showinfo("Clear Users", "Clear Users from Database")

def main():
    init_db() # initialize users.db

    root = tk.Tk()
    root.title("DCM Login")
    root.geometry("400x300")  # Larger, more comfortable window
    root.resizable(False, False)

    font_style = ("Arial", 9)  # Match your main interface font

    # Use a centered frame for layout
    frame = tk.Frame(root, padx=20, pady=20)
    frame.place(relx=0.5, rely=0.5, anchor="center")

    # Username
    tk.Label(frame, text="Username:", font=font_style).grid(row=0, column=0, sticky="w", pady=(0, 10))
    username_entry = tk.Entry(frame, width=30, font=font_style)
    username_entry.grid(row=0, column=1, pady=(0, 10))

    # Password
    tk.Label(frame, text="Password:", font=font_style).grid(row=1, column=0, sticky="w", pady=(0, 20))
    password_entry = tk.Entry(frame, show="*", width=30, font=font_style)
    password_entry.grid(row=1, column=1, pady=(0, 20))

    # Buttons (Login & Register side by side)
    btn_frame = tk.Frame(frame)
    btn_frame.grid(row=2, column=0, columnspan=2)

    # 'lambda' is required to run the function with parameters on button press
    tk.Button(
        btn_frame, text="Login", width=12, 
        command=lambda: attempt_login(username_entry.get(), password_entry.get(), root)
    ).pack(side="left", padx=10)

    tk.Button(
        btn_frame, text="Register", width=12, 
        command=lambda: attempt_register(username_entry.get(), password_entry.get())
    ).pack(side="left", padx=10)

    tk.Button(root, text="Clear Users", font=font_style, width = 11, command=clearing_users).pack(pady=(220, 10))

    # (Optional) Keyboard focus
    username_entry.focus()

    root.mainloop()

if __name__ == "__main__":
    main()