# Ingestão e Curadoria de Dados (Fase 1) Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow
its Execute flow and Critical Rules.** Do not search for skill files by filesystem path.
The skill is the source of truth for the full flow (per-task cycle, sub-agent
delegation, adequacy review, Verifier, discrimination sensor).

**If the skill cannot be activated, STOP and tell the user — do not proceed without it.**

---

**Design**: `.specs/features/ingestao-curadoria/design.md`
**Status**: Done — todas as 14 tasks (T1-T14) implementadas, testadas e commitadas.
T1 `d64d994`, T2 `77d5652`, T3 `3b59142`, T4 `28c64f0`, T5 `47a777a`, T6 `91dbe2f`,
T7 `18b5b32`, T8 `476aa63`, T9 `bdef0fc`, T10 `aafd314`, T11 `a54a27a`, T12 `05eb363`,
T13 `f34d2bd`, T14 `bc37be0` (45 testes passando). Verificado — ver
[validation.md](validation.md): Rodada 1 = FAIL (gate de Build falhou por 3 erros de
`ruff` DTZ007/DTZ011; sensor 3/3 morto; 2 gaps menores de cobertura). Rodada 2 = **PASS**
após os fixes `93303bc`, `971ce32`, `d129366` (47 testes passando, gate limpo, sensor
2/2 morto). Feature **Verified**.

> **SPEC_DEVIATION (T11)**: `store_treated(source_version_id, db_path=...)` em vez da
> assinatura literal `store_treated(normalized_rows, source_version_id)` do design.md —
> lê a camada bruta internamente e aplica normalizer+matcher, seguindo a descrição
> textual da task em vez da assinatura literal (as duas eram inconsistentes entre si).
> A fila de revisão do fuzzy match (ING-07) é exposta via `get_review_queue(version_id)`
> em memória, não persistida em tabela — não há tabela `review_queue` no schema.sql.
> Revisar se a Fase 2 (Camada de Acesso a Dados) precisa dessa fila persistida antes de
> considerar ING-07 "Verified" definitivo.

> **SPEC_DEVIATION (T12/T13)**: spec.md/TDD não definem o valor literal de `resultado`
> que representa "reclamação não avaliada"/inconclusiva para diferenciar índice de
> solução oficial vs. estrito numericamente. Assumido: qualquer `resultado` diferente
> de "Resolvido"/"Nao Resolvido" conta como resolvida no índice oficial e como não
> resolvida no estrito. Isso faz oficial e estrito coincidirem no fixture atual (que só
> usa esses dois valores no mês fechado) — revisar a metodologia exata quando o layout
> real do CSV oficial for confirmado (mesmo bloqueio já registrado para ING-02).

---

## Technical Decisions Confirmed for Tasks

Estas decisões preenchem lacunas técnicas do `design.md` (não eram decisões de produto,
por isso não estavam no `spec.md`/`context.md`):

| Decision                    | Choice                                                         |
| ---------------------------- | --------------------------------------------------------------- |
| Gerenciador de pacotes Python | `uv` (`pyproject.toml` + `uv.lock`)                              |
| Framework web do endpoint    | FastAPI (async, validação via Pydantic)                          |
| Framework de teste           | `pytest` (unit + integration), comando raiz: `pytest`            |
| Lint/build gate              | `ruff check .`                                                   |
| Bibliotecas de pipeline      | `pandas`, `rapidfuzz` (conforme Tech Decisions do `design.md`)   |

---

## Test Coverage Matrix

> Generated from spec.md + design.md. Guidelines found: nenhum guideline de teste
> declarado no repositório (`.github/copilot-instructions.md` apenas afirma que não há
> comandos de build/test ainda). Projeto greenfield, sem testes existentes — strong
> defaults aplicados (confirmado com o usuário: pytest, sem framework/guideline prévio).

