"""Calculador de indicadores agregados - ING-08, ING-09, ING-10.

Calcula indice de solucao (oficial/estrito), tempo medio de resposta e nota media,
agrupados por empresa/segmento, apenas para o mes fechado (ver design.md - Calculador
de Indicadores). Cada chamada a `calculate` grava uma nova versao em `dataset_versions`
(layer='agregado'), vinculada a versao tratada de origem via `source_version_id`, sem
sobrescrever execucoes anteriores (ING-10).

SPEC_DEVIATION: spec.md/TDD descrevem a diferenca oficial/estrito como "oficial conta
reclamacao nao avaliada como resolvida; estrito nao conta"
(docs/tdd-radar-consumidor.md linhas 215/377), mas nao definem o valor literal da coluna
`resultado` que representa "nao avaliada". O fixture sintetico (T5) so usa "Resolvido"
e "Nao Resolvido" no mes fechado, entao os dois indices coincidem numericamente no
golden data documentado em scripts/generate_fixture.py. Assumido: qualquer valor de
`resultado` diferente de "Resolvido" e "Nao Resolvido" conta como resolvida no indice
oficial (inflando o resultado) e como nao resolvida no indice estrito.
"""

from datetime import UTC, datetime
from pathlib import Path

from app.db.connection import DEFAULT_DB_PATH, get_connection

RESOLVIDO = "Resolvido"
NAO_RESOLVIDO = "Nao Resolvido"

TREATED_COLUMNS = [
    "empresa_entidade_id",
    "segmento",
    "data_abertura",
    "data_resposta",
    "resultado",
    "nota_satisfacao",
]


def is_month_closed(period: str) -> bool:
    """Retorna True se `period` (YYYY-MM) e um mes estritamente anterior ao atual."""
    current_period = datetime.now(UTC).strftime("%Y-%m")
    return period < current_period


def _read_treated_rows(
    treated_version_id: int, period: str, db_path: str | Path
) -> list[dict]:
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            f"SELECT {', '.join(TREATED_COLUMNS)} FROM tratado_reclamacoes "
            "WHERE version_id = ? AND substr(data_abertura, 1, 7) = ?",
            (treated_version_id, period),
        ).fetchall()
    finally:
        conn.close()
    return [dict(zip(TREATED_COLUMNS, row, strict=True)) for row in rows]


def _response_days(data_abertura: str, data_resposta: str) -> int:
    abertura = datetime.strptime(data_abertura, "%Y-%m-%d")
    resposta = datetime.strptime(data_resposta, "%Y-%m-%d")
    return (resposta - abertura).days


def _calculate_group(rows: list[dict]) -> dict:
    total = len(rows)
    oficial_resolvidas = sum(
        1
        for r in rows
        if r["resultado"] == RESOLVIDO or r["resultado"] not in (RESOLVIDO, NAO_RESOLVIDO)
    )
    estrito_resolvidas = sum(1 for r in rows if r["resultado"] == RESOLVIDO)

    tempos_resposta = [
        _response_days(r["data_abertura"], r["data_resposta"])
        for r in rows
        if r["data_resposta"]
    ]
    notas = [r["nota_satisfacao"] for r in rows if r["nota_satisfacao"] is not None]

    return {
        "indice_solucao_oficial": oficial_resolvidas / total,
        "indice_solucao_estrito": estrito_resolvidas / total,
        "tempo_medio_resposta": (
            sum(tempos_resposta) / len(tempos_resposta) if tempos_resposta else 0.0
        ),
        "nota_media": sum(notas) / len(notas) if notas else None,
    }


def calculate(
    treated_version_id: int, period: str, db_path: str | Path = DEFAULT_DB_PATH
) -> int:
    """Calcula indicadores agregados do `period` (YYYY-MM) fechado sobre a versao tratada.

    Grava o resultado como nova versao em `dataset_versions` (layer='agregado') e
    retorna o `version_id` criado. Recusa o calculo se `period` nao e um mes fechado.
    """
    if not is_month_closed(period):
        raise ValueError(
            f"Periodo '{period}' ainda esta em andamento; calculo de indicadores recusado."
        )

    rows = _read_treated_rows(treated_version_id, period, db_path)

    groups: dict[tuple[int, str], list[dict]] = {}
    for row in rows:
        key = (row["empresa_entidade_id"], row["segmento"])
        groups.setdefault(key, []).append(row)
    group_metrics = {key: _calculate_group(group_rows) for key, group_rows in groups.items()}

    now = datetime.now(UTC).isoformat()
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            "INSERT INTO dataset_versions "
            "(layer, source_version_id, created_at, row_count, status) "
            "VALUES ('agregado', ?, ?, ?, 'ready')",
            (treated_version_id, now, len(group_metrics)),
        )
        version_id = cursor.lastrowid

        conn.executemany(
            "INSERT INTO agregado_indicadores_mensais "
            "(version_id, empresa_entidade_id, segmento, periodo, "
            "indice_solucao_oficial, indice_solucao_estrito, tempo_medio_resposta, nota_media) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    version_id,
                    empresa_entidade_id,
                    segmento,
                    period,
                    metrics["indice_solucao_oficial"],
                    metrics["indice_solucao_estrito"],
                    metrics["tempo_medio_resposta"],
                    metrics["nota_media"],
                )
                for (empresa_entidade_id, segmento), metrics in group_metrics.items()
            ],
        )
        conn.commit()
    finally:
        conn.close()

    return version_id
