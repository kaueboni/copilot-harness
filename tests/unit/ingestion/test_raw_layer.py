from datetime import UTC, datetime

from app.db.connection import get_connection
from app.db.migrate import migrate
from app.ingestion.raw_layer import store_raw

FIXTURE_PATH = "tests/fixtures/reclamacoes_sample.csv"


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


def test_store_raw_writes_rows_unchanged_into_bruto_reclamacoes(tmp_path):
    db_path = tmp_path / "test.db"
    migrate(db_path)
    run_id = _insert_ingestion_run(db_path)

    version_id = store_raw(FIXTURE_PATH, run_id, db_path=db_path)

    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT empresa_nome_raw, segmento, assunto, uf, data_abertura, "
            "data_resposta, resultado, nota_satisfacao "
            "FROM bruto_reclamacoes WHERE version_id = ? ORDER BY rowid",
            (version_id,),
        ).fetchall()
    finally:
        conn.close()

    # o fixture tem 6 linhas, incluindo a duplicata exata -> camada bruta grava
    # todas as 6 sem descartar nada (dedupe e responsabilidade da camada tratada)
    assert len(rows) == 6
    assert rows[0] == (
        "Empresa X S.A.",
        "Telecomunicacoes",
        "Cobranca indevida",
        "SP",
        "2026-06-01",
        "2026-06-05",
        "Resolvido",
        8.0,
    )
    # linha sem nota_satisfacao preenchida deve permanecer nula, nao inventada
    assert rows[3][-1] is None


def test_store_raw_creates_dataset_version_with_correct_row_count(tmp_path):
    db_path = tmp_path / "test.db"
    migrate(db_path)
    run_id = _insert_ingestion_run(db_path)

    version_id = store_raw(FIXTURE_PATH, run_id, db_path=db_path)

    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT layer, row_count, status, source_run_id FROM dataset_versions "
            "WHERE version_id = ?",
            (version_id,),
        ).fetchone()
    finally:
        conn.close()

    assert row == ("bruto", 6, "ready", run_id)


def test_store_raw_updates_ingestion_run_metadata(tmp_path):
    db_path = tmp_path / "test.db"
    migrate(db_path)
    run_id = _insert_ingestion_run(db_path)

    store_raw(FIXTURE_PATH, run_id, db_path=db_path)

    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT status, row_count, finished_at, source_checksum "
            "FROM ingestion_runs WHERE run_id = ?",
            (run_id,),
        ).fetchone()
    finally:
        conn.close()

    status, row_count, finished_at, source_checksum = row
    assert status == "success"
    assert row_count == 6
    assert finished_at is not None
    assert len(source_checksum) == 64  # sha256 hexdigest


def test_store_raw_reingestion_of_same_period_creates_new_version_without_overwrite(
    tmp_path,
):
    db_path = tmp_path / "test.db"
    migrate(db_path)
    run_id_1 = _insert_ingestion_run(db_path)
    run_id_2 = _insert_ingestion_run(db_path)

    version_id_1 = store_raw(FIXTURE_PATH, run_id_1, db_path=db_path)
    version_id_2 = store_raw(FIXTURE_PATH, run_id_2, db_path=db_path)

    assert version_id_1 != version_id_2

    conn = get_connection(db_path)
    try:
        version_count = conn.execute(
            "SELECT COUNT(*) FROM dataset_versions WHERE layer = 'bruto'"
        ).fetchone()[0]
        rows_v1 = conn.execute(
            "SELECT COUNT(*) FROM bruto_reclamacoes WHERE version_id = ?",
            (version_id_1,),
        ).fetchone()[0]
        rows_v2 = conn.execute(
            "SELECT COUNT(*) FROM bruto_reclamacoes WHERE version_id = ?",
            (version_id_2,),
        ).fetchone()[0]
    finally:
        conn.close()

    assert version_count == 2
    assert rows_v1 == 6
    assert rows_v2 == 6
