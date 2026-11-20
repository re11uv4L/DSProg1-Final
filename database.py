
import sqlite3

DB_NAME = "google_repos.db"


def create_database():
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS repositories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            language TEXT,
            stars INTEGER
        )
    """)

    con.commit()
    con.close()


def save_repository(name, language, stars):
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()

    cur.execute("""
        INSERT INTO repositories (name, language, stars)
        VALUES (?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET
            language = excluded.language,
            stars = excluded.stars
    """, (name, language, stars))

    con.commit()
    con.close()


def show_repositories():
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()

    cur.execute("""
        SELECT name, language, stars
        FROM repositories
        ORDER BY stars DESC
    """)

    for row in cur.fetchall():
        print(row)

    con.close()