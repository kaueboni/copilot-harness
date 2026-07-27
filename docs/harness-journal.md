# Harness Journal

Registro cronológico de como o harness (skills, instructions, subagents, modos) foi usado
neste projeto, e das decisões tomadas ao longo do caminho. Pensado para ser lido por quem
quiser reaproveitar este harness em outro projeto.

---

## [2026-07-26] Criação do TDD do Radar Consumidor

**Tarefa**: Criar o Technical Design Document (TDD) do produto Radar Consumidor a partir do zero (projeto greenfield, workspace vazio).

**Harness usado**: skill `technical-design-doc-creator` — seguiu o fluxo interativo de perguntas (tamanho do projeto, tipo, seções críticas/sugeridas) em vez de gerar um documento genérico de cara, garantindo que seções obrigatórias (Contexto, Problema, Escopo, Solução, Riscos, Plano) e críticas (Segurança, Testes, Monitoramento, Rollback) fossem preenchidas com informação real do usuário.

**Resultado**: [docs/tdd-radar-consumidor.md](tdd-radar-consumidor.md) criado com todas as seções obrigatórias e críticas, mais Métricas de Sucesso, Glossário, Alternativas e Dependências. Duas questões ficaram em aberto: tecnologia de processamento de dados e cloud provider.

**Lição para reaproveitar**: para um projeto greenfield sem contexto prévio, valeu a pena rodar 2-3 rodadas de perguntas (`vscode_askQuestions`) antes de gerar o documento — cada rodada aprofundou uma camada diferente (problema → escopo/solução → riscos/seções extras) em vez de tentar extrair tudo de uma vez.

---

## [2026-07-26] Ambiente de execução e stack de dados: local com Docker

**Tarefa**: Resolver as duas questões em aberto do TDD (tecnologia de processamento de dados e cloud provider), a partir da decisão do usuário de rodar o produto localmente com Docker.

**Harness usado**: skill `create-adr` (formato MADR) — a decisão já tinha sido tomada pelo usuário ("rodar localmente com docker"), então era caso de registrar, não de deliberar (por isso `create-adr` e não `create-rfc`). Antes de gerar os ADRs, usei `vscode_askQuestions` para fechar os detalhes de stack (linguagem, banco, orquestração de ingestão, LLM, UI) que a decisão de "rodar local" deixava em aberto.

**Decisão**: (1) Executar 100% localmente via Docker Compose, sem cloud → [ADR-001](adr/001-execucao-local-com-docker-compose.md). (2) Pipeline em Python (pandas/polars) com SQLite como armazenamento único (`analytics.db` + `app.db` separados por escritor), no lugar de Databricks → [ADR-002](adr/002-stack-processamento-dados-local.md).

**Resultado**: dois ADRs criados e cross-referenciados entre si; TDD atualizado (seção Solução Técnica, Dependências e Questões em Aberto) para apontar para os ADRs em vez de repetir o raciocínio.

**Lição para reaproveitar**: quando uma decisão guarda-chuva ("rodar local com Docker") na verdade resolve duas perguntas em aberto diferentes do TDD, vale separar em dois ADRs pequenos e ligados por "Links" em vez de um ADR único e genérico — fica mais fácil superseder um sem afetar o outro depois. Depois de gerar os ADRs, sempre volte no TDD e troque o texto solto por um link — evita ter a mesma decisão descrita de duas formas diferentes no repo.

---

## [2026-07-26] Specify + Discuss da Fase 1 (Ingestão e Curadoria)

**Tarefa**: A partir do TDD, especificar a Fase 1 do Plano de Implementação (ingestão bruta, normalização/curadoria, cálculo de indicadores) para começar a implementação.

**Harness usado**: skill `tlc-spec-driven` (fases Specify + Discuss) — feature classificada como Large (multi-componente: 3 camadas de dado + versionamento), então gerou spec completo com IDs rastreáveis (`ING-01`...`ING-11`) em vez de um spec inline. A fase Discuss foi acionada porque a feature tem dimensões implícitas presentes (persistência/estado, dependência externa, concorrência já resolvida no ADR-002, transição de estado entre versões da camada agregada).

**Decisão**: Duas decisões de projeto (cross-cutting, registradas em `STATE.md` como AD-001/AD-002): indicadores só valem para mês fechado; disparo da ingestão é via endpoint manual, não cron.

**Resultado**: `.specs/features/ingestao-curadoria/spec.md`, `context.md` e `.specs/STATE.md` criados. Um ponto ficou pendente e registrado como assumption: layout exato de colunas do CSV oficial não pôde ser confirmado porque a fonte (dados.mj.gov.br) estava fora do ar na data da especificação — a validação de schema (ING-02) precisa ser revisada quando o site voltar.

**Lição para reaproveitar**: ao concluir uma fase do `tlc-spec-driven` (Specify/Discuss/Design/Tasks/Execute), registrar no journal deveria ser automático — a skill `harness-journal` já lista "concluir uma tarefa ou fase" como gatilho automático, mas isso exige o agente lembrar de acioná-la sem que o usuário peça. Vale tratar a conclusão de cada fase do spec-driven como um checkpoint natural para atualizar o journal, não só decisões formalizadas em ADR.

