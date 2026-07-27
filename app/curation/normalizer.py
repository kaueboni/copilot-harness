"""Normalizador de encoding e datas (ING-04).

Padroniza encoding e formato de data para ISO 8601 antes da etapa de fuzzy match
(ver design.md - Componente Normalizador).
"""

from collections.abc import Iterable

DATE_FIELDS = ("data_abertura", "data_resposta")


def _fix_encoding(value: str) -> str:
    """Corrige mojibake tipico (UTF-8 decodificado incorretamente como Latin-1).

    Textos ja corretos em UTF-8 nao sobrevivem ao round-trip latin1->utf-8 (levantam
    UnicodeDecodeError/UnicodeEncodeError) e sao retornados inalterados.
    """
    try:
        return value.encode("latin1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        return value


def _normalize_date(value: str) -> str:
    """Converte datas em formato DD/MM/YYYY para ISO 8601 (YYYY-MM-DD).

    Valores vazios ou ja em ISO 8601 sao retornados inalterados.
    """
    if not value or "/" not in value:
        return value
    day, month, year = value.split("/")
    return f"{year}-{int(month):02d}-{int(day):02d}"


def normalize(raw_rows: Iterable[dict]) -> Iterable[dict]:
    """Normaliza encoding e datas de cada linha de `raw_rows`."""
    normalized = []
    for row in raw_rows:
        new_row = {}
        for key, value in row.items():
            if key in DATE_FIELDS and isinstance(value, str):
                new_row[key] = _normalize_date(value)
            elif isinstance(value, str):
                new_row[key] = _fix_encoding(value)
            else:
                new_row[key] = value
        normalized.append(new_row)
    return normalized
