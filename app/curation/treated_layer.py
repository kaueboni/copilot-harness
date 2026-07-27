"""Camada tratada (writer) - ING-04, ING-05, ING-06, ING-07.

Le a camada bruta de origem, aplica normalizacao de encoding/datas (T9) e fuzzy match
de empresa (T10), remove duplicatas exatas de reclamacao mantendo uma ocorrencia, e
grava `tratado_reclamacoes` com o `empresa_entidade_id` resolvido. Cria uma nova versao
em `dataset_versions` (layer='tratado') vinculada a versao bruta de origem via
`source_version_id` (ver design.md - Camada Tratada).

A amostra de revisao do fuzzy match (pares com score 80-91) nao tem tabela dedicada no
schema; fica disponivel em memoria por versao tratada via `get_review_queue`, atendendo
ING-07 (revisao amostral humana).
"""

from datetime import UTC, datetime
from pathlib import Path

from app.curation.company_matcher import match_companies
from app.curation.normalizer import normalize
from app.db.connection import DEFAULT_DB_PATH, get_connection

BRUTO_COLUMNS = [
    "empresa_nome_raw",
    "segmento",
    "assunto",
    "uf",
    "data_abertura",
    "data_resposta",
    "resultado",
    "nota_satisfacao",
]

_review_queues: dict[int, list[tuple[str, str, float]]] = {}


def get_review_queue(version_id: int) -> list[tuple[str, str, float]]:
    """Retorna a amostra de revisao (pares de nomes com score 80-91) da versao tratada."""
    return _review_queues.get(version_id, [])


def _read_bruto_rows(source_version_id: int, db_path: str | Path) -> list[dict]:
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            f"SELECT {', '.join(BRUTO_COLUMNS)} FROM bruto_reclamacoes "
            "WHERE version_id = ? ORDER BY rowid",
            (source_version_id,),
        ).fetchall()
    finally:
        conn.close()
    return [dict(zip(BRUTO_COLUMNS, row, strict=True)) for row in rows]


def _dedupe_exact(rows: list[dict]) -> list[dict]:
    seen = set()
    deduped = []
    for row in rows:
        key = tuple(row[col] for col in BRUTO_COLUMNS)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def store_treated(source_version_id: int, db_path: str | Path = DEFAULT_DB_PATH) -> int:
    """Processa a camada bruta `source_version_id` e grava a nova versao tratada.

    Retorna o `version_id` da versao tratada criada.
    """
    raw_rows = _read_bruto_rows(source_version_id, db_path)
    normalized_rows = list(normalize(raw_rows))
    deduped_rows = _dedupe_exact(normalized_rows)

    names = [row["empresa_nome_raw"] for row in deduped_rows]
    match_result = match_companies(names)

    now = datetime.now(UTC).isoformat()
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            "INSERT INTO dataset_versions "
            "(layer, source_version_id, created_at, row_count, status) "
            "VALUES ('tratado', ?, ?, ?, 'ready')",
            (source_version_id, now, len(deduped_rows)),
        )
        version_id = cursor.lastrowid

        conn.executemany(
            "INSERT INTO tratado_reclamacoes "
            "(version_id, empresa_entidade_id, segmento, assunto, uf, "
            "data_abertura, data_resposta, resultado, nota_satisfacao) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    version_id,
                    match_result.entity_id_by_name[row["empresa_nome_raw"]],
                    row["segmento"],
                    row["assunto"],
                    row["uf"],
                    row["data_abertura"],
                    row["data_resposta"],
                    row["resultado"],
                    row["nota_satisfacao"],
                )
                for row in deduped_rows
            ],
        )
        conn.commit()
    finally:
        conn.close()

    _review_queues[version_id] = match_result.review_queue
    return version_id
