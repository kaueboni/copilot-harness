import sqlite3

import pytest

from app.db.connection import get_connection
from app.db.migrate import migrate


def test_migrate_creates_all_tables_and_view(tmp_path):
    db_path = tmp_path / "test.db"
    migrate(db_path)

    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table', 'view')"
        ).fetchall()
        names = {row[0] for row in rows}
    finally:
        conn.close()

    expected = {
        "ingestion_runs",
        "dataset_versions",
        "active_version",
        "bruto_reclamacoes",
        "tratado_reclamacoes",
        "agregado_indicadores_mensais",
        "agregado_indicadores_ativo",
    }
    assert expected.issubset(names)


def test_migrate_is_idempotent(tmp_path):
    db_path = tmp_path / "test.db"

    migrate(db_path)
    migrate(db_path)  # segunda chamada nao deve levantar erro

    conn = get_connection(db_path)
    try:
        count = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name = 'ingestion_runs'"
        ).fetchone()[0]
    finally:
        conn.close()
    assert count == 1


def test_schema_constraints_are_enforced(tmp_path):
    db_path = tmp_path / "test.db"
    migrate(db_path)

    conn = get_connection(db_path)
    try:
        # CHECK constraint em ingestion_runs.status
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO ingestion_runs "
                "(started_at, status, source_file_name, source_checksum) "
                "VALUES ('2026-07-01T00:00:00Z', 'invalid_status', 'file.csv', 'abc123')"
            )

        conn.execute(
            "INSERT INTO ingestion_runs "
            "(started_at, status, source_file_name, source_checksum) "
            "VALUES ('2026-07-01T00:00:00Z', 'success', 'file.csv', 'abc123')"
        )
        conn.execute(
            "INSERT INTO dataset_versions "
            "(layer, source_run_id, created_at, row_count, status) "
            "VALUES ('agregado', 1, '2026-07-01T00:00:00Z', 10, 'ready')"
        )
        conn.execute(
            "INSERT INTO agregado_indicadores_mensais "
            "(version_id, empresa_entidade_id, segmento, periodo, "
            "indice_solucao_oficial, indice_solucao_estrito, tempo_medio_resposta) "
            "VALUES (1, 1, 'telecom', '2026-06', 0.8, 0.7, 5.0)"
        )
        conn.commit()

        # UNIQUE constraint em agregado_indicadores_mensais
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO agregado_indicadores_mensais "
                "(version_id, empresa_entidade_id, segmento, periodo, "
                "indice_solucao_oficial, indice_solucao_estrito, tempo_medio_resposta) "
                "VALUES (1, 1, 'telecom', '2026-06', 0.9, 0.8, 4.0)"
            )
    finally:
        conn.close()
