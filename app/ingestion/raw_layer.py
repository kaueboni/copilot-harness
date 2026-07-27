"""Camada bruta versionada (writer) - ING-01, ING-03.

Grava o CSV oficial sem transformacao em `bruto_reclamacoes`, cria uma nova versao em
`dataset_versions` (layer='bruto') vinculada ao `run_id` e atualiza `ingestion_runs`
com os metadados da execucao concluida (ver design.md - Camada Bruta / Data Models).
"""

import hashlib
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from app.db.connection import DEFAULT_DB_PATH, get_connection


def _checksum_file(csv_path: str | Path) -> str:
    return hashlib.sha256(Path(csv_path).read_bytes()).hexdigest()


def store_raw(csv_path: str, run_id: int, db_path: str | Path = DEFAULT_DB_PATH) -> int:
    """Grava `csv_path` como nova versao da camada bruta, vinculada a `run_id`.

    Retorna o `version_id` da nova versao criada.
    """
    df = pd.read_csv(csv_path)
    row_count = len(df)
    checksum = _checksum_file(csv_path)
    now = datetime.now(UTC).isoformat()

    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            "INSERT INTO dataset_versions "
            "(layer, source_run_id, created_at, row_count, status) "
            "VALUES ('bruto', ?, ?, ?, 'ready')",
            (run_id, now, row_count),
        )
        version_id = cursor.lastrowid

        conn.executemany(
            "INSERT INTO bruto_reclamacoes "
            "(version_id, empresa_nome_raw, segmento, assunto, uf, "
            "data_abertura, data_resposta, resultado, nota_satisfacao) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    version_id,
                    row.get("empresa"),
                    row.get("segmento"),
                    row.get("assunto"),
                    row.get("uf"),
                    row.get("data_abertura"),
                    row.get("data_resposta"),
                    row.get("resultado"),
                    row.get("nota_satisfacao")
                    if pd.notna(row.get("nota_satisfacao"))
                    else None,
                )
                for row in df.to_dict(orient="records")
            ],
        )

        conn.execute(
            "UPDATE ingestion_runs "
            "SET finished_at = ?, status = 'success', row_count = ?, source_checksum = ? "
            "WHERE run_id = ?",
            (now, row_count, checksum, run_id),
        )
        conn.commit()
    finally:
        conn.close()

    return version_id