| Code Layer                                                                                                     | Required Test Type | Coverage Expectation                                                                     | Location Pattern                     | Run Command                          |
| ---------------------------------------------------------------------------------------------------------------- | ------------------- | ------------------------------------------------------------------------------------------- | -------------------------------------- | --------------------------------------- |
| Domínio/pipeline (schema_validator, raw_layer, normalizer, company_matcher, treated_layer, indicators, version_manager) | unit                | Todas as ramificações; 1:1 com ACs de ING-01..ING-11; todo edge case listado no spec.md tem teste | `tests/unit/**/test_*.py`              | `pytest tests/unit`                     |
| Acesso a dados (db/connection.py, migrate.py)                                                                    | unit                | Caminhos-chave de leitura/escrita + tratamento de erro (idempotência da migração, WAL/busy_timeout) | `tests/unit/db/test_*.py`              | `pytest tests/unit`                     |
| Endpoint HTTP (app/ingestion/endpoint.py, app/main.py)                                                            | integration         | Todas as rotas do escopo: caminho feliz + cada edge case listado + caminhos de erro          | `tests/integration/test_*.py`          | `pytest tests/integration`              |
| Pipeline ponta a ponta (bruto → tratado → agregado → rollback)                                                   | integration         | Critérios de sucesso do spec.md (execução completa, reprodutibilidade, rollback)             | `tests/integration/test_pipeline_*.py` | `pytest tests/integration`              |
| Fixture sintético (ING-12)                                                                                        | unit                | Fixture contém as colunas e casos de borda exigidos pelo spec.md                             | `tests/unit/fixtures/test_*.py`        | `pytest tests/unit`                     |
| Config/Schema (pyproject.toml, schema.sql, Dockerfile)                                                            | none                | — build gate only                                                                            | —                                       | build gate only                         |

## Gate Check Commands

| Gate Level | When to Use                                          | Command                                       |
| ---------- | ----------------------------------------------------- | ---------------------------------------------- |
| Quick      | Após tasks com apenas testes unitários                | `pytest tests/unit`                            |
| Full       | Após tasks com testes de integração/e2e               | `pytest tests/unit tests/integration`          |
| Build      | Após conclusão de fase ou tasks só de config/schema    | `pytest && ruff check .`                       |

---

## Execution Plan

Phases are ordered and run sequentially — each phase completes before the next begins,
and tasks within a phase execute in order.

### Phase 1: Fundação (projeto, banco, versionamento)

```
T1 → T2 → T3 → T4
```

### Phase 2: Fixture sintético

```
T5
```

### Phase 3: Ingestão bruta

```
T6 → T7 → T8
```

### Phase 4: Curadoria (camada tratada)

```
T9 → T10 → T11
```

### Phase 5: Indicadores agregados

```
T12 → T13
```

### Phase 6: Orquestração ponta a ponta e rollback

```
T14
```

---

## Task Breakdown

### T1: Scaffold do projeto Python

**What**: Criar a estrutura base do projeto — `pyproject.toml` (uv, dependências:
fastapi, uvicorn, pandas, rapidfuzz, pytest, httpx, ruff), pacote `app/` com
`__init__.py` em `app/`, `app/db/`, `app/ingestion/`, `app/curation/`,
`app/aggregation/`, e um `Dockerfile` mínimo para rodar o serviço via Docker Compose
([ADR-001](../../../docs/adr/001-execucao-local-com-docker-compose.md)).
**Where**: `pyproject.toml`, `app/__init__.py`, `app/db/__init__.py`,
`app/ingestion/__init__.py`, `app/curation/__init__.py`, `app/aggregation/__init__.py`,
`Dockerfile`
**Depends on**: None
**Reuses**: nenhum (primeira task de código do projeto)
**Requirement**: N/A (fundação técnica)

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] `uv sync` instala as dependências sem erro
- [ ] Estrutura de pacotes existe conforme listado em "Where"
- [ ] `Dockerfile` builda a imagem sem erro
- [ ] Gate check passa: `ruff check .`

**Tests**: none
**Gate**: build

**Commit**: `chore(scaffold): estrutura inicial do projeto Python (uv, FastAPI, pastas app/)`

---

### T2: Helper de conexão SQLite (analytics.db)

