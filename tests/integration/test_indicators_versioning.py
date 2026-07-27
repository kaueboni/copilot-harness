from datetime import UTC, datetime

from app.aggregation.indicators import calculate
from app.curation.treated_layer import store_treated
from app.db.connection import get_connection
from app.db.migrate import migrate
from app.ingestion.raw_layer import store_raw

FIXTURE_PATH = "tests/fixtures/reclamacoes_sample.csv"
CLOSED_PERIOD = "2026-06"


def _insert_ingestion_run(db_path, source_file_name="reclamacoes_sample.csv"):
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            "INSERT INTO ingestion_runs (started_at, status, source_file_name, source_checksum) "
            "VALUES (?, 'running', ?, '')",
            (datetime.now(UTC).isoformat(), source_file_name),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def _store_fixture_as_treated(db_path):
    run_id = _insert_ingestion_run(db_path)
    bruto_version_id = store_raw(FIXTURE_PATH, run_id, db_path=db_path)
    return store_treated(bruto_version_id, db_path=db_path)


def _fetch_indicator_rows(db_path, version_id):
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT empresa_entidade_id, segmento, indice_solucao_oficial, "
            "indice_solucao_estrito, tempo_medio_resposta, nota_media "
            "FROM agregado_indicadores_mensais WHERE version_id = ? "
            "ORDER BY empresa_entidade_id, segmento",
            (version_id,),
        ).fetchall()
    finally:
        conn.close()
    return rows


def test_calculate_creates_new_dataset_version_with_agregado_lineage(tmp_path):
    db_path = tmp_path / "test.db"
    migrate(db_path)
    treated_version_id = _store_fixture_as_treated(db_path)

    version_id = calculate(treated_version_id, CLOSED_PERIOD, db_path=db_path)

    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT layer, source_version_id, status FROM dataset_versions "
            "WHERE version_id = ?",
            (version_id,),
        ).fetchone()
    finally:
        conn.close()

    assert row == ("agregado", treated_version_id, "ready")


def test_calculate_twice_on_same_treated_version_is_reproducible(tmp_path):
    db_path = tmp_path / "test.db"
    migrate(db_path)
    treated_version_id = _store_fixture_as_treated(db_path)

    first_version_id = calculate(treated_version_id, CLOSED_PERIOD, db_path=db_path)
    second_version_id = calculate(treated_version_id, CLOSED_PERIOD, db_path=db_path)

    assert first_version_id != second_version_id
    first_rows = _fetch_indicator_rows(db_path, first_version_id)
    second_rows = _fetch_indicator_rows(db_path, second_version_id)
    assert first_rows == second_rows


def test_calculate_preserves_previous_aggregated_version_after_new_run(tmp_path):
    db_path = tmp_path / "test.db"
    migrate(db_path)
    treated_version_id = _store_fixture_as_treated(db_path)

    first_version_id = calculate(treated_version_id, CLOSED_PERIOD, db_path=db_path)
    first_rows_before = _fetch_indicator_rows(db_path, first_version_id)

    calculate(treated_version_id, CLOSED_PERIOD, db_path=db_path)

    first_rows_after = _fetch_indicator_rows(db_path, first_version_id)
    assert first_rows_before == first_rows_after
