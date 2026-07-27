"""Testes de integracao do pipeline ponta a ponta (T14 - ING-11).

Cobrem o "Done when" de T14: execucao completa ativa a nova versao agregada, a view
`agregado_indicadores_ativo` reflete a versao ativa corrente, e o rollback preserva a
versao revertida (nao deletada) reapontando a view.
"""

from app.db import version_manager
from app.db.connection import get_connection
from app.db.migrate import migrate
from app.pipeline.run_ingestion import run_pipeline

FIXTURE_PATH = "tests/fixtures/reclamacoes_sample.csv"
CLOSED_PERIOD = "2026-06"


def _fetch_view_version_ids(db_path):
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT DISTINCT version_id FROM agregado_indicadores_ativo"
        ).fetchall()
    finally:
        conn.close()
    return {row[0] for row in rows}


def test_run_pipeline_activates_new_aggregated_version(tmp_path):
    db_path = tmp_path / "test.db"
    migrate(db_path)

    version_id = run_pipeline(FIXTURE_PATH, CLOSED_PERIOD, db_path=db_path)

    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT layer, status FROM dataset_versions WHERE version_id = ?",
            (version_id,),
        ).fetchone()
    finally:
        conn.close()

    assert row == ("agregado", "ready")
    assert version_manager.get_active("agregado", db_path=str(db_path)) == version_id


def test_agregado_indicadores_ativo_view_reflects_active_version(tmp_path):
    db_path = tmp_path / "test.db"
    migrate(db_path)

    version_id = run_pipeline(FIXTURE_PATH, CLOSED_PERIOD, db_path=db_path)

    view_version_ids = _fetch_view_version_ids(db_path)
    assert view_version_ids == {version_id}


def test_rollback_preserves_reverted_version_and_repoints_view(tmp_path):
    db_path = tmp_path / "test.db"
    migrate(db_path)

    first_version_id = run_pipeline(FIXTURE_PATH, CLOSED_PERIOD, db_path=db_path)
    second_version_id = run_pipeline(FIXTURE_PATH, CLOSED_PERIOD, db_path=db_path)
    assert second_version_id != first_version_id
    assert version_manager.get_active("agregado", db_path=str(db_path)) == second_version_id

    version_manager.rollback("agregado", first_version_id, db_path=str(db_path))

    assert version_manager.get_active("agregado", db_path=str(db_path)) == first_version_id
    assert _fetch_view_version_ids(db_path) == {first_version_id}

    conn = get_connection(db_path)
    try:
        second_still_present = conn.execute(
            "SELECT COUNT(*) FROM dataset_versions WHERE version_id = ?",
            (second_version_id,),
        ).fetchone()[0]
    finally:
        conn.close()
    assert second_still_present == 1
