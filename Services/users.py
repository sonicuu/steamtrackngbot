import sqlite3
import threading

# Данные, специфичные для потока, для хранения соединения с базой данных
local_data = threading.local()

def get_db_connection():
    if not hasattr(local_data, 'connection'):
        local_data.connection = sqlite3.connect('users.db', check_same_thread=False)
    return local_data.connection

class Users:
    def __init__(self):
        self.conn = get_db_connection()
        self.cursor = self.conn.cursor()
        self.setup_database()

    def setup_database(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                chat_id INTEGER PRIMARY KEY,
                steam_id TEXT,
                selected_game TEXT,
                selected_items TEXT
            )
        ''')
        self.conn.commit()

    def save_user_data(self, chat_id, steam_id, selected_game, selected_items):
        self.cursor.execute('''
            INSERT OR REPLACE INTO users (chat_id, steam_id, selected_game, selected_items)
            VALUES (?, ?, ?, ?)
        ''', (chat_id, steam_id, selected_game, selected_items))
        self.conn.commit()

    def get_user_data(self, chat_id):
        self.cursor.execute('SELECT * FROM users WHERE chat_id = ?', (chat_id,))
        row = self.cursor.fetchone()
        if row:
            return row[1], row[2], row[3].split(',')
        return None, None, []

# Пример использования
serviceUser = Users()