**What**: Criar módulo de conexão ao `analytics.db` com `journal_mode=WAL` e
`busy_timeout` configurados (conforme Tech Decisions do design.md), expondo uma função
`get_connection() -> sqlite3.Connection`.
**Where**: `app/db/connection.py`
**Depends on**: T1
**Reuses**: nenhum
**Requirement**: N/A (fundação técnica — suporta ING-01, ING-03, ING-10, ING-11)

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] `get_connection()` retorna conexão com `PRAGMA journal_mode=WAL` ativo
- [ ] `busy_timeout` configurado (ex.: 5000ms)
- [ ] Teste unitário confirma os dois pragmas ativos na conexão retornada
- [ ] Gate check passa: `pytest tests/unit`
- [ ] Test count: 2 testes passam (WAL ativo, busy_timeout configurado)

**Tests**: unit
**Gate**: quick

**Commit**: `feat(db): helper de conexao SQLite com WAL e busy_timeout`

---

### T3: DDL das tabelas de controle e camadas de fato + migração

**What**: Criar o schema SQL completo (`ingestion_runs`, `dataset_versions`,
`active_version`, `bruto_reclamacoes`, `tratado_reclamacoes`,
`agregado_indicadores_mensais`, view `agregado_indicadores_ativo`) exatamente conforme
`design.md` § Data Models, e um script `migrate.py` que aplica o schema de forma
idempotente (usa `CREATE TABLE IF NOT EXISTS` / equivalente).
**Where**: `app/db/schema.sql`, `app/db/migrate.py`
**Depends on**: T2
**Reuses**: `app/db/connection.py` (T2)
**Requirement**: N/A (fundação técnica — suporta todos os ING-*)

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] Rodar `migrate.py` duas vezes seguidas não gera erro (idempotente)
- [ ] Todas as tabelas e a view do design.md existem após a migração
- [ ] Constraints (`CHECK`, `UNIQUE`, `REFERENCES`) do design.md estão presentes
- [ ] Gate check passa: `pytest tests/unit`
- [ ] Test count: 3 testes passam (schema completo criado, idempotência, constraints ativas)

**Tests**: unit
**Gate**: quick

**Commit**: `feat(db): schema DDL das camadas bruto/tratado/agregado e migracao idempotente`

---

### T4: Gerenciador de Versão/Rollback (`version_manager`)

**What**: Implementar `activate(layer, version_id)`, `get_active(layer)` e
`rollback(layer, version_id)` sobre a tabela `active_version`, garantindo que só existe
uma versão ativa por camada por vez (ING-11, AC1/AC2).
**Where**: `app/db/version_manager.py`
**Depends on**: T3
**Reuses**: `app/db/connection.py` (T2), schema de T3
**Requirement**: ING-11

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] `activate` grava/atualiza a linha de `active_version` para a camada informada
- [ ] `get_active` retorna o `version_id` ativo atual da camada
- [ ] `rollback` reaponta `active_version` para uma versão anterior sem apagar a versão revertida de `dataset_versions`
- [ ] Duas versões existentes + rollback → versão revertida some de "ativa" mas continua presente em `dataset_versions`
- [ ] Gate check passa: `pytest tests/unit`
- [ ] Test count: 4 testes passam (activate, get_active, rollback, versão antiga preservada)

**Tests**: unit
**Gate**: quick

**Commit**: `feat(db): version_manager com activate/get_active/rollback (ING-11)`

---

### T5: Fixture CSV sintético para desenvolvimento (ING-12)

