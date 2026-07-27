from datetime import UTC, datetime

from app.curation.treated_layer import get_review_queue, store_treated
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


def _store_fixture_as_bruto(db_path):
    run_id = _insert_ingestion_run(db_path)
    return store_raw(FIXTURE_PATH, run_id, db_path=db_path)


def _insert_bruto_version(db_path, rows):
    """Cria uma versao bruta sintetica com `rows` (tuplas nas colunas de bruto_reclamacoes)."""
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            "INSERT INTO dataset_versions (layer, created_at, row_count, status) "
            "VALUES ('bruto', '2026-07-01T00:00:00Z', ?, 'ready')",
            (len(rows),),
        )
        version_id = cursor.lastrowid
        conn.executemany(
            "INSERT INTO bruto_reclamacoes "
            "(version_id, empresa_nome_raw, segmento, assunto, uf, "
            "data_abertura, data_resposta, resultado, nota_satisfacao) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(version_id, *row) for row in rows],
        )
        conn.commit()
        return version_id
    finally:
        conn.close()


def test_store_treated_removes_exact_duplicate_keeping_one_occurrence(tmp_path):
    db_path = tmp_path / "test.db"
    migrate(db_path)
    bruto_version_id = _store_fixture_as_bruto(db_path)

    treated_version_id = store_treated(bruto_version_id, db_path=db_path)

    conn = get_connection(db_path)
    try:
        row_count = conn.execute(
            "SELECT COUNT(*) FROM tratado_reclamacoes WHERE version_id = ?",
            (treated_version_id,),
        ).fetchone()[0]
    finally:
        conn.close()

    # fixture tem 6 linhas com 1 duplicata exata -> tratado deve ter 5
    assert row_count == 5


def test_store_treated_assigns_same_entity_id_to_company_name_variants(tmp_path):
    db_path = tmp_path / "test.db"
    migrate(db_path)
    bruto_version_id = _store_fixture_as_bruto(db_path)

    treated_version_id = store_treated(bruto_version_id, db_path=db_path)

    conn = get_connection(db_path)
    try:
        rows_by_assunto = dict(
            conn.execute(
                "SELECT assunto, empresa_entidade_id FROM tratado_reclamacoes "
                "WHERE version_id = ?",
                (treated_version_id,),
            ).fetchall()
        )
    finally:
        conn.close()

    # "Empresa X S.A." (Cobranca indevida) e "EMPRESA X SA" (Atraso na entrega)
    # sao a mesma empresa apos o fuzzy match
    assert rows_by_assunto["Cobranca indevida"] == rows_by_assunto["Atraso na entrega"]
    # "Empresa Y Ltda" (Entrega atrasada) e uma entidade claramente distinta
    assert rows_by_assunto["Entrega atrasada"] != rows_by_assunto["Cobranca indevida"]


def test_store_treated_creates_new_version_with_source_lineage_to_bruto(tmp_path):
    db_path = tmp_path / "test.db"
    migrate(db_path)
    bruto_version_id = _store_fixture_as_bruto(db_path)

    treated_version_id = store_treated(bruto_version_id, db_path=db_path)

    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT layer, source_version_id, row_count, status FROM dataset_versions "
            "WHERE version_id = ?",
            (treated_version_id,),
        ).fetchone()
    finally:
        conn.close()

    assert row == ("tratado", bruto_version_id, 5, "ready")


def test_store_treated_review_queue_is_accessible_after_processing(tmp_path):
    db_path = tmp_path / "test.db"
    migrate(db_path)
    # "Banco do Brasil S.A." vs "Banco Brasil SA" -> mesma chave de blocking ("banco"),
    # score ~88 (faixa 80-91) - par ambiguo que deve ir para a fila de revisao
    rows = [
        (
            "Banco do Brasil S.A.",
            "Bancario",
            "Tarifa indevida",
            "SP",
            "2026-06-01",
            "2026-06-05",
            "Resolvido",
            7.0,
        ),
        (
            "Banco Brasil SA",
            "Bancario",
            "Conta bloqueada",
            "SP",
            "2026-06-02",
            "2026-06-06",
            "Resolvido",
            8.0,
        ),
    ]
    bruto_version_id = _insert_bruto_version(db_path, rows)

    treated_version_id = store_treated(bruto_version_id, db_path=db_path)

    review_queue = get_review_queue(treated_version_id)
    review_pairs = {frozenset((a, b)) for a, b, _ in review_queue}
    assert frozenset(("Banco do Brasil S.A.", "Banco Brasil SA")) in review_pairs
