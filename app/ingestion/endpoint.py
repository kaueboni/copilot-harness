"""Endpoint HTTP de disparo manual da ingestao (ING-01, ING-02, ING-03).

Orquestra: cria `ingestion_runs` (status running) -> valida schema (T6) -> se
invalido, marca `failed` com `error_message` e nao grava nada; se valido, chama
`store_raw` (T7), que marca `success` e cria a nova versao bruta.
"""

import os
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db.connection import DEFAULT_DB_PATH, get_connection
from app.ingestion.raw_layer import store_raw
from app.ingestion.schema_validator import SchemaValidationResult, validate

router = APIRouter()


def _db_path() -> str:
    return os.environ.get("RADAR_ANALYTICS_DB_PATH", str(DEFAULT_DB_PATH))


class IngestRequest(BaseModel):
    source_path: str
    period: str


class IngestResponse(BaseModel):
    run_id: int


class IngestStatusResponse(BaseModel):
    status: str
    row_count: int | None
    error_message: str | None


def _create_running_run(source_path: str) -> int:
    conn = get_connection(_db_path())
    try:
        cursor = conn.execute(
            "INSERT INTO ingestion_runs (started_at, status, source_file_name, source_checksum) "
            "VALUES (?, 'running', ?, '')",
            (datetime.now(UTC).isoformat(), source_path),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def _mark_failed(run_id: int, error_message: str) -> None:
    conn = get_connection(_db_path())
    try:
        conn.execute(
            "UPDATE ingestion_runs SET finished_at = ?, status = 'failed', error_message = ? "
            "WHERE run_id = ?",
            (datetime.now(UTC).isoformat(), error_message, run_id),
        )
        conn.commit()
    finally:
        conn.close()


def _format_schema_error(result: SchemaValidationResult) -> str:
    if result.error == "empty_file":
        return "Arquivo de origem vazio."
    if result.error == "corrupted_file":
        return "Arquivo de origem corrompido (nao parseavel)."
    parts = []
    if result.missing_columns:
        parts.append(f"colunas faltantes: {', '.join(result.missing_columns)}")
    if result.unexpected_columns:
        parts.append(f"colunas inesperadas: {', '.join(result.unexpected_columns)}")
    return "Schema invalido - " + "; ".join(parts)


@router.post("/ingest", status_code=202)
def ingest(request: IngestRequest) -> IngestResponse:
    run_id = _create_running_run(request.source_path)

    result = validate(request.source_path)
    if not result.ok:
        error_message = _format_schema_error(result)
        _mark_failed(run_id, error_message)
        raise HTTPException(status_code=422, detail=error_message)

    store_raw(request.source_path, run_id, db_path=_db_path())
    return IngestResponse(run_id=run_id)


@router.get("/ingest/{run_id}")
def get_ingest_status(run_id: int) -> IngestStatusResponse:
    conn = get_connection(_db_path())
    try:
        row = conn.execute(
            "SELECT status, row_count, error_message FROM ingestion_runs WHERE run_id = ?",
            (run_id,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="run_id nao encontrado")

    return IngestStatusResponse(status=row[0], row_count=row[1], error_message=row[2])
