import csv

from fastapi.testclient import TestClient

from app.db.connection import get_connection
from app.db.migrate import migrate
from app.main import app

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


def _client(db_path, monkeypatch):
    migrate(db_path)
    monkeypatch.setenv("RADAR_ANALYTICS_DB_PATH", str(db_path))
    return TestClient(app)


def test_post_ingest_with_valid_csv_returns_202_and_creates_bruto_version(
    tmp_path, monkeypatch
):
    db_path = tmp_path / "test.db"
    client = _client(db_path, monkeypatch)

    response = client.post(
        "/ingest", json={"source_path": FIXTURE_PATH, "period": "2026-06"}
    )

    assert response.status_code == 202
    run_id = response.json()["run_id"]

    conn = get_connection(db_path)
    try:
        version_count = conn.execute(
            "SELECT COUNT(*) FROM dataset_versions WHERE layer = 'bruto'"
        ).fetchone()[0]
        run_status = conn.execute(
            "SELECT status FROM ingestion_runs WHERE run_id = ?", (run_id,)
        ).fetchone()[0]
    finally:
        conn.close()

    assert version_count == 1
    assert run_status == "success"


def test_post_ingest_with_missing_column_rejects_without_writing_version(
    tmp_path, monkeypatch
):
    db_path = tmp_path / "test.db"
    client = _client(db_path, monkeypatch)

    fieldnames, rows = _read_fixture_rows()
    fieldnames_missing = [c for c in fieldnames if c != "nota_satisfacao"]
    rows_missing = [
        {k: v for k, v in row.items() if k != "nota_satisfacao"} for row in rows
    ]
    csv_path = tmp_path / "missing_column.csv"
    _write_csv(csv_path, fieldnames_missing, rows_missing)

    response = client.post(
        "/ingest", json={"source_path": str(csv_path), "period": "2026-06"}
    )

    assert response.status_code == 422
    assert "nota_satisfacao" in response.json()["detail"]

    conn = get_connection(db_path)
    try:
        version_count = conn.execute(
            "SELECT COUNT(*) FROM dataset_versions WHERE layer = 'bruto'"
        ).fetchone()[0]
    finally:
        conn.close()

    assert version_count == 0


def test_post_ingest_with_empty_csv_distinguishes_from_invalid_schema(
    tmp_path, monkeypatch
):
    db_path = tmp_path / "test.db"
    client = _client(db_path, monkeypatch)

    csv_path = tmp_path / "empty.csv"
    csv_path.write_text("", encoding="utf-8")

    response = client.post(
        "/ingest", json={"source_path": str(csv_path), "period": "2026-06"}
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "vazio" in detail.lower()
    assert "schema invalido" not in detail.lower()

    conn = get_connection(db_path)
    try:
        version_count = conn.execute(
            "SELECT COUNT(*) FROM dataset_versions WHERE layer = 'bruto'"
        ).fetchone()[0]
    finally:
        conn.close()

    assert version_count == 0


def test_post_ingest_with_corrupted_csv_distinguishes_from_invalid_schema(
    tmp_path, monkeypatch
):
    db_path = tmp_path / "test.db"
    client = _client(db_path, monkeypatch)

    fieldnames, _ = _read_fixture_rows()
    csv_path = tmp_path / "corrupted.csv"
    header = ",".join(fieldnames)
    # campo com aspas nao fechadas -> EOF dentro de string, nao parseavel
    broken_row = '"empresa sem fechar aspas,x,x,x,x,x,x'
    csv_path.write_text(f"{header}\n{broken_row}\n", encoding="utf-8")

    response = client.post(
        "/ingest", json={"source_path": str(csv_path), "period": "2026-06"}
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "corrompido" in detail.lower()
    assert "schema invalido" not in detail.lower()

    conn = get_connection(db_path)
    try:
        version_count = conn.execute(
            "SELECT COUNT(*) FROM dataset_versions WHERE layer = 'bruto'"
        ).fetchone()[0]
    finally:
        conn.close()

    assert version_count == 0


def test_get_ingest_status_returns_status_row_count_and_error_after_run(
    tmp_path, monkeypatch
):
    db_path = tmp_path / "test.db"
    client = _client(db_path, monkeypatch)

    post_response = client.post(
        "/ingest", json={"source_path": FIXTURE_PATH, "period": "2026-06"}
    )
    run_id = post_response.json()["run_id"]

    status_response = client.get(f"/ingest/{run_id}")

    assert status_response.status_code == 200
    body = status_response.json()
    assert body["status"] == "success"
    assert body["row_count"] == 6
    assert body["error_message"] is None


def test_post_ingest_twice_for_same_period_creates_two_versions(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    client = _client(db_path, monkeypatch)

    first = client.post(
        "/ingest", json={"source_path": FIXTURE_PATH, "period": "2026-06"}
    )
    second = client.post(
        "/ingest", json={"source_path": FIXTURE_PATH, "period": "2026-06"}
    )

    assert first.json()["run_id"] != second.json()["run_id"]

    conn = get_connection(db_path)
    try:
        version_count = conn.execute(
            "SELECT COUNT(*) FROM dataset_versions WHERE layer = 'bruto'"
        ).fetchone()[0]
    finally:
        conn.close()

    assert version_count == 2
