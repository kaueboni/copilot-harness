# Copilot Instructions

## Project Overview
Radar Consumidor: produto greenfield que transforma os dados abertos de reclamações do
Consumidor.gov.br (Senacon) em indicadores de qualidade de atendimento consultáveis em
linguagem natural, com metodologia de cálculo sempre explicitada. Ver
[docs/tdd-radar-consumidor.md](../docs/tdd-radar-consumidor.md) para contexto completo,
escopo e plano de implementação.

Este repositório está em fase de planejamento: não há código de aplicação ainda, apenas
documentação de arquitetura e specs de feature.

## Repo Structure
- `docs/` — TDD do produto e ADRs (decisões de arquitetura aceitas).
  - `docs/tdd-radar-consumidor.md` — visão, escopo e problema a resolver.
  - `docs/adr/` — decisões arquiteturais (ex.: execução local via Docker Compose,
    stack Python + SQLite). Consulte antes de propor alternativas de infraestrutura.
- `.specs/` — workflow de spec-driven development (skill `tlc-spec-driven`).
  - `.specs/STATE.md` — decisões ativas e handoff do trabalho em andamento; leia antes
    de continuar qualquer feature.
  - `.specs/features/<nome>/` — spec, contexto e design de cada feature.
- `.github/skills/` — skills reutilizáveis do harness de Copilot (ADR, RFC, TDD,
  spec-driven workflow, journal, criação de subagentes/skills).

## Conventions
- Documentação de produto (TDD, ADRs, specs) é escrita em **português**.
- ADRs seguem o formato MADR (Contexto, Decision Drivers, Options, Outcome,
  Consequences) — ver exemplos em `docs/adr/`.
- Antes de assumir uma decisão de arquitetura nova, verifique se já existe um ADR
  cobrindo o tema.
- Trabalho de feature usa o fluxo Specify → Design → Tasks → Execute descrito na skill
  `tlc-spec-driven`; o estado atual e próximos passos ficam em `.specs/STATE.md`.

## Build and Test
Nenhum código de aplicação foi implementado ainda — não há comandos de build/test
válidos neste momento. Quando a implementação começar (ver ADR-001/ADR-002: Docker
Compose + Python/SQLite), atualize esta seção com os comandos reais.
