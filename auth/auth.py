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

# Determine database file directory
DB_FILE = os.path.join(BASE_DIR, "data", "users.db")

# Create users database table if doesn't already exists
def init_db():  
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # INTEGER 'userID' AUTOINCREMENTS and counts the number of users in the table
    #       as the PRIMARY KEY, each user will have a UNIQUE 'userID' and cannot be NULL
    # 'username' and 'password' are TEXT fields and cannot be NULL
    # each stored 'username' must be UNIQUE from each other, but different users can have the same 'password'
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                 userID INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT UNIQUE NOT NULL,
                 password_hash TEXT NOT NULL
                 )""")
    conn.commit()
    conn.close()

# Count the number of users stored in users.db
def get_user_count():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) AS [Number of Users] FROM users")
    count = c.fetchone()[0]
    conn.close()
    return count

# Add entered username and password to users.db
def add_user(username, password):
    # raise error if there is already 10 users
    if get_user_count() >= MAX_USERS:
        raise ValueError("Maximum number of users (10) reached.")

    # hash password (for security)
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    conn = sqlite3.connect(DB_FILE) 
    c = conn.cursor()
    # attempt to insert the username and hashed password of the new user into users.db
    try:
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash.decode()))
        conn.commit()
    # since username must be unique, if the entered username already exists in users.db
    # it will raise an IntegrityError
    except sqlite3.IntegrityError:
        raise ValueError("Username already exists.")
    finally:
        conn.close()

# Verify the user attemping to login
def check_login(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # get the hashed password of the user with the matching username in users.db
    c.execute("SELECT password_hash FROM users WHERE username = ?", (username,)) # the placeholder is expecting a tuple
    row = c.fetchone()
    conn.close()
    # row is None if a matching username was not found
    # checkpw is false if the entered and stored hashed passwords don't match
    return row is not None and bcrypt.checkpw(password.encode('utf-8'), row[0].encode('utf-8'))

# Remove all users from users.db
def clear_users():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM users")
    conn.commit()
    conn.close()