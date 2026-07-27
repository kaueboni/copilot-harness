from app.db.connection import get_connection


def test_get_connection_enables_wal_mode(tmp_path):
    db_path = tmp_path / "test.db"
    conn = get_connection(db_path)
    try:
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert mode.lower() == "wal"
    finally:
        conn.close()


def test_get_connection_sets_busy_timeout(tmp_path):
    db_path = tmp_path / "test.db"
    conn = get_connection(db_path)
    try:
        timeout = conn.execute("PRAGMA busy_timeout").fetchone()[0]
        assert timeout == 5000
    finally:
        conn.close()
