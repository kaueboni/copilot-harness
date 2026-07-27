# copilot-harness

> **O foco deste repositório é demonstrar, na prática, um harness de contexto para o GitHub Copilot.**
> O produto de exemplo — *Radar Consumidor* — existe apenas como pretexto realista para exercitar o harness: skills, rules, specs, ADRs, RFCs e journal versionados como artefatos de repositório, guiando o Copilot a trabalhar de forma consistente, rastreável e alinhada às decisões do time.

## O que é um "harness" de Copilot?

É o conjunto de arquivos e convenções versionados no próprio repositório que dão contexto persistente ao Copilot — em vez de depender só do prompt da conversa. Aqui isso é feito através de:

- **`.github/copilot-instructions.md`** — instruções globais lidas automaticamente pelo Copilot: visão do projeto, estrutura de pastas, convenções de escrita e onde buscar contexto antes de agir.
- **`.github/skills/`** — skills reutilizáveis que ensinam o agente a produzir artefatos padronizados sob demanda:
  - `create-adr` — gera Architecture Decision Records (MADR, Nygard ou Y-Statement).
  - `create-rfc` — gera RFCs estruturados para decisões que precisam de aprovação/alinhamento de stakeholders.
  - `technical-design-doc-creator` — gera TDDs (Technical Design Docs) de implementação.
  - `tlc-spec-driven` — workflow de spec-driven development (Specify → Design → Tasks → Execute).
  - `harness-journal` — registra decisões e aprendizados do próprio uso do harness.
  - `skill-architect` / `subagent-creator` — meta-skills para criar novas skills e subagentes.
- **`.specs/`** — estado vivo do trabalho em andamento (`STATE.md`), specs de features e lições aprendidas (`LESSONS.md`, `lessons.json`), permitindo retomar o contexto entre sessões.
- **`.agents/`** — lockfile das skills instaladas (`.skill-lock.json`), garantindo reprodutibilidade do harness entre máquinas/sessões.
- **`docs/`** — TDD do produto e ADRs aceitos, servindo de "memória" arquitetural que o Copilot consulta antes de propor algo novo.

A ideia central: **o comportamento do Copilot é dirigido por artefatos versionados e revisáveis em PR**, não por configuração implícita ou conhecimento tácito do desenvolvedor.

## O produto de exemplo: Radar Consumidor

Para dar um contexto de negócio real ao harness, o repositório simula o desenvolvimento do **Radar Consumidor**: um produto que transformaria os dados abertos de reclamações do Consumidor.gov.br (Senacon) em indicadores de qualidade de atendimento consultáveis em linguagem natural, com metodologia de cálculo sempre explicitada.

O projeto está em fase de planejamento — a maior parte do repositório é documentação de arquitetura (TDD, ADRs, specs), não código de aplicação. Isso é intencional: o objetivo não é entregar o Radar Consumidor, e sim mostrar como o harness sustenta o processo de decisão e planejamento de um produto do zero, com o Copilot como colaborador ativo.

## Estrutura do repositório

```
.github/
  copilot-instructions.md   # instruções globais do projeto para o Copilot
  skills/                   # skills do harness (ADR, RFC, TDD, spec-driven, journal...)
.agents/
  .skill-lock.json          # lockfile de skills instaladas
.specs/
  STATE.md                  # estado atual / handoff de trabalho em andamento
  LESSONS.md, lessons.json  # aprendizados registrados durante o uso do harness
  features/                 # specs de features (Specify → Design → Tasks)
docs/
  tdd-radar-consumidor.md   # visão e escopo do produto de exemplo
  adr/                      # decisões arquiteturais aceitas
app/                        # esqueleto de aplicação Python (FastAPI) para o produto de exemplo
```

## Como explorar este repositório

- Quer ver como uma decisão vira documento? Veja os exemplos gerados em `docs/adr/` e a skill correspondente em [`.github/skills/create-adr`](.github/skills/create-adr/README.md).
- Quer entender como o Copilot decide entre RFC e ADR? Veja [`.github/skills/create-rfc`](.github/skills/create-rfc/README.md).
- Quer ver o "estado mental" do agente entre sessões? Veja [`.specs/STATE.md`](.specs/STATE.md) e [`.specs/LESSONS.md`](.specs/LESSONS.md).
- Quer entender as regras globais que moldam qualquer interação do Copilot neste repo? Veja [`.github/copilot-instructions.md`](.github/copilot-instructions.md).

## Stack técnica (produto de exemplo)

Python 3.11+, FastAPI, pandas e rapidfuzz, gerenciado com `uv`/`hatchling`. Consulte `docs/adr/` para as decisões de infraestrutura (ex.: execução local via Docker Compose, stack Python + SQLite).

## Licença

Ver [LICENSE](LICENSE).
