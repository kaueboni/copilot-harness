"""Helper de conexao com o SQLite (analytics.db).

Configura WAL mode e busy_timeout para permitir leitores concorrentes durante a
ingestao (ver design.md - Tech Decisions).
"""

import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path("analytics.db")
BUSY_TIMEOUT_MS = 5000


def get_connection(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Abre uma conexao ao SQLite com journal_mode=WAL e busy_timeout configurados."""
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(f"PRAGMA busy_timeout={BUSY_TIMEOUT_MS}")
    return conn
