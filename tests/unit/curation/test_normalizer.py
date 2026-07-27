import csv

from app.curation.normalizer import normalize

FIXTURE_PATH = "tests/fixtures/reclamacoes_sample.csv"


def _read_fixture_rows():
    with open(FIXTURE_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_normalize_converts_distinct_date_formats_to_iso8601():
    rows = [
        {"empresa": "Empresa Z", "data_abertura": "05/06/2026", "data_resposta": "10/06/2026"},
        {"empresa": "Empresa Z", "data_abertura": "2026-06-05", "data_resposta": ""},
    ]

    result = normalize(rows)

    assert result[0]["data_abertura"] == "2026-06-05"
    assert result[0]["data_resposta"] == "2026-06-10"
    # ja em ISO 8601 -> permanece igual
    assert result[1]["data_abertura"] == "2026-06-05"
    # vazio -> permanece vazio, nao vira erro
    assert result[1]["data_resposta"] == ""


def test_normalize_fixes_mojibake_encoding():
    # "Comércio" em UTF-8 (bytes C3 A9 para o "é"), decodificado incorretamente
    # como Latin-1, produz o mojibake "ComÃ©rcio".
    mojibake = "ComÃ©rcio".encode("latin1").decode("latin1")
    rows = [{"empresa": "Empresa Z", "segmento": mojibake}]

    result = normalize(rows)

    assert result[0]["segmento"] == "Comércio"


def test_normalize_is_idempotent_for_already_clean_rows():
    rows = _read_fixture_rows()

    once = normalize(rows)
    twice = normalize(once)

    assert once == twice
    # dados ja normalizados do fixture permanecem semanticamente identicos
    assert once[0]["empresa"] == "Empresa X S.A."
    assert once[0]["data_abertura"] == "2026-06-01"
