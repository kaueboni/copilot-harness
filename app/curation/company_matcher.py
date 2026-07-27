"""Modulo de fuzzy match de nomes de empresa (ING-05, ING-07).

Agrupa nomes de empresa distintos-porem-similares como a mesma entidade, usando uma
chave de blocking (primeira palavra normalizada) antes do fuzzy match completo com
`rapidfuzz.process.cdist` (ver design.md - Componente Fuzzy Match / Tech Decisions).
Pares com confianca ambigua (score 80-91) sao sinalizados para revisao amostral em vez
de fundidos automaticamente; pares com score <80 permanecem entidades distintas.
"""

import re
from dataclasses import dataclass, field

from rapidfuzz import fuzz, process

MERGE_THRESHOLD = 92
REVIEW_THRESHOLD = 80


@dataclass
class MatchResult:
    entity_id_by_name: dict[str, int]
    review_queue: list[tuple[str, str, float]] = field(default_factory=list)
    comparisons_made: int = 0


def _normalize(name: str) -> str:
    normalized = re.sub(r"[^a-z0-9\s]", " ", name.lower())
    return re.sub(r"\s+", " ", normalized).strip()


def _blocking_key(name: str) -> str:
    normalized = _normalize(name)
    return normalized.split(" ")[0] if normalized else ""


def match_companies(names: list[str]) -> MatchResult:
    """Agrupa `names` em entidades unicas via fuzzy match com blocking.

    Retorna o id de entidade resolvido para cada nome original, a fila de revisao
    amostral (pares com score 80-91) e o total de comparacoes realizadas (para
    validar que o blocking reduz o custo em relacao ao O(n^2) puro).
    """
    unique_names = list(dict.fromkeys(names))
    normalized_by_name = {name: _normalize(name) for name in unique_names}

    blocks: dict[str, list[str]] = {}
    for name in unique_names:
        blocks.setdefault(_blocking_key(name), []).append(name)

    parent = {name: name for name in unique_names}

    def find(node: str) -> str:
        while parent[node] != node:
            node = parent[node]
        return node

    def union(a: str, b: str) -> None:
        root_a, root_b = find(a), find(b)
        if root_a != root_b:
            parent[root_b] = root_a

    review_queue: list[tuple[str, str, float]] = []
    comparisons_made = 0

    for block_names in blocks.values():
        if len(block_names) < 2:
            continue
        normalized_block = [normalized_by_name[name] for name in block_names]
        score_matrix = process.cdist(normalized_block, normalized_block, scorer=fuzz.ratio)
        for i in range(len(block_names)):
            for j in range(i + 1, len(block_names)):
                score = float(score_matrix[i][j])
                comparisons_made += 1
                if score >= MERGE_THRESHOLD:
                    union(block_names[i], block_names[j])
                elif score >= REVIEW_THRESHOLD:
                    review_queue.append((block_names[i], block_names[j], score))

    root_to_id: dict[str, int] = {}
    entity_id_by_name: dict[str, int] = {}
    next_id = 1
    for name in unique_names:
        root = find(name)
        if root not in root_to_id:
            root_to_id[root] = next_id
            next_id += 1
        entity_id_by_name[name] = root_to_id[root]

    return MatchResult(
        entity_id_by_name=entity_id_by_name,
        review_queue=review_queue,
        comparisons_made=comparisons_made,
    )