**What**: Criar um gerador de CSV sintético seguindo o layout assumido em
`spec.md` (empresa, segmento, assunto, UF, data_abertura, data_resposta, resultado,
nota_satisfacao), incluindo os casos de borda exigidos: ≥2 variantes de grafia do mesmo
nome de empresa, uma duplicata exata, registros de um mês fechado e de um mês em
andamento, e ao menos um registro sem `nota_satisfacao`. Persistir a saída gerada em
`tests/fixtures/reclamacoes_sample.csv` para uso como dado "golden" nas próximas tasks.
**Where**: `scripts/generate_fixture.py`, `tests/fixtures/reclamacoes_sample.csv`
**Depends on**: T1
**Reuses**: nenhum
**Requirement**: ING-12

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] CSV gerado contém exatamente as colunas assumidas no spec.md
- [ ] Contém ≥2 variantes de grafia da mesma empresa (ex.: "Empresa X S.A.", "EMPRESA X SA")
- [ ] Contém 1 duplicata exata de reclamação
- [ ] Contém registros de um mês fechado e de um mês em andamento (mês corrente)
- [ ] Contém ao menos 1 registro com `nota_satisfacao` vazia/nula
- [ ] Valores esperados (índice de solução, etc.) para o mês fechado são calculáveis manualmente e documentados em comentário no script (servem de golden data para T12/T13)
- [ ] Gate check passa: `pytest tests/unit`
- [ ] Test count: 1 teste passa (fixture contém todas as colunas e casos de borda exigidos)

**Tests**: unit
**Gate**: quick

**Commit**: `test(fixtures): gerador de CSV sintetico com casos de borda (ING-12)`

---

### T6: Validador de Schema (ING-02)

**What**: Implementar `validate(csv_path) -> SchemaValidationResult` que confirma que o
CSV tem exatamente as colunas esperadas (conjunto definido em `spec.md` Assumptions),
identificando colunas divergentes/faltantes/adicionais, e distinguindo "arquivo
vazio/corrompido" de "schema inválido".
**Where**: `app/ingestion/schema_validator.py`
**Depends on**: T1, T5
**Reuses**: `tests/fixtures/reclamacoes_sample.csv` (T5) para os testes
**Requirement**: ING-02

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] CSV com todas as colunas esperadas → `SchemaValidationResult` OK
- [ ] CSV com coluna faltante → resultado inválido, identificando a(s) coluna(s) faltante(s)
- [ ] CSV com coluna renomeada/adicional incompatível → resultado inválido, identificando a(s) coluna(s) divergente(s)
- [ ] CSV vazio → erro distinto de "schema inválido" (ex.: "arquivo vazio/corrompido")
- [ ] CSV corrompido (não parseável) → erro distinto de "schema inválido"
- [ ] Gate check passa: `pytest tests/unit`
- [ ] Test count: 5 testes passam (um por cenário acima)

**Tests**: unit
**Gate**: quick

**Commit**: `feat(ingestion): validador de schema do CSV oficial (ING-02)`

---

### T7: Camada Bruta — writer com versionamento (ING-01, ING-03)

**What**: Implementar `store_raw(csv_path, run_id) -> version_id` que grava o CSV sem
alteração em `bruto_reclamacoes`, cria uma nova linha em `dataset_versions`
(`layer='bruto'`) vinculada ao `run_id`, e atualiza `ingestion_runs` com
timestamp/quantidade de linhas/checksum. Reingestão do mesmo período sempre cria nova
versão, nunca sobrescreve.
**Where**: `app/ingestion/raw_layer.py`
**Depends on**: T3, T4, T6
**Reuses**: `app/db/connection.py` (T2), `app/db/version_manager.py` (T4), schema (T3)
**Requirement**: ING-01, ING-03

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] `store_raw` grava linhas do CSV sem transformação em `bruto_reclamacoes`
- [ ] Nova linha em `dataset_versions` (`layer='bruto'`) criada com `row_count` correto
- [ ] `ingestion_runs` atualizado com `finished_at`, `status='success'`, `row_count`, `source_checksum`
- [ ] Chamar `store_raw` duas vezes para o mesmo período cria duas versões distintas (nenhuma sobrescrita)
- [ ] Gate check passa: `pytest tests/unit`
- [ ] Test count: 4 testes passam (gravação fiel, versão criada, run atualizado, reingestão não sobrescreve)

**Tests**: unit
**Gate**: quick

**Commit**: `feat(ingestion): camada bruta versionada (ING-01, ING-03)`

---

### T8: Endpoint de Ingestão (FastAPI)

