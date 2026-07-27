"""Validador de schema do CSV oficial de reclamacoes (ING-02).

Confirma que o CSV recebido tem exatamente as colunas esperadas (conjunto assumido em
spec.md - Assumptions), identificando colunas faltantes/divergentes e distinguindo
"arquivo vazio/corrompido" de "schema invalido" (ver design.md - Error Handling
Strategy).
"""

from dataclasses import dataclass, field

import pandas as pd

EXPECTED_COLUMNS = [
    "empresa",
    "segmento",
    "assunto",
    "uf",
    "data_abertura",
    "data_resposta",
    "resultado",
    "nota_satisfacao",
]


@dataclass
class SchemaValidationResult:
    ok: bool
    missing_columns: list[str] = field(default_factory=list)
    unexpected_columns: list[str] = field(default_factory=list)
    error: str | None = None  # "empty_file" | "corrupted_file" | None


def validate(csv_path: str) -> SchemaValidationResult:
    """Valida se `csv_path` tem exatamente as colunas de `EXPECTED_COLUMNS`."""
    try:
        df = pd.read_csv(csv_path)
    except pd.errors.EmptyDataError:
        return SchemaValidationResult(ok=False, error="empty_file")
    except (pd.errors.ParserError, UnicodeDecodeError):
        return SchemaValidationResult(ok=False, error="corrupted_file")

    actual_columns = list(df.columns)
    missing = [c for c in EXPECTED_COLUMNS if c not in actual_columns]
    unexpected = [c for c in actual_columns if c not in EXPECTED_COLUMNS]

    if missing or unexpected:
        return SchemaValidationResult(
            ok=False, missing_columns=missing, unexpected_columns=unexpected
        )

    return SchemaValidationResult(ok=True)
