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
        launch_main_interface(user)  # Launch main DCM interface
    else:
        messagebox.showerror("Login", "Invalid credentials")

def launch_main_interface(username):
    main_root = tk.Tk()
    from gui.main_interface import DCMMainInterface
    DCMMainInterface(main_root, username)
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

    # Username entry field
    root = tk.Tk()
    tk.Label(root, text="Username").pack()
    username_entry = tk.Entry(root)
    username_entry.pack()

    # Password entry field
    tk.Label(root, text="Password").pack()
    password_entry = tk.Entry(root, show="*")
    password_entry.pack()

    # Button Inputs
    # 'lambda' is required to run the function with parameters on button press
    tk.Button(root, text="Login", command=lambda: attempt_login(username_entry.get(), password_entry.get(), root)).pack() 
    tk.Button(root, text="Register", command=lambda: attempt_register(username_entry.get(), password_entry.get())).pack()
    tk.Button(root, text="Clear Users", command=clearing_users).pack() # 'lambda' not needed because there are no parameters

    root.mainloop()

if __name__ == "__main__":
    main()