**What**: Criar a aplicação FastAPI (`app/main.py`) e o endpoint
`POST /ingest {source_path, period} -> 202 {run_id}` e `GET /ingest/{run_id} ->
{status, row_count, error_message}`, orquestrando: cria `ingestion_runs` (status
running) → chama Validador de Schema (T6) → se inválido, marca `failed` com
`error_message` e retorna erro sem gravar nada; se válido, chama `store_raw` (T7) e
marca `success`.
**Where**: `app/ingestion/endpoint.py`, `app/main.py`
**Depends on**: T6, T7
**Reuses**: `app/ingestion/schema_validator.py` (T6), `app/ingestion/raw_layer.py` (T7)
**Requirement**: ING-01, ING-02, ING-03

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] `POST /ingest` com CSV válido (fixture) retorna `202` e cria nova versão bruta
- [ ] `POST /ingest` com CSV inválido (coluna removida) retorna erro explícito citando a(s) coluna(s), sem gravar nenhuma versão
- [ ] `POST /ingest` com CSV vazio/corrompido retorna erro distinguindo esse caso de "schema inválido"
- [ ] `GET /ingest/{run_id}` retorna status/row_count/error_message corretos após uma execução
- [ ] `POST /ingest` chamado duas vezes para o mesmo período cria duas versões (não sobrescreve)
- [ ] Gate check passa: `pytest tests/unit tests/integration`
- [ ] Test count: 5 testes de integração passam (um por cenário acima)

**Tests**: integration
**Gate**: full

**Commit**: `feat(ingestion): endpoint HTTP de disparo manual da ingestao (ING-01/02/03)`

---

### T9: Normalizador (encoding/datas) (ING-04)

**What**: Implementar `normalize(raw_rows) -> Iterable[dict]` que padroniza encoding e
formato de data (para ISO 8601) antes da etapa de fuzzy match.
**Where**: `app/curation/normalizer.py`
**Depends on**: T5
**Reuses**: `tests/fixtures/reclamacoes_sample.csv` (T5) para os testes
**Requirement**: ING-04

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] Datas em formatos distintos no fixture são normalizadas para um único padrão (ISO 8601)
- [ ] Encoding inconsistente (ex.: caracteres mal decodificados) é corrigido
- [ ] Linhas sem alteração necessária permanecem semanticamente idênticas após normalização
- [ ] Gate check passa: `pytest tests/unit`
- [ ] Test count: 3 testes passam (normalização de data, normalização de encoding, idempotência)

**Tests**: unit
**Gate**: quick

**Commit**: `feat(curation): normalizador de encoding e datas (ING-04)`

---

### T10: Módulo de Fuzzy Match de Empresa (ING-05, ING-07)

**What**: Implementar `match_companies(names) -> MatchResult` usando `rapidfuzz`, com
blocking key (primeira palavra normalizada) antes do fuzzy match completo
(`rapidfuzz.process.cdist`), aplicando threshold ≥92 (merge automático), 80-91 (fila de
revisão amostral), <80 (entidades distintas) — conforme Tech Decisions do design.md.
**Where**: `app/curation/company_matcher.py`
**Depends on**: T1, T5
**Reuses**: `tests/fixtures/reclamacoes_sample.csv` (T5) para os testes
**Requirement**: ING-05, ING-07

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] Variantes de grafia da mesma empresa no fixture (score ≥92) são agrupadas na mesma entidade
- [ ] Par de nomes com score 80-91 é mantido como entidades separadas E aparece na fila de revisão (`review_queue`)
- [ ] Nomes claramente distintos (score <80) permanecem como entidades separadas e não entram na fila de revisão
- [ ] Blocking key reduz o conjunto de comparações (não é O(n²) puro) — validado por teste que conta comparações realizadas
- [ ] Gate check passa: `pytest tests/unit`
- [ ] Test count: 4 testes passam (merge automático, fila de revisão, entidades distintas, blocking aplicado)

**Tests**: unit
**Gate**: quick

**Commit**: `feat(curation): fuzzy match de empresa com rapidfuzz e fila de revisao (ING-05, ING-07)`

---

### T11: Camada Tratada — writer com dedupe (ING-06) e wiring completo

