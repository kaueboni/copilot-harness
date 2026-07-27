from app.db.connection import get_connection
from app.db.migrate import migrate
from app.db.version_manager import activate, get_active, rollback


def _insert_dataset_version(db_path, version_id, layer="agregado"):
    conn = get_connection(db_path)
    try:
        conn.execute(
            "INSERT INTO dataset_versions "
            "(version_id, layer, created_at, row_count, status) "
            "VALUES (?, ?, '2026-07-01T00:00:00Z', 10, 'ready')",
            (version_id, layer),
        )
        conn.commit()
    finally:
        conn.close()


def test_activate_sets_active_version(tmp_path):
    db_path = tmp_path / "test.db"
    migrate(db_path)
    _insert_dataset_version(db_path, 1)

    activate("agregado", 1, db_path=db_path)

    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT version_id FROM active_version WHERE layer = 'agregado'"
        ).fetchone()
    finally:
        conn.close()
    assert row[0] == 1


def test_get_active_returns_current_version(tmp_path):
    db_path = tmp_path / "test.db"
    migrate(db_path)
    _insert_dataset_version(db_path, 1)

    activate("agregado", 1, db_path=db_path)

    assert get_active("agregado", db_path=db_path) == 1


def test_rollback_repoints_to_previous_version(tmp_path):
    db_path = tmp_path / "test.db"
    migrate(db_path)
    _insert_dataset_version(db_path, 1)
    _insert_dataset_version(db_path, 2)

    activate("agregado", 2, db_path=db_path)
    assert get_active("agregado", db_path=db_path) == 2

    rollback("agregado", 1, db_path=db_path)
    assert get_active("agregado", db_path=db_path) == 1


def test_rollback_preserves_reverted_version_in_dataset_versions(tmp_path):
    db_path = tmp_path / "test.db"
    migrate(db_path)
    _insert_dataset_version(db_path, 1)
    _insert_dataset_version(db_path, 2)

    activate("agregado", 2, db_path=db_path)
    rollback("agregado", 1, db_path=db_path)

    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT version_id FROM dataset_versions WHERE version_id = 2"
        ).fetchone()
    finally:
        conn.close()

    assert row is not None
    assert get_active("agregado", db_path=db_path) != 2
