"""Aplica o schema SQL (schema.sql) de forma idempotente sobre o analytics.db."""

from pathlib import Path

from app.db.connection import DEFAULT_DB_PATH, get_connection

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def migrate(db_path: str | Path = DEFAULT_DB_PATH) -> None:
    """Cria (se necessario) todas as tabelas/views do schema no banco indicado."""
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn = get_connection(db_path)
    try:
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