**What**: Implementar `store_treated(normalized_rows, source_version_id) -> version_id`
que: aplica `normalizer` (T9) e `company_matcher` (T10) sobre a camada bruta ativa,
remove duplicatas exatas de reclamação mantendo uma ocorrência, grava
`tratado_reclamacoes` com `empresa_entidade_id` resolvido, cria nova linha em
`dataset_versions` (`layer='tratado'`, `source_version_id` apontando para a versão
bruta), e disponibiliza a amostra de revisão (`review_queue` de T10) para consulta.
**Where**: `app/curation/treated_layer.py`
**Depends on**: T4, T7, T9, T10
**Reuses**: `app/curation/normalizer.py` (T9), `app/curation/company_matcher.py` (T10),
`app/db/version_manager.py` (T4), camada bruta de T7
**Requirement**: ING-04, ING-05, ING-06, ING-07

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] Duplicata exata do fixture é removida, mantendo apenas 1 ocorrência
- [ ] Registros com nomes de empresa variantes (fixture) recebem o mesmo `empresa_entidade_id`
- [ ] Nova versão `tratado` criada em `dataset_versions` com `source_version_id` apontando para a versão bruta de origem
- [ ] Amostra de revisão (pares 80-91 do fuzzy match) fica acessível para consulta após o processamento
- [ ] Gate check passa: `pytest tests/unit`
- [ ] Test count: 4 testes passam (dedupe, entidade unificada, versionamento/lineage, amostra de revisão acessível)

**Tests**: unit
**Gate**: quick

**Commit**: `feat(curation): camada tratada com normalizacao, fuzzy match e dedupe (ING-04/05/06/07)`

---

### T12: Calculador de Indicadores — cálculo e regra de mês fechado (ING-08, ING-09)

**What**: Implementar `is_month_closed(period) -> bool` e
`calculate(treated_version_id, period) -> version_id`, calculando índice de solução
oficial, índice de solução estrito, tempo médio de resposta e nota média, agrupados por
empresa e segmento, apenas para meses fechados; recusa explicitamente o cálculo para o
mês corrente em andamento.
**Where**: `app/aggregation/indicators.py`
**Depends on**: T11
**Reuses**: camada tratada de T11, valores golden documentados no fixture (T5)
**Requirement**: ING-08, ING-09

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] Índice de solução oficial, índice de solução estrito, tempo médio de resposta e nota média calculados sobre o mês fechado do fixture batem com os valores de referência documentados em T5
- [ ] Indicadores agrupados corretamente por empresa e por segmento
- [ ] `is_month_closed` retorna `False` para o mês em andamento do fixture e `calculate` recusa o cálculo para esse período com erro explícito
- [ ] Gate check passa: `pytest tests/unit`
- [ ] Test count: 4 testes passam (índice oficial, índice estrito, tempo médio + nota média, recusa de mês aberto)

**Tests**: unit
**Gate**: quick

**Commit**: `feat(aggregation): calculo de indicadores por mes fechado (ING-08, ING-09)`

---

### T13: Versionamento e reprodutibilidade da camada agregada (ING-10)

**What**: Estender `calculate` (T12) para gravar cada execução como uma nova linha em
`dataset_versions` (`layer='agregado'`, `source_version_id` apontando para a versão
tratada), sem nunca sobrescrever versões anteriores; garantir que rodar `calculate` duas
vezes com a mesma versão tratada de entrada produz o mesmo resultado numérico
(reprodutibilidade).
**Where**: `app/aggregation/indicators.py` (extensão)
**Depends on**: T4, T12
**Reuses**: `app/db/version_manager.py` (T4)
**Requirement**: ING-10

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] Cada chamada a `calculate` cria uma nova linha em `dataset_versions` (`layer='agregado'`) com lineage correto (`source_version_id`)
- [ ] Duas execuções consecutivas sobre a mesma versão tratada de entrada produzem os mesmos valores numéricos de indicadores (comparação linha a linha)
- [ ] Versões agregadas anteriores permanecem intactas em `agregado_indicadores_mensais` após uma nova execução
- [ ] Gate check passa: `pytest tests/unit tests/integration`
- [ ] Test count: 3 testes passam (nova versão + lineage, reprodutibilidade, versões antigas preservadas)

