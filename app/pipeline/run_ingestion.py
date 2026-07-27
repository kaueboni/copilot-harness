"""Orquestracao ponta a ponta do pipeline (ING-11).

Encadeia as camadas ja implementadas (endpoint de ingestao -> bruto -> tratado ->
agregado) e ativa a nova versao agregada resultante, sem reimplementar a logica de
cada camada (ver design.md - Architecture Overview / Components).

Fluxo: `endpoint.ingest` (T8, que ja chama `schema_validator.validate` e
`raw_layer.store_raw`) -> `treated_layer.store_treated` (T11) ->
`indicators.calculate` (T13) -> `version_manager.activate` (T4) na camada agregada.

O rollback (`version_manager.rollback`) ja existe e e reutilizado diretamente sobre a
camada agregada; este modulo nao precisa de wrapper proprio para ele.
"""

import os
from pathlib import Path

from app.aggregation.indicators import calculate
from app.curation.treated_layer import store_treated
from app.db import version_manager
from app.db.connection import DEFAULT_DB_PATH, get_connection
from app.ingestion.endpoint import IngestRequest, ingest


def _get_bruto_version_id(run_id: int, db_path: str | Path) -> int:
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT version_id FROM dataset_versions "
            "WHERE layer = 'bruto' AND source_run_id = ?",
            (run_id,),
        ).fetchone()
    finally:
        conn.close()
    return row[0]


def _ingest_via_endpoint(csv_path: str, period: str, db_path: str | Path) -> int:
    """Chama `endpoint.ingest` (T8) apontando temporariamente para `db_path`.

    O endpoint le o caminho do banco via a variavel de ambiente
    `RADAR_ANALYTICS_DB_PATH`; o valor anterior e restaurado ao final.
    """
    previous = os.environ.get("RADAR_ANALYTICS_DB_PATH")
    os.environ["RADAR_ANALYTICS_DB_PATH"] = str(db_path)
    try:
        response = ingest(IngestRequest(source_path=csv_path, period=period))
    finally:
        if previous is None:
            os.environ.pop("RADAR_ANALYTICS_DB_PATH", None)
        else:
            os.environ["RADAR_ANALYTICS_DB_PATH"] = previous
    return response.run_id


def run_pipeline(
    csv_path: str, period: str, db_path: str | Path = DEFAULT_DB_PATH
) -> int:
    """Roda o pipeline completo (bruto -> tratado -> agregado) sem intervencao manual.

    Ingere `csv_path` via o endpoint (T8), gera a camada tratada (T11), calcula os
    indicadores agregados do `period` fechado (T13) e ativa a nova versao agregada
    (T4). Retorna o `version_id` agregado ativado.

    Propaga `HTTPException` se o schema do CSV for invalido, e `ValueError` se
    `period` nao for um mes fechado (comportamento das camadas reutilizadas).
    """
    run_id = _ingest_via_endpoint(csv_path, period, db_path)
    bruto_version_id = _get_bruto_version_id(run_id, db_path)
    treated_version_id = store_treated(bruto_version_id, db_path=db_path)
    agregado_version_id = calculate(treated_version_id, period, db_path=db_path)
    version_manager.activate("agregado", agregado_version_id, db_path=str(db_path))
    return agregado_version_id
