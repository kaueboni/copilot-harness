from app.curation.company_matcher import match_companies


def test_match_companies_merges_fixture_name_variants_above_threshold():
    # variantes de grafia da mesma empresa no fixture (score ~96, >= 92)
    names = ["Empresa X S.A.", "EMPRESA X SA", "Empresa Y Ltda"]

    result = match_companies(names)

    assert (
        result.entity_id_by_name["Empresa X S.A."]
        == result.entity_id_by_name["EMPRESA X SA"]
    )
    assert (
        result.entity_id_by_name["Empresa Y Ltda"]
        != result.entity_id_by_name["Empresa X S.A."]
    )


def test_match_companies_flags_ambiguous_pair_for_review_without_merging():
    # mesma chave de blocking ("banco"), score ~88 (faixa 80-91) - nao deve fundir
    names = ["Banco do Brasil S.A.", "Banco Brasil SA"]

    result = match_companies(names)

    assert (
        result.entity_id_by_name["Banco do Brasil S.A."]
        != result.entity_id_by_name["Banco Brasil SA"]
    )
    review_pairs = {frozenset((a, b)) for a, b, _ in result.review_queue}
    assert frozenset(("Banco do Brasil S.A.", "Banco Brasil SA")) in review_pairs


def test_match_companies_keeps_clearly_distinct_names_separate_and_out_of_review_queue():
    # mesma chave de blocking ("empresa"), score ~74 (< 80) - claramente distintas
    names = ["Empresa X S.A.", "Empresa Y Ltda"]

    result = match_companies(names)

    assert (
        result.entity_id_by_name["Empresa X S.A."]
        != result.entity_id_by_name["Empresa Y Ltda"]
    )
    review_pairs = {frozenset((a, b)) for a, b, _ in result.review_queue}
    assert frozenset(("Empresa X S.A.", "Empresa Y Ltda")) not in review_pairs


def test_match_companies_blocking_reduces_comparisons_below_full_pairwise():
    names = [
        "Empresa X S.A.",
        "EMPRESA X SA",
        "Banco do Brasil S.A.",
        "Banco Brasil SA",
        "Farmacia Popular",
        "Livraria Cultura",
    ]
    full_pairwise_count = len(names) * (len(names) - 1) // 2  # 15, sem blocking

    result = match_companies(names)

    # so ha comparacao dentro de cada bloco (2 blocos de 2 nomes -> 1 par cada)
    assert result.comparisons_made == 2
    assert result.comparisons_made < full_pairwise_count