**Tests**: integration
**Gate**: full

**Commit**: `feat(aggregation): versionamento e reprodutibilidade da camada agregada (ING-10)`

---

### T14: Orquestração ponta a ponta e rollback (ING-11 + fluxo completo)

**What**: Criar `app/pipeline/run_ingestion.py` que orquestra o fluxo completo (endpoint
→ bruto → tratado → agregado → `version_manager.activate` na camada agregada), e expor
a operação de rollback (`version_manager.rollback`) sobre a camada agregada, validando
que a view `agregado_indicadores_ativo` resolve sempre para a versão ativa corrente.
**Where**: `app/pipeline/run_ingestion.py`
**Depends on**: T8, T11, T13
**Reuses**: endpoint (T8), camada tratada (T11), calculador com versionamento (T13),
`version_manager` (T4)
**Requirement**: ING-11 (+ integra ING-01..ING-10 em fluxo único)

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] Execução completa sobre o fixture (endpoint → bruto → tratado → agregado) roda sem intervenção manual e ativa a nova versão agregada
- [ ] `agregado_indicadores_ativo` retorna os dados da versão recém-ativada
- [ ] Gerar uma segunda versão agregada e fazer rollback para a primeira: view volta a refletir a primeira versão, a segunda permanece presente (não deletada) porém inativa
- [ ] Gate check passa: `pytest tests/unit tests/integration`
- [ ] Test count: 3 testes de integração passam (fluxo completo ativa versão, view reflete versão ativa, rollback preserva versão revertida)

**Tests**: integration
**Gate**: full

**Commit**: `feat(pipeline): orquestracao ponta a ponta e rollback da camada agregada (ING-11)`

---

## Phase Execution Map

```
Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6

Phase 1:  T1 ──→ T2 ──→ T3 ──→ T4
Phase 2:  T5 (depende de T1)
Phase 3:  T6 (depende de T1, T5) ──→ T7 (depende de T3, T4, T6) ──→ T8 (depende de T6, T7)
Phase 4:  T9 (depende de T5) ──→ T10 (depende de T1, T5) ──→ T11 (depende de T4, T7, T9, T10)
Phase 5:  T12 (depende de T11) ──→ T13 (depende de T4, T12)
Phase 6:  T14 (depende de T8, T11, T13)
```

Execution is strictly sequential — there is no intra-phase parallelism. A single agent
(or batch worker) works one task at a time, in order.

**Batching for Execute** (14 tasks total, > ~8 → sub-agent delegation offered per skill rules):

- **Batch 1** (Phases 1–3, 8 tasks): T1, T2, T3, T4, T5, T6, T7, T8
- **Batch 2** (Phases 4–6, 6 tasks): T9, T10, T11, T12, T13, T14

Batch cut lands exactly on the Phase 3/Phase 4 boundary — no phase is split.

---

## Task Granularity Check

| Task                                   | Scope                          | Status      |
| --------------------------------------- | -------------------------------- | ------------ |
| T1: Scaffold do projeto                 | 1 estrutura de projeto (config)  | ✅ Granular |
| T2: Helper de conexão SQLite            | 1 módulo                         | ✅ Granular |
| T3: DDL + migração                      | 1 schema + 1 script (cohesivos)  | ✅ Granular |
| T4: Version manager                     | 1 módulo                         | ✅ Granular |
| T5: Fixture CSV sintético               | 1 script + 1 artefato de dado    | ✅ Granular |
| T6: Validador de schema                 | 1 módulo/função                  | ✅ Granular |
| T7: Camada bruta (writer)               | 1 módulo/função                  | ✅ Granular |
| T8: Endpoint de ingestão                | 1 endpoint (2 rotas cohesivas)   | ✅ Granular |
| T9: Normalizador                        | 1 módulo/função                  | ✅ Granular |
| T10: Fuzzy match de empresa             | 1 módulo/função                  | ✅ Granular |
| T11: Camada tratada (writer + wiring)   | 1 módulo, integra T9/T10 (cohesivo) | ✅ Granular |
| T12: Calculador de indicadores          | 1 módulo/função                  | ✅ Granular |
| T13: Versionamento/reprodutibilidade    | extensão de 1 módulo (T12)       | ✅ Granular |
| T14: Orquestração ponta a ponta         | 1 módulo de orquestração          | ✅ Granular |

