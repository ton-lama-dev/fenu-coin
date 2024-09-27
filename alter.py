import sqlite3


def connect_db():
    return sqlite3.connect("data.db")


def alter():
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("ALTER TABLE users ADD COLUMN paid_balance INTEGER DEFAULT 0")
        conn.commit()


alter()
