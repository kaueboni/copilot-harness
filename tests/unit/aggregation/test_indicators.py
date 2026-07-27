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


def _store_treated_version_with_rows(db_path, rows):
    """Cria uma versao tratada sintetica (sem passar pelo pipeline bruto/T5) para
    exercitar diretamente a agregacao com dados de teste isolados."""
    conn = get_connection(db_path)
    try:
        now = datetime.now(UTC).isoformat()
        cursor = conn.execute(
            "INSERT INTO dataset_versions (layer, created_at, row_count, status) "
            "VALUES ('tratado', ?, ?, 'ready')",
            (now, len(rows)),
        )
        treated_version_id = cursor.lastrowid
        conn.executemany(
            "INSERT INTO tratado_reclamacoes "
            "(version_id, empresa_entidade_id, segmento, data_abertura, data_resposta, "
            "resultado, nota_satisfacao) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [(treated_version_id, *row) for row in rows],
        )
        conn.commit()
    finally:
        conn.close()
    return treated_version_id


def test_calculate_indice_oficial_and_estrito_diverge_with_inconclusive_resultado(
    tmp_path,
):
    db_path = tmp_path / "test.db"
    migrate(db_path)

    # 3 reclamacoes no mes fechado: 1 Resolvido, 1 Nao Resolvido, 1 com resultado
    # inconclusivo ("Em Analise") - nao presente no fixture golden de T5.
    treated_version_id = _store_treated_version_with_rows(
        db_path,
        [
            (1, "Telecomunicacoes", f"{CLOSED_PERIOD}-01", f"{CLOSED_PERIOD}-05", "Resolvido", 8),
            (
                1,
                "Telecomunicacoes",
                f"{CLOSED_PERIOD}-02",
                f"{CLOSED_PERIOD}-06",
                "Nao Resolvido",
                4,
            ),
            (1, "Telecomunicacoes", f"{CLOSED_PERIOD}-03", f"{CLOSED_PERIOD}-07", "Em Analise", 5),
        ],
    )

    version_id = calculate(treated_version_id, CLOSED_PERIOD, db_path=db_path)

    row = _indicators_by_segmento(db_path, version_id, "Telecomunicacoes")
    # oficial conta "Resolvido" + o valor inconclusivo como resolvida -> 2/3
    assert row[0] == pytest.approx(2 / 3, abs=1e-4)
    # estrito conta apenas "Resolvido" como resolvida -> 1/3
    assert row[1] == pytest.approx(1 / 3, abs=1e-4)
    assert row[0] != row[1]

