# STATE

## Decisions

### AD-001
- **Decision**: Indicadores agregados só são calculados/publicados para meses fechados; o mês corrente em andamento nunca entra na camada agregada.
- **Reason**: Resolve a ambiguidade de arredondamento de período sinalizada como Questão em Aberto no TDD; garante reprodutibilidade (mesma pergunta, mesma janela de dados, mesma resposta).
- **Trade-off**: Indicadores do mês corrente não ficam disponíveis até o mês fechar — nenhuma visão "em tempo real" do mês em curso.
- **Scope**: Fase 1 (Ingestão e Curadoria) e qualquer feature futura que consulte a camada agregada (ex.: Fase 2 — Camada de Acesso a Dados).
- **Date**: 2026-07-26
- **Status**: active

### AD-002
- **Decision**: A ingestão de dados é disparada manualmente via endpoint HTTP, não por agendamento/cron.
- **Reason**: Alinhado à decisão já registrada no ADR-002 (stack local Python + SQLite), que previa disparo manual por script/endpoint.
- **Trade-off**: Sem execução automática periódica nesta fase — depende de alguém/algo chamar o endpoint.
- **Scope**: Fase 1 (Ingestão e Curadoria).
- **Date**: 2026-07-26
- **Status**: active

### AD-003
- **Decision**: Versionamento das camadas de dados (bruto/tratado/agregado) usa um padrão de 3 tabelas de controle append-only — `ingestion_runs` (ledger de execuções), `dataset_versions` (versão por camada, com lineage via `source_run_id`/`source_version_id`) e `active_version` (ponteiro de versão ativa por camada, tabela separada — não flag `is_active` por linha). Qualquer consumidor da camada agregada (ex.: Fase 2 — Camada de Acesso a Dados) deve ler através de views que já resolvem para a versão ativa (ex.: `agregado_indicadores_ativo`), nunca diretamente das tabelas de fato.
- **Reason**: Suporta rollback (ING-11) sem apagar dados e sem exigir UPDATE em massa; centraliza a lógica de "qual versão está ativa" numa única tabela pequena em vez de duplicar `is_active` em cada tabela de fato; elimina risco de duas versões "ativas" simultâneas.
- **Trade-off**: Consumidores precisam sempre passar pelas views (nunca consultar as tabelas de fato diretamente) para respeitar o ponteiro de versão ativa; o arquivo `analytics.db` cresce continuamente, já que versões antigas nunca são apagadas — política de retenção/purga fica em aberto.
- **Scope**: Fase 1 (Ingestão e Curadoria) e Fase 2 (Camada de Acesso a Dados) — qualquer feature futura que leia a camada agregada.
- **Date**: 2026-07-26
- **Status**: active

## Handoff

- **Feature**: ingestao-curadoria (`.specs/features/ingestao-curadoria/`)
- **Phase / Task**: Execute concluído e Verificado (PASS) — feature completa (T1-T14 + 3 fix tasks)
- **Completed**: Specify, Discuss, Design, Tasks, Execute, Verify
- **In-progress** (file:line): nenhum
- **Next step**: Nenhum pendente para esta feature. Próxima feature candidata: Fase 2 (Camada de Acesso a Dados) do TDD — depende desta fase estar concluída (agora está). Antes de iniciar, revisar os 2 itens em aberto abaixo.
- **Blockers**: (1) Layout exato de colunas do CSV oficial não confirmado — fonte (dados.mj.gov.br) está fora do ar desde 2026-07-26; revisar quando voltar, antes de considerar ING-02/tabelas de fato definitivas. (2) Fila de revisão do fuzzy match (ING-07) é in-memory (`get_review_queue`), não persistida — avaliar se a Fase 2 precisa dela persistida em tabela.
- **Uncommitted files**: `.specs/STATE.md` (documentação apenas — todo o código da feature está commitado; ver `tasks.md` para os 17 hashes de commit: T1-T14 + 3 fix tasks)
- **Branch**: `main` (17 commits locais à frente de `origin/main` — não enviados ainda)
- **Resultado final**: 47 testes passando, `ruff check .` limpo, `validation.md` com veredito PASS (Rodada 2) após 1 iteração de fix→re-verify. 4 lições registradas em `.specs/LESSONS.md`/`lessons.json` (candidatas).
