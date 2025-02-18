import sqlite3


class Database:
    def __init__(self, db_file="data/database.db"):
        self.db_file = db_file
        self._ensure_table_exists()

    def _ensure_table_exists(self):
        """Создает таблицу, если её еще нет."""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS players (
                tg_id INTEGER PRIMARY KEY,
                nick TEXT
            )
        """)
        conn.commit()
        conn.close()

    def save_nickname(self, tg_id, nick):
        """Сохраняет или обновляет ник для указанного telegram_id."""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO players (tg_id, nick) VALUES (?, ?)", (tg_id, nick))
        conn.commit()
        conn.close()

    def get_nickname(self, tg_id):
        """Возвращает ник для указанного telegram_id или None, если запись отсутствует."""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute("SELECT nick FROM players WHERE tg_id = ?", (tg_id,))
        row = c.fetchone()
        conn.close()
        return row[0] if row else None
