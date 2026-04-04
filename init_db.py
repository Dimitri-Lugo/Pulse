import sqlite3

def setup_database():
    # Connect to SQLite (this automatically creates pulse.db if it doesn't exist)
    conn = sqlite3.connect('pulse.db')
    cursor = conn.cursor()

    # Create the USERS table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create the PORTFOLIOS table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS portfolios (
            asset_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            ticker TEXT NOT NULL,
            amount REAL NOT NULL,
            added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    conn.commit()
    conn.close()
    print("Success: Pulse database and tables initialized.")

if __name__ == "__main__":
    setup_database()