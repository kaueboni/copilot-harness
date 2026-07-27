import csv

from app.ingestion.schema_validator import validate

FIXTURE_PATH = "tests/fixtures/reclamacoes_sample.csv"


def _read_fixture_rows():
    with open(FIXTURE_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, list(reader)


def _write_csv(path, fieldnames, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_validate_ok_when_all_expected_columns_present():
    result = validate(FIXTURE_PATH)

    assert result.ok is True
    assert result.missing_columns == []
    assert result.unexpected_columns == []
    assert result.error is None


def test_validate_detects_missing_column(tmp_path):
    fieldnames, rows = _read_fixture_rows()
    fieldnames_missing = [c for c in fieldnames if c != "nota_satisfacao"]
    rows_missing = [
        {k: v for k, v in row.items() if k != "nota_satisfacao"} for row in rows
    ]
    csv_path = tmp_path / "missing_column.csv"
    _write_csv(csv_path, fieldnames_missing, rows_missing)

    result = validate(str(csv_path))

    assert result.ok is False
    assert result.error is None
    assert result.missing_columns == ["nota_satisfacao"]
    assert result.unexpected_columns == []


def test_validate_detects_unexpected_or_renamed_column(tmp_path):
    fieldnames, rows = _read_fixture_rows()
    renamed_fields = ["empresa_nome" if c == "empresa" else c for c in fieldnames]
    renamed_rows = [
        {("empresa_nome" if k == "empresa" else k): v for k, v in row.items()}
        for row in rows
    ]
    csv_path = tmp_path / "renamed_column.csv"
    _write_csv(csv_path, renamed_fields, renamed_rows)

    result = validate(str(csv_path))

    assert result.ok is False
    assert result.error is None
    assert result.missing_columns == ["empresa"]
    assert result.unexpected_columns == ["empresa_nome"]


def test_validate_empty_file_is_distinct_from_invalid_schema(tmp_path):
    csv_path = tmp_path / "empty.csv"
    csv_path.write_text("", encoding="utf-8")

    result = validate(str(csv_path))

    assert result.ok is False
    assert result.error == "empty_file"
    assert result.missing_columns == []
    assert result.unexpected_columns == []


def test_validate_corrupted_file_is_distinct_from_invalid_schema(tmp_path):
    fieldnames, _ = _read_fixture_rows()
    csv_path = tmp_path / "corrupted.csv"
    header = ",".join(fieldnames)
    # campo com aspas nao fechadas -> EOF dentro de string, nao parseavel
    broken_row = '"empresa sem fechar aspas,x,x,x,x,x,x'
    csv_path.write_text(f"{header}\n{broken_row}\n", encoding="utf-8")

    result = validate(str(csv_path))

    assert result.ok is False
    assert result.error == "corrupted_file"
    assert result.missing_columns == []
    assert result.unexpected_columns == []
