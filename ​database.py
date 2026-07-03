import sqlite3
import json

DB_NAME = "logocraft.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Configuration tracker
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            user_id INTEGER PRIMARY KEY,
            style TEXT DEFAULT 'Modern',
            premium_hd INTEGER DEFAULT 0
        )
    ''')
    # History logs tracker
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            brand_name TEXT,
            prompt TEXT,
            image_url TEXT,
            is_favorite INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def get_preferences(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT style, premium_hd FROM user_preferences WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"style": row[0], "premium_hd": bool(row[1])}
    return {"style": "Modern", "premium_hd": False}

def update_preference(user_id: int, column: str, value):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO user_preferences (user_id) VALUES (?)", (user_id,))
    cursor.execute(f"UPDATE user_preferences SET {column} = ? WHERE user_id = ?", (value, user_id))
    conn.commit()
    conn.close()

def log_generation(user_id: int, brand_name: str, prompt: str, image_url: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO history (user_id, brand_name, prompt, image_url) VALUES (?, ?, ?, ?)",
                   (user_id, brand_name, prompt, image_url))
    conn.commit()
    conn.close()

def get_history(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT brand_name, style, prompt FROM history WHERE user_id = ? ORDER BY id DESC LIMIT 5", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