---

## [2026-07-26] Design da Fase 1 (Ingestão e Curadoria)

**Tarefa**: Produzir `design.md` da feature `ingestao-curadoria` (arquitetura do pipeline, componentes, schema do `analytics.db`, contrato do endpoint, biblioteca de fuzzy match), a partir do spec.md/context.md já escritos.

**Harness usado**: skill `tlc-spec-driven` (fase Design) — antes de escrever, rodei 3 subagents em paralelo para fechar lacunas de pesquisa (requisitos exatos do template de `design.md`, comparação de bibliotecas de fuzzy match, padrão de schema versionado em SQLite), em vez de decidir sem pesquisa ou pedir tudo ao usuário. Segui a regra da skill de reler `.specs/STATE.md` Decisions (AD-001, AD-002) antes de qualquer escolha arquitetural.

**Decisão**: Padrão de versionamento das camadas de dados (`ingestion_runs` + `dataset_versions` + `active_version` como ponteiro separado, consumido via views pela Fase 2) formalizado como decisão de projeto → **AD-003** em [.specs/STATE.md](../.specs/STATE.md). Decisões feature-locais (biblioteca `rapidfuzz` + thresholds, payload do endpoint por referência a arquivo) ficaram só na tabela Tech Decisions de [design.md](../.specs/features/ingestao-curadoria/design.md).

**Resultado**: `.specs/features/ingestao-curadoria/design.md` criado com as 7 seções obrigatórias do template; `spec.md` atualizado (Requirement Traceability: 11 requisitos ING-01..11 agora "In Design"); `STATE.md` com AD-003 e handoff apontando para a fase Tasks. Layout exato do CSV oficial segue como suposição em aberto (fonte fora do ar).

**Lição para reaproveitar**: quando uma decisão de Design depende de comparar bibliotecas/padrões técnicos (não só ler o repo), vale rodar subagents de pesquisa em paralelo — um por área independente — antes de escrever o `design.md`, em vez de decidir por intuição ou parar para perguntar cada detalhe ao usuário. Usar a heurística do `memory.md` ("uma feature diferente precisaria saber disso?") logo ao final do Design evita esquecer de promover uma decisão feature-local para `AD-NNN` quando ela na verdade é project-level.

---

## [2026-07-26] Tasks da Fase 1 (Ingestão e Curadoria)

**Tarefa**: Quebrar `design.md` da feature `ingestao-curadoria` em tarefas atômicas executáveis (fase Tasks do `tlc-spec-driven`), a partir do pedido do usuário para "implemente".

**Harness usado**: skill `tlc-spec-driven` (fase Tasks) — antes de escrever `tasks.md`, usei `vscode_askQuestions` para fechar 4 lacunas técnicas que `design.md` deixava em aberto e que bloqueavam a Test Coverage Matrix (projeto greenfield, sem testes/framework definidos): framework de teste, framework web do endpoint, gerenciador de pacotes Python e tools por task. O usuário sinalizou indisponibilidade e autorizou trabalho autônomo, então segui com os defaults recomendados (pytest, FastAPI, uv, sem MCPs/skills extras) em vez de bloquear a fase.

**Decisão**: 14 tarefas atômicas (T1-T14) em 6 fases, empacotadas em 2 batches (8 + 6 tasks) por passar do limite de auto-execução inline (~8 tasks) definido pela skill. Decisões técnicas complementares registradas em `tasks.md` (não eram decisão de produto, por isso não foram para `spec.md`/`STATE.md`).

**Resultado**: `.specs/features/ingestao-curadoria/tasks.md` criado com Test Coverage Matrix, Gate Check Commands, e as 3 validações obrigatórias (Granularity Check, Diagram-Definition Cross-Check, Test Co-location Validation) — todas ✅ antes de prosseguir. `spec.md` (Requirement Traceability → "In Tasks") e `STATE.md` (Handoff) atualizados.

**Lição para reaproveitar**: quando o projeto é greenfield e sem guidelines de teste documentadas, a fase Tasks do `tlc-spec-driven` exige perguntar ao usuário o framework/comando de teste antes de gerar a Test Coverage Matrix — mas isso frequentemente também expõe lacunas técnicas do `design.md` (framework web, gerenciador de pacotes) que não são decisão de produto e por isso nunca apareceriam em `spec.md`. Vale agrupar essas perguntas técnicas complementares numa única rodada de `vscode_askQuestions`, junto com a pergunta de teste, em vez de descobri-las uma a uma durante a implementação.

---

## [2026-07-26] Execute da Fase 1 (Ingestão e Curadoria) — T1-T14

**Tarefa**: Implementar as 14 tasks de `tasks.md` (scaffold do projeto Python, banco versionado, ingestão bruta, curadoria/fuzzy match, indicadores agregados, orquestração e rollback), a partir do plano já aprovado na fase Tasks.

