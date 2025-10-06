import sqlite3
import bcrypt
import os

MAX_USERS = 10

# # Determine base directory for persistent storage
# if getattr(sys, "frozen", False):
#     # Running as PyInstaller executable
#     BASE_DIR = os.path.join(os.path.expanduser("~"), "MyLoginAppData")
#     os.makedirs(BASE_DIR, exist_ok=True)  # create folder if it doesn't exist
# else:
#     # Running as Python script
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_FILE = os.path.join(BASE_DIR, "users.db")

def init_db():  
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                 userID INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT UNIQUE NOT NULL,
                 password_hash TEXT NOT NULL
                 )""")
    conn.commit()
    conn.close()

def get_user_count():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) AS [Number of Users] FROM users")
    count = c.fetchone()[0]
    conn.close()
    return count

def add_user(username, password):
    if get_user_count() >= MAX_USERS:
        raise ValueError("Maximum number of users (10) reached.")

    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    conn = sqlite3.connect(DB_FILE) 
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash.decode()))
        conn.commit()
    except sqlite3.IntegrityError:
        raise ValueError("Username already exists.")
    finally:
        conn.close()
        print(DB_FILE)

def check_login(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    return row is not None and bcrypt.checkpw(password.encode('utf-8'), row[0].encode('utf-8'))

def clear_users():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM users")
    conn.commit()
    conn.close()