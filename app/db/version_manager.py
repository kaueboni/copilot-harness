"""Gerenciador de versao ativa por camada (bruto/tratado/agregado).

Garante que existe no maximo uma versao ativa por camada por vez, sobre a tabela
`active_version` (ver design.md - Tech Decisions, ING-11).
"""

from datetime import UTC, datetime

from app.db.connection import DEFAULT_DB_PATH, get_connection

ACTIVATED_BY_DEFAULT = "system"


def activate(
    layer: str,
    version_id: int,
    db_path: str = DEFAULT_DB_PATH,
    activated_by: str = ACTIVATED_BY_DEFAULT,
) -> None:
    """Marca `version_id` como a versao ativa da camada `layer` (upsert)."""
    conn = get_connection(db_path)
    try:
        conn.execute(
            """
            INSERT INTO active_version (layer, version_id, activated_at, activated_by)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (layer) DO UPDATE SET
                version_id = excluded.version_id,
                activated_at = excluded.activated_at,
                activated_by = excluded.activated_by
            """,
            (layer, version_id, datetime.now(UTC).isoformat(), activated_by),
        )
        conn.commit()
    finally:
        conn.close()


def get_active(layer: str, db_path: str = DEFAULT_DB_PATH) -> int | None:
    """Retorna o `version_id` ativo da camada `layer`, ou None se nenhuma versao ativa."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT version_id FROM active_version WHERE layer = ?", (layer,)
        ).fetchone()
    finally:
        conn.close()
    return row[0] if row else None


def rollback(
    layer: str,
    version_id: int,
    db_path: str = DEFAULT_DB_PATH,
    activated_by: str = ACTIVATED_BY_DEFAULT,
) -> None:
    """Reaponta a versao ativa da camada para `version_id` (versao anterior).

    A versao previamente ativa nao e apagada de `dataset_versions`, apenas deixa de
    estar marcada como ativa.
    """
    activate(layer, version_id, db_path=db_path, activated_by=activated_by)