**Harness usado**: skill `tlc-spec-driven` (fase Execute) — 14 tasks > limite de ~8 para execução inline, então empacotei em batches de fases inteiras (Batch 1 = Fases 1-3/T1-T8, Batch 2a = Fase 4/T9-T11, Batch 2b = Fase 5/T12-T13, dispatch isolado para T14) e dispatchei cada batch como um subagent via `runSubagent`, verificando de forma independente (`git log`, `uv run pytest`) o resultado de cada um antes de avançar para o próximo, em vez de confiar cegamente no resumo retornado.

**Decisão**: O primeiro subagent (Batch 1 completo, T1-T8) retornou "Agent completed with no output" — sem resumo compacto — após ter implementado e commitado apenas T1-T4, deixando T5 implementado mas não commitado, e T6-T8 não iniciados. Em vez de re-disparar o batch inteiro do zero, inspecionei o estado real do repo (`git log`, `git status`, rodei os testes), completei manualmente o commit de T5, e disparei um segundo subagent focado apenas nas tasks restantes (T6-T8) com o estado atual explicitado no prompt.

**Resultado**: 14 tasks implementadas, 47 testes passando (após a rodada de fix, ver entrada seguinte), 17 commits atômicos no total (T1-T14 + 3 fixes). Dois `SPEC_DEVIATION` auto-documentados pelos próprios subagents ficaram registrados no topo de `tasks.md`: assinatura de `store_treated` divergente do design.md, fila de revisão do fuzzy match em memória (não persistida), e suposição sobre o valor literal de `resultado` para diferenciar índice de solução oficial vs. estrito.

**Lição para reaproveitar**: um subagent de batch pode retornar "sem output" mesmo tendo feito trabalho real e válido — nunca confie apenas no resumo (ou na ausência dele) retornado pelo `runSubagent`; sempre verifique independentemente via `git log --oneline` e o gate de teste real antes de decidir se o batch terminou, terminou parcialmente, ou falhou. Quando um batch para no meio, é mais barato inspecionar o estado real e despachar um subagent de continuação com o progresso já feito explicitado, do que re-rodar o batch inteiro do zero.

---

## [2026-07-26] Validação independente (Execute) da Fase 1 (Ingestão e Curadoria)

**Tarefa**: Auditar as 14 tasks (T1-T14) já implementadas e commitadas da feature `ingestao-curadoria`, como Verifier independente (author ≠ verifier), e conduzir o ciclo fix→re-verify até um veredito final.

**Harness usado**: skill `tlc-spec-driven` (fase Execute → Validate), seguindo `references/validate.md` à risca: tabela de Acceptance Criteria ancorada no spec (evidence-or-zero, `file:line` obrigatório), gate de build mandatório (`pytest && ruff check .`), Discrimination Sensor (mutações comportamentais aplicadas em estado descartável e revertidas), Code Quality Check por camada, e distilação de lições via `scripts/lessons.py` no fechamento.

**Decisão/Achado**: Rodada 1 — gate de Build **falhou** por 3 erros de `ruff` (`DTZ007`/`DTZ011` — datetime/date sem timezone em `indicators.py` e `generate_fixture.py`), mesmo com as 45 suites de teste passando e as 3 mutações do sensor todas mortas; mais 2 gaps reais de cobertura (CSV corrompido não testado no endpoint; divergência entre índice oficial/estrito não exercitada no mês fechado). Veredito: FAIL. Dispatei um subagent de fix (iteração 1 de 3 permitidas) para os 3 gaps, verifiquei cada fix independentemente (`git log`, `uv run pytest && uv run ruff check .`), e re-dispatchei o Verifier para a Rodada 2: **PASS** ✅ — 47 testes, `ruff` limpo, sensor 2/2 morto nos trechos novos, sem gaps remanescentes além dos SPEC_DEVIATION já auto-documentados (aceitos como limitação conhecida, não bloqueadores).

**Resultado**: `.specs/features/ingestao-curadoria/validation.md` com o relatório completo das duas rodadas; `spec.md` (Requirement Traceability → 12/12 "✅ Verified", ING-07 com ressalva arquitetural anotada); `STATE.md` com handoff fechado para esta feature. 4 lições gravadas via `lessons.py` (`L-001` a `L-004`, status `candidate`): consistência de timezone-aware datetime, review queue em memória (SPEC_DEVIATION T11), branch de `resultado` não testado (SPEC_DEVIATION T12/T13), e paridade de cobertura unit↔integration para edge cases.

**Lição para reaproveitar**: o Discrimination Sensor vale mesmo quando o gate de build já falhou por lint — separar "gate de teste" (lógica) de "gate de lint" (estilo) no relatório evita que um `ruff` failure esconda que a suite de testes é, na prática, forte o suficiente. O ciclo fix→re-verify funcionou melhor quando cada gap virou um commit atômico isolado (não um commit único "corrige tudo"), porque isso deixou o Verifier da Rodada 2 confirmar cada fix individualmente por `file:line`, em vez de reavaliar um diff misturado.
