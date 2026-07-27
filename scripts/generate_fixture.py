"""Gerador de CSV sintetico (fixture) para desenvolvimento e testes (ING-12).

Fonte oficial (dados.mj.gov.br) esta fora do ar desde 2026-07-26 (ver spec.md
Assumptions) - este fixture segue o layout de colunas assumido ate a confirmacao do
layout real.

Casos de borda incluidos (ver spec.md P1 "Fixture CSV sintetico para desenvolvimento"):
- >=2 variantes de grafia da mesma empresa ("Empresa X S.A." / "EMPRESA X SA")
- 1 duplicata exata de reclamacao
- registros de um mes fechado e de um mes em andamento (mes corrente)
- 1 registro sem nota_satisfacao

Golden data (mes fechado = mes anterior ao mes corrente no momento da geracao),
calculado manualmente a partir das linhas abaixo - apos dedupe da duplicata exata e
apos o fuzzy match agrupar "Empresa X S.A." e "EMPRESA X SA" como a mesma entidade.
Serve de referencia para os testes de T9-T13:

Empresa X, segmento "Telecomunicacoes", mes fechado (3 reclamacoes tratadas):
  - indice_solucao_oficial (resultado == 'Resolvido'): 2/3 = 0.6667
  - tempo_medio_resposta (dias entre data_abertura e data_resposta): (4 + 7 + 10) / 3 = 7.0
  - nota_media (media das notas presentes: 8 e 6; uma linha sem nota): (8 + 6) / 2 = 7.0

Empresa Y Ltda, segmento "Varejo", mes fechado (1 reclamacao):
  - indice_solucao_oficial: 1/1 = 1.0
  - tempo_medio_resposta: 3.0 dias
  - nota_media: 9.0

A linha do mes em andamento (mes corrente) nunca deve entrar em um calculo de
indicadores (ING-09) e por isso nao compoe o golden data acima.
"""

import csv
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "tests" / "fixtures" / "reclamacoes_sample.csv"

COLUMNS = [
    "empresa",
    "segmento",
    "assunto",
    "uf",
    "data_abertura",
    "data_resposta",
    "resultado",
    "nota_satisfacao",
]


def _previous_month(today: date) -> tuple[int, int]:
    if today.month == 1:
        return today.year - 1, 12
    return today.year, today.month - 1


def _fmt(year: int, month: int, day: int) -> str:
    return f"{year:04d}-{month:02d}-{day:02d}"


def build_rows(today: date | None = None) -> list[dict]:
    today = today or date.today()
    closed_year, closed_month = _previous_month(today)
    open_year, open_month = today.year, today.month

    return [
        {
            "empresa": "Empresa X S.A.",
            "segmento": "Telecomunicacoes",
            "assunto": "Cobranca indevida",
            "uf": "SP",
            "data_abertura": _fmt(closed_year, closed_month, 1),
            "data_resposta": _fmt(closed_year, closed_month, 5),
            "resultado": "Resolvido",
            "nota_satisfacao": "8",
        },
        {
            "empresa": "EMPRESA X SA",
            "segmento": "Telecomunicacoes",
            "assunto": "Atraso na entrega",
            "uf": "SP",
            "data_abertura": _fmt(closed_year, closed_month, 3),
            "data_resposta": _fmt(closed_year, closed_month, 10),
            "resultado": "Resolvido",
            "nota_satisfacao": "6",
        },
        {
            # duplicata exata da primeira linha
            "empresa": "Empresa X S.A.",
            "segmento": "Telecomunicacoes",
            "assunto": "Cobranca indevida",
            "uf": "SP",
            "data_abertura": _fmt(closed_year, closed_month, 1),
            "data_resposta": _fmt(closed_year, closed_month, 5),
            "resultado": "Resolvido",
            "nota_satisfacao": "8",
        },
        {
            "empresa": "Empresa X S.A.",
            "segmento": "Telecomunicacoes",
            "assunto": "Produto com defeito",
            "uf": "RJ",
            "data_abertura": _fmt(closed_year, closed_month, 10),
            "data_resposta": _fmt(closed_year, closed_month, 20),
            "resultado": "Nao Resolvido",
            "nota_satisfacao": "",
        },
        {
            "empresa": "Empresa Y Ltda",
            "segmento": "Varejo",
            "assunto": "Entrega atrasada",
            "uf": "MG",
            "data_abertura": _fmt(closed_year, closed_month, 15),
            "data_resposta": _fmt(closed_year, closed_month, 18),
            "resultado": "Resolvido",
            "nota_satisfacao": "9",
        },
        {
            # mes em andamento (mes corrente) - nunca deve ser agregado (ING-09)
            "empresa": "Empresa X S.A.",
            "segmento": "Telecomunicacoes",
            "assunto": "Reclamacao em aberto",
            "uf": "SP",
            "data_abertura": _fmt(open_year, open_month, min(today.day, 5)),
            "data_resposta": "",
            "resultado": "Em Analise",
            "nota_satisfacao": "",
        },
    ]


def generate_fixture(output_path: Path = OUTPUT_PATH, today: date | None = None) -> Path:
    rows = build_rows(today)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return output_path


if __name__ == "__main__":
    generate_fixture()
