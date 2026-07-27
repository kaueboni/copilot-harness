# Ingestão e Curadoria de Dados (Fase 1) Context

**Gathered:** 2026-07-26
**Spec:** `.specs/features/ingestao-curadoria/spec.md`
**Status:** Ready for design

---

## Feature Boundary

Pipeline de ingestão e curadoria dos dados do Consumidor.gov.br: camada bruta
(imutável, versionada) → camada tratada (normalizada, deduplicada) → camada agregada
(indicadores por empresa/segmento/mês, mês fechado, com as duas metodologias de índice
de solução). Disparado manualmente via endpoint. Não inclui consulta/exposição dos
dados agregados (Fase 2) nem nada além da Fase 1 do TDD.

---

## Implementation Decisions

### Fonte de dados e disponibilidade

- Fonte oficial: [dados.mj.gov.br/dataset/reclamacoes-do-consumidor-gov-br](https://dados.mj.gov.br/dataset/reclamacoes-do-consumidor-gov-br).
- Em 2026-07-26 (data desta especificação), o site está fora do ar — não foi possível
  inspecionar o layout real do CSV. Tratar como dependência externa sem SLA (risco já
  mapeado no TDD), não como bloqueio da especificação.

### Disparo de execução

- A ingestão é exposta como **endpoint** HTTP, chamado manualmente — não há
  agendamento/cron nesta fase. Alinhado ao texto do ADR-002.

### Regra de período

- Indicadores só são calculados/publicados para **meses fechados**. O mês corrente em
  andamento nunca entra na camada agregada. Esta regra resolve a ambiguidade de
  arredondamento de período que estava como Questão em Aberto no TDD original — e passa
  a valer também para qualquer feature futura que consuma a camada agregada (ex.: Fase
  2 — Camada de Acesso a Dados).

### Normalização de empresa

- Deduplicação/normalização de nomes de empresa usa **fuzzy match** (correspondência
  aproximada de string), com uma etapa de amostra para revisão humana — conforme
  mitigação já prevista no TDD para o risco de fragmentar/fundir empresas
  incorretamente.

### Agent's Discretion

- Biblioteca e limiar de similaridade exatos do fuzzy match — decisão técnica de
  Design, não de produto.
- Formato exato do payload do endpoint (upload direto de arquivo vs. referência a um
  arquivo já disponível) — decisão de contrato técnico, fica para Design.
- Estrutura de tabelas dentro do `analytics.db` (nomes, colunas de controle de versão)
  — decisão de Design.

### Declined / Undiscussed Gray Areas → Assumptions

- **Layout exato de colunas do CSV**: não discutido em profundidade porque a fonte
  está indisponível hoje. Assumido, como default, o conjunto de campos já citado no
  TDD (empresa, segmento, assunto, prazos, resultado do atendimento, UF, data) — a
  confirmar assim que o site voltar, antes de finalizar a validação de schema (ING-02).
  Registrado no spec.md em Assumptions & Open Questions.
- **Payload/contrato do endpoint**: não é uma decisão de produto, então não foi
  aprofundada aqui — registrada como decisão pendente de Design no spec.md.

---

## Specific References

Nenhuma referência de produto específica trazida pelo usuário além do link da fonte
oficial (dados.mj.gov.br) e das decisões registradas acima.

---

## Deferred Ideas

Nenhuma — a discussão ficou dentro do escopo desta feature (Fase 1 do TDD). Escopo de
consulta/exposição de dados permanece explicitamente na Fase 2 (fora desta feature).
