import csv

from scripts.generate_fixture import COLUMNS, OUTPUT_PATH, generate_fixture


def test_fixture_contains_expected_columns_and_edge_cases(tmp_path):
    output_path = generate_fixture(output_path=tmp_path / "reclamacoes_sample.csv")

    with output_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == COLUMNS
        rows = list(reader)

    # >=2 variantes de grafia da mesma empresa
    empresa_variants = {row["empresa"] for row in rows if row["empresa"].upper().startswith("EMPRESA X")}
    assert len(empresa_variants) >= 2
    assert "Empresa X S.A." in empresa_variants
    assert "EMPRESA X SA" in empresa_variants

    # 1 duplicata exata
    seen = set()
    duplicate_count = 0
    for row in rows:
        key = tuple(row.values())
        if key in seen:
            duplicate_count += 1
        seen.add(key)
    assert duplicate_count == 1

    # registros de um mes fechado e de um mes em andamento (mes corrente)
    periods = {row["data_abertura"][:7] for row in rows}
    assert len(periods) == 2

    # ao menos 1 registro sem nota_satisfacao
    assert any(row["nota_satisfacao"] == "" for row in rows)

    # o caminho padrao de saida aponta para o golden fixture usado pelas proximas tasks
    assert OUTPUT_PATH.name == "reclamacoes_sample.csv"
    assert OUTPUT_PATH.parent.name == "fixtures"