---

## Diagram-Definition Cross-Check

| Task | Depends On (task body) | Diagram Shows                | Status    |
| ---- | ----------------------- | ------------------------------ | --------- |
| T1   | None                     | (início da Phase 1)            | ✅ Match |
| T2   | T1                       | T1 → T2                        | ✅ Match |
| T3   | T2                       | T2 → T3                        | ✅ Match |
| T4   | T3                       | T3 → T4                        | ✅ Match |
| T5   | T1                       | "T5 (depende de T1)"           | ✅ Match |
| T6   | T1, T5                   | "T6 (depende de T1, T5)"       | ✅ Match |
| T7   | T3, T4, T6               | "T7 (depende de T3, T4, T6)"   | ✅ Match |
| T8   | T6, T7                   | "T8 (depende de T6, T7)"       | ✅ Match |
| T9   | T5                       | "T9 (depende de T5)"           | ✅ Match |
| T10  | T1, T5                   | "T10 (depende de T1, T5)"      | ✅ Match |
| T11  | T4, T7, T9, T10          | "T11 (depende de T4, T7, T9, T10)" | ✅ Match |
| T12  | T11                      | "T12 (depende de T11)"         | ✅ Match |
| T13  | T4, T12                  | "T13 (depende de T4, T12)"     | ✅ Match |
| T14  | T8, T11, T13             | "T14 (depende de T8, T11, T13)"| ✅ Match |

No task depends on a task in a later phase — all dependencies point backward or within
the same phase.

---

## Test Co-location Validation

| Task | Code Layer Created/Modified              | Matrix Requires | Task Says | Status |
| ---- | ------------------------------------------ | ---------------- | --------- | ------ |
| T1   | Config/Schema (scaffold)                    | none              | none      | ✅ OK  |
| T2   | Acesso a dados (connection.py)              | unit              | unit      | ✅ OK  |
| T3   | Acesso a dados (schema.sql, migrate.py)     | unit              | unit      | ✅ OK  |
| T4   | Domínio (version_manager.py)                | unit              | unit      | ✅ OK  |
| T5   | Fixture sintético                           | unit              | unit      | ✅ OK  |
| T6   | Domínio (schema_validator.py)                | unit              | unit      | ✅ OK  |
| T7   | Domínio (raw_layer.py)                       | unit              | unit      | ✅ OK  |
| T8   | Endpoint HTTP (endpoint.py, main.py)         | integration       | integration | ✅ OK |
| T9   | Domínio (normalizer.py)                      | unit              | unit      | ✅ OK  |
| T10  | Domínio (company_matcher.py)                 | unit              | unit      | ✅ OK  |
| T11  | Domínio (treated_layer.py)                   | unit              | unit      | ✅ OK  |
| T12  | Domínio (indicators.py)                      | unit              | unit      | ✅ OK  |
| T13  | Pipeline ponta a ponta (indicators.py, versionamento) | integration | integration | ✅ OK |
| T14  | Pipeline ponta a ponta (run_ingestion.py)    | integration       | integration | ✅ OK  |

No violations — every task's `Tests` field matches its highest-required layer in the
Test Coverage Matrix. No task defers its tests to a later task.

---

## Requirement Coverage

| Requirement ID | Covered by Task(s) |
| --------------- | -------------------- |
| ING-01           | T7, T8                |
| ING-02           | T6, T8                |
| ING-03           | T7, T8                |
| ING-04           | T9, T11                |
| ING-05           | T10, T11               |
| ING-06           | T11                    |
| ING-07           | T10, T11               |
| ING-08           | T12                    |
| ING-09           | T12                    |
| ING-10           | T13                    |
| ING-11           | T4, T14                |
| ING-12           | T5                     |

All 12 requirements from `spec.md` Requirement Traceability are mapped to at least one task.
