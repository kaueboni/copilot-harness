from datetime import UTC, datetime

import pytest

from app.aggregation.indicators import calculate, is_month_closed
from app.curation.treated_layer import store_treated
from app.db.connection import get_connection
from app.db.migrate import migrate
from app.ingestion.raw_layer import store_raw

FIXTURE_PATH = "tests/fixtures/reclamacoes_sample.csv"
# mes fechado / mes em andamento do fixture (ver scripts/generate_fixture.py golden data)
CLOSED_PERIOD = "2026-06"
OPEN_PERIOD = "2026-07"


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


def _indicators_by_segmento(db_path, version_id, segmento):
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT indice_solucao_oficial, indice_solucao_estrito, "
            "tempo_medio_resposta, nota_media FROM agregado_indicadores_mensais "
            "WHERE version_id = ? AND segmento = ?",
            (version_id, segmento),
        ).fetchone()
    finally:
        conn.close()
    return row


def test_calculate_indice_solucao_oficial_matches_golden_data(tmp_path):
    db_path = tmp_path / "test.db"
    migrate(db_path)
    treated_version_id = _store_fixture_as_treated(db_path)

    version_id = calculate(treated_version_id, CLOSED_PERIOD, db_path=db_path)

    # Empresa X, Telecomunicacoes: 2 de 3 reclamacoes resolvidas -> 2/3
    row = _indicators_by_segmento(db_path, version_id, "Telecomunicacoes")
    assert row[0] == pytest.approx(2 / 3, abs=1e-4)


def test_calculate_indice_solucao_estrito_matches_golden_data(tmp_path):
    db_path = tmp_path / "test.db"
    migrate(db_path)
    treated_version_id = _store_fixture_as_treated(db_path)

    version_id = calculate(treated_version_id, CLOSED_PERIOD, db_path=db_path)

    # Fixture nao tem status "nao avaliado" no mes fechado, entao estrito == oficial (2/3)
    row = _indicators_by_segmento(db_path, version_id, "Telecomunicacoes")
    assert row[1] == pytest.approx(2 / 3, abs=1e-4)


def test_calculate_tempo_medio_resposta_e_nota_media_matches_golden_data(tmp_path):
    db_path = tmp_path / "test.db"
    migrate(db_path)
    treated_version_id = _store_fixture_as_treated(db_path)

    version_id = calculate(treated_version_id, CLOSED_PERIOD, db_path=db_path)

    telecom_row = _indicators_by_segmento(db_path, version_id, "Telecomunicacoes")
    varejo_row = _indicators_by_segmento(db_path, version_id, "Varejo")

    # Empresa X: tempo_medio (4+7+10)/3 = 7.0, nota_media (8+6)/2 = 7.0
    assert telecom_row[2] == pytest.approx(7.0, abs=1e-4)
    assert telecom_row[3] == pytest.approx(7.0, abs=1e-4)
    # Empresa Y: tempo_medio 3.0, nota_media 9.0
    assert varejo_row[2] == pytest.approx(3.0, abs=1e-4)
    assert varejo_row[3] == pytest.approx(9.0, abs=1e-4)


def test_calculate_refuses_open_month_with_explicit_error(tmp_path):
    db_path = tmp_path / "test.db"
    migrate(db_path)
    treated_version_id = _store_fixture_as_treated(db_path)

    assert is_month_closed(OPEN_PERIOD) is False

    with pytest.raises(ValueError):
        calculate(treated_version_id, OPEN_PERIOD, db_path=db_path)
