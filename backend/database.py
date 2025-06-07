import sqlite3

DB_FILE = "db.sqlite3"


def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "CREATE TABLE IF NOT EXISTS documents (id TEXT PRIMARY KEY, filename TEXT)"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS chunks (doc_id TEXT, chunk_index INTEGER, text TEXT)"
    )
    conn.commit()
    conn.close()


def store_chunks(doc_id: str, filename: str, chunks: list[str]):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO documents (id, filename) VALUES (?, ?)",
        (doc_id, filename),
    )
    for i, chunk in enumerate(chunks):
        c.execute(
            "INSERT INTO chunks (doc_id, chunk_index, text) VALUES (?, ?, ?)",
            (doc_id, i, chunk),
        )
    conn.commit()
    conn.close()


def get_chunk(doc_id: str, chunk_index: int) -> str | None:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "SELECT text FROM chunks WHERE doc_id = ? AND chunk_index = ?",
        (doc_id, chunk_index),
    )
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

