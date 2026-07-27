# Ingestão e Curadoria de Dados — Validation

**Date**: 2026-07-26
**Spec**: `.specs/features/ingestao-curadoria/spec.md`
**Diff range**: `abac20f..HEAD` (d129366)
**Verifier**: independent sub-agent (author ≠ verifier)

---

## Histórico

**Rodada 1 (FAIL ❌)** — commit `bc37be0`, 45 testes. Gate de Build reprovado por 3
erros de `ruff` (`DTZ007` × 2 em `indicators.py`, `DTZ011` em `generate_fixture.py`).
Sensor: 3/3 mutantes mortos. 2 gaps reais de cobertura identificados: (1) sem teste de
integração para CSV corrompido no endpoint; (2) sem teste que force `resultado` a
assumir um 3º valor ("Em Analise") dentro do mês fechado para provar que índice oficial
e estrito de fato divergem. Texto completo da rodada 1 preservado no histórico do git
(`git show bc37be0:.specs/features/ingestao-curadoria/validation.md`).

**Rodada 2 (esta rodada) — PASS ✅**. Três commits de fix aplicados desde a rodada 1:
`93303bc` (ruff), `971ce32` (teste CSV corrompido no endpoint), `d129366` (teste
divergência oficial/estrito). Todos os 3 gaps confirmados corrigidos com evidência.
Gate limpo (47 passed, ruff 0 erros). Sensor: 2/2 novas mutações mortas. Sem scope
creep. Feature pronta para ser marcada como Verified.

---

## Re-verificação dos 3 Gaps da Rodada 1

| # | Gap (Rodada 1) | Commit de fix | Evidência (file:line + asserção) | Resultado |
| - | --------------- | -------------- | --------------------------------- | --------- |
| 1 | `ruff check .` falhava (`DTZ007` × 2, `DTZ011` × 1) | `93303bc` | [app/aggregation/indicators.py:59-60](../../../app/aggregation/indicators.py#L59-L60) — `_response_days` agora usa `date.fromisoformat(data_abertura)` / `date.fromisoformat(data_resposta)` em vez de `datetime.strptime` sem timezone; [scripts/generate_fixture.py:62](../../../scripts/generate_fixture.py#L62) — `today or datetime.now(UTC).date()` em vez de `date.today()`. Confirmado por execução real: `uv run ruff check .` → **exit 0, "All checks passed!"** | ✅ Confirmado |
| 2 | Sem teste de integração para CSV corrompido no endpoint | `971ce32` | [tests/integration/test_ingestion_endpoint.py:120-153](../../../tests/integration/test_ingestion_endpoint.py#L120-L153) `test_post_ingest_with_corrupted_csv_distinguishes_from_invalid_schema` — grava CSV com aspas não fechadas, `assert response.status_code == 422`, `assert "corrompido" in detail.lower()`, `assert "schema invalido" not in detail.lower()`, `assert version_count == 0`. Código correspondente confirmado em [app/ingestion/endpoint.py:70-71](../../../app/ingestion/endpoint.py#L70-L71) (`if result.error == "corrupted_file": return "Arquivo de origem corrompido (nao parseavel)."`) | ✅ Confirmado |
| 3 | Sem teste do ramo de 3º valor de `resultado` (divergência oficial/estrito) no mês fechado | `d129366` | [tests/unit/aggregation/test_indicators.py:127-158](../../../tests/unit/aggregation/test_indicators.py#L127-L158) `test_calculate_indice_oficial_and_estrito_diverge_with_inconclusive_resultado` — insere 3 registros sintéticos (Resolvido, Nao Resolvido, "Em Analise") diretamente na camada tratada e afirma `row[0] == pytest.approx(2/3)` (oficial), `row[1] == pytest.approx(1/3)` (estrito), `row[0] != row[1]`. Lógica correspondente confirmada em [app/aggregation/indicators.py:68-73](../../../app/aggregation/indicators.py#L68-L73) (`oficial_resolvidas` conta `RESOLVIDO` OU valor fora do binário; `estrito_resolvidas` conta só `RESOLVIDO`) | ✅ Confirmado |

**Fixes confirmados**: 3/3, todos com evidência real de `file:line` + asserção (não apenas confiando na mensagem do commit).

---

## Gate Check (Build, mandatório — Rodada 2)

- **Gate command**: `uv run pytest && uv run ruff check .`
- **Result**: pytest → **47 passed, 0 failed, 0 skipped**. `ruff check .` → **0 erros, exit 0** ("All checks passed!").
- **Test count Rodada 1**: 45. **Test count Rodada 2**: 47. **Delta**: +2 (os dois testes de fix: CSV corrompido no endpoint + divergência oficial/estrito).
- **Skipped tests**: nenhum.
- **Failures**: nenhuma.

**Build gate PASS** — protocolo de validate.md satisfeito (exit 0 em ambos os comandos).

---

## Discrimination Sensor (mutações novas desta rodada)

Mutações aplicadas apenas nos trechos novos/corrigidos desta rodada de fix, em estado
descartável, revertidas com `git checkout -- <arquivo>` imediatamente após confirmação.
`git status --porcelain` confirmado limpo (exceto diretórios pré-existentes não
rastreados `.agents/`, `.github/`, `.specs/`, `docs/` — não relacionados a esta
validação) após cada reversão e ao final.

| # | File:line | Description | Killed? |
| - | --------- | ------------ | ------- |
| 1 | `app/aggregation/indicators.py:68-72` | Removeu a cláusula `or r["resultado"] not in (RESOLVIDO, NAO_RESOLVIDO)` de `oficial_resolvidas`, fazendo oficial contar apenas `Resolvido` (igual a estrito) — elimina a divergência que o novo teste prova | ✅ Killed — `test_calculate_indice_oficial_and_estrito_diverge_with_inconclusive_resultado` falhou: `assert 0.333... == 0.666... ± 1e-4` |
| 2 | `app/ingestion/endpoint.py:85` | Mudou `if not result.ok:` para `if not result.ok and result.error != "corrupted_file":`, fazendo o endpoint tentar prosseguir (bypassar o erro 422) para CSV corrompido | ✅ Killed — `test_post_ingest_with_corrupted_csv_distinguishes_from_invalid_schema` falhou (exceção de parsing do pandas propagada em vez do 422 esperado, já que a validação de schema deixou de barrar o arquivo corrompido antes de `store_raw`) |

**Sensor depth**: lightweight (2 mutations, focadas nos trechos novos desta rodada)
**Result**: 2/2 killed — ✅ PASS

---

## Scope Check (sem repetir Code Quality Check completo)

Confirmado via `git show --stat` dos 3 commits de fix — cada um tocou exatamente os
arquivos esperados, sem scope creep:

| Commit | Arquivos tocados | Esperado? |
| ------ | ------------------ | --------- |
| `93303bc` (fix ruff) | `app/aggregation/indicators.py` (+3/-3), `scripts/generate_fixture.py` (+2/-2) | ✅ Exatamente os 2 arquivos apontados no Fix 1 da rodada 1 |
| `971ce32` (teste CSV corrompido) | `tests/integration/test_ingestion_endpoint.py` (+33) | ✅ Apenas o arquivo de teste apontado no Fix 2 da rodada 1; nenhum código de produção tocado |
| `d129366` (teste divergência oficial/estrito) | `tests/unit/aggregation/test_indicators.py` (+59) | ✅ Apenas o arquivo de teste apontado no Fix 3 da rodada 1; nenhum código de produção tocado |

Nenhum arquivo fora do escopo dos 3 fixes foi modificado.

---

## Itens não re-testados (fora do escopo desta rodada, por decisão do processo)

- **Fix 4 da rodada 1** (teste de reingestão com CSV literalmente "diferente", não
  idêntico) — não fazia parte do escopo dos 3 commits desta rodada de fix e não foi
  solicitado nesta iteração. Continua como gap Minor em aberto, não bloqueador.
- **Risco arquitetural da fila de revisão do fuzzy match em memória** (ING-07,
  `_review_queues` não persistida) — conforme instrução desta rodada, é uma limitação
  arquitetural já auto-documentada como `SPEC_DEVIATION` em tasks.md, aceita como
  conhecida, não tratada como gap de teste.

---

## Task Completion (Rodada 1, referência)

| Task | Status  | Notes                                                                 |
| ---- | ------- | ---------------------------------------------------------------------- |
| T1   | ✅ Done | Scaffold present, `Dockerfile` builds (confirmed by prior terminal history: `docker build` exit 0) |
| T2   | ✅ Done | [app/db/connection.py](../../../app/db/connection.py) — WAL + busy_timeout |
| T3   | ✅ Done | [app/db/schema.sql](../../../app/db/schema.sql), [app/db/migrate.py](../../../app/db/migrate.py) |
| T4   | ✅ Done | [app/db/version_manager.py](../../../app/db/version_manager.py) |
| T5   | ✅ Done | [scripts/generate_fixture.py](../../../scripts/generate_fixture.py) |
| T6   | ✅ Done | [app/ingestion/schema_validator.py](../../../app/ingestion/schema_validator.py) |
| T7   | ✅ Done | [app/ingestion/raw_layer.py](../../../app/ingestion/raw_layer.py) |
| T8   | ✅ Done | [app/ingestion/endpoint.py](../../../app/ingestion/endpoint.py), [app/main.py](../../../app/main.py) |
| T9   | ✅ Done | [app/curation/normalizer.py](../../../app/curation/normalizer.py) |
| T10  | ✅ Done | [app/curation/company_matcher.py](../../../app/curation/company_matcher.py) |
| T11  | ✅ Done | [app/curation/treated_layer.py](../../../app/curation/treated_layer.py) — signature deviates from design.md (self-documented SPEC_DEVIATION) |
| T12  | ✅ Done | [app/aggregation/indicators.py](../../../app/aggregation/indicators.py) |
| T13  | ✅ Done | extension of same file, versioning verified |
| T14  | ✅ Done | [app/pipeline/run_ingestion.py](../../../app/pipeline/run_ingestion.py) |

All 14 tasks implemented and committed (hashes match tasks.md Status line). Two self-documented `SPEC_DEVIATION`s exist at the top of tasks.md (T11 signature / in-memory review queue; T12/T13 `resultado` value assumption) — both re-verified below.

---

## Spec-Anchored Acceptance Criteria

### P1: Ingestão bruta com validação de schema (ING-01, ING-02, ING-03)

| Criterion (WHEN X THEN Y) | Spec-defined outcome | `file:line` + assertion | Result |
| --- | --- | --- | --- |
| AC1: CSV válido → gravado sem alteração em nova versão bruta | Linha gravada idêntica à origem; nova versão criada | [app/ingestion/raw_layer.py:21](../../../app/ingestion/raw_layer.py#L21) `store_raw` — [tests/unit/ingestion/test_raw_layer.py:45](../../../tests/unit/ingestion/test_raw_layer.py#L45) `assert rows[0] == (...)` (tupla exata da linha 1 do fixture) e `:56` `assert rows[3][-1] is None` (nota ausente preservada como NULL, não inventada) | ✅ PASS |
| AC2: CSV com coluna faltante/renomeada/adicional → rejeitado com erro explícito citando coluna(s), nada gravado | `ok=False`, `missing_columns`/`unexpected_columns` populados; endpoint retorna erro citando a coluna | [app/ingestion/schema_validator.py:33](../../../app/ingestion/schema_validator.py#L33) — [tests/unit/ingestion/test_schema_validator.py:43-44](../../../tests/unit/ingestion/test_schema_validator.py#L43-L44) (`missing_columns == ["nota_satisfacao"]`) e `:61-62` (renomeada: `missing==["empresa"]`, `unexpected==["empresa_nome"]`); endpoint: [tests/integration/test_ingestion_endpoint.py:77-78](../../../tests/integration/test_ingestion_endpoint.py#L77-L78) (`422`, `"nota_satisfacao" in detail`) e `:88` (`version_count == 0`) | ✅ PASS |
| AC3: Ingestão concluída → registra timestamp, row_count, checksum | `ingestion_runs.finished_at/row_count/source_checksum` preenchidos (sha256, 64 hex) | [app/ingestion/raw_layer.py:21](../../../app/ingestion/raw_layer.py#L21) (`_checksum_file`, `UPDATE ingestion_runs`) — [tests/unit/ingestion/test_raw_layer.py:76](../../../tests/unit/ingestion/test_raw_layer.py#L76) e teste `test_store_raw_updates_ingestion_run_metadata` (`len(source_checksum) == 64`) | ✅ PASS |
| AC4: Reingestão do mesmo período → nova versão, sem sobrescrever | `version_id` distinto por chamada; contagem de versões cresce | [tests/unit/ingestion/test_raw_layer.py:114](../../../tests/unit/ingestion/test_raw_layer.py#L114) (`version_id_1 != version_id_2`), `:132-134` (`version_count==2`, ambas com 6 linhas); endpoint: [tests/integration/test_ingestion_endpoint.py:151](../../../tests/integration/test_ingestion_endpoint.py#L151) e `:161` (`version_count==2`) | ✅ PASS |

**Edge case (spec.md § Edge Cases) — CSV vazio/corrompido → erro explícito, nada gravado**: [tests/unit/ingestion/test_schema_validator.py:71-74](../../../tests/unit/ingestion/test_schema_validator.py#L71-L74) (`error=="empty_file"`) e `:87-90` (`error=="corrupted_file"`) cobrem o comportamento unitário. No nível de integração (endpoint), apenas o caso "vazio" é exercitado ([tests/integration/test_ingestion_endpoint.py:104-107](../../../tests/integration/test_ingestion_endpoint.py#L104-L107)) — **não há teste de integração para CSV corrompido/não-parseável no endpoint**, o que o Test Coverage Matrix de tasks.md exige explicitamente para a camada de endpoint ("todas as rotas do escopo: caminho feliz + cada edge case listado"). ⚠️ **Gap parcial** (unit coberto, integration não).

---

### P1: Normalização e curadoria (ING-04, ING-05, ING-06, ING-07)

| Criterion | Spec-defined outcome | `file:line` + assertion | Result |
| --- | --- | --- | --- |
| AC1: Encoding e data normalizados antes de gravar na tratada | Datas em ISO 8601; mojibake corrigido | [app/curation/normalizer.py:35](../../../app/curation/normalizer.py#L35) — [tests/unit/curation/test_normalizer.py:13](../../../tests/unit/curation/test_normalizer.py#L13) (`data_abertura == "2026-06-05"`) e `:29` (mojibake `"ComÃ©rcio"` → `"Comércio"`) | ✅ PASS |
| AC2: Nomes similares (fuzzy ≥ limiar) → mesma entidade | Score ≥92 = merge automático (Tech Decision de design.md) | [app/curation/company_matcher.py:36](../../../app/curation/company_matcher.py#L36), threshold em `:15` — [tests/unit/curation/test_company_matcher.py:4](../../../tests/unit/curation/test_company_matcher.py#L4) e [tests/unit/curation/test_treated_layer.py:94](../../../tests/unit/curation/test_treated_layer.py#L94) (`rows_by_assunto[...] ==`) | ✅ PASS |
| AC3: Duplicata exata → removida, mantendo 1 ocorrência | `tratado_reclamacoes` tem N-1 linhas quando há 1 duplicata | [app/curation/treated_layer.py:53](../../../app/curation/treated_layer.py#L53) `_dedupe_exact` — [tests/unit/curation/test_treated_layer.py:70](../../../tests/unit/curation/test_treated_layer.py#L70) (`row_count == 5`, fixture tem 6 linhas com 1 duplicata) | ✅ PASS |
| AC4: Amostra de agrupamentos disponível para revisão amostral | Pares 80-91 acessíveis para consulta humana | [app/curation/treated_layer.py:35](../../../app/curation/treated_layer.py#L35) `get_review_queue` — [tests/unit/curation/test_treated_layer.py:152](../../../tests/unit/curation/test_treated_layer.py#L152) | ⚠️ **PASS com ressalva arquitetural**: fila mantida em dict de módulo em memória (`_review_queues`, não persistida em tabela) — já auto-documentado como SPEC_DEVIATION em tasks.md. Funciona para o teste/processo atual, mas não sobrevive a um restart do processo e não é consultável pela Fase 2 sem essa fila ser persistida. Não é um GAP de teste (o comportamento testado corresponde ao implementado), é um risco arquitetural em aberto que o próprio autor já sinalizou para revisão. |

**Edge case — fuzzy match ambíguo (80-91) → mantém separado + sinaliza fila**: [tests/unit/curation/test_company_matcher.py](../../../tests/unit/curation/test_company_matcher.py) `test_match_companies_flags_ambiguous_pair_for_review_without_merging` — ✅ coberto.

---

### P1: Cálculo de indicadores agregados (ING-08, ING-09)

| Criterion | Spec-defined outcome | `file:line` + assertion | Result |
| --- | --- | --- | --- |
| AC1: Mês fechado → índice oficial/estrito, tempo médio, nota média por empresa/segmento | Valores batem com golden data documentado em [scripts/generate_fixture.py](../../../scripts/generate_fixture.py) (Empresa X Telecom: 2/3, 7.0, 7.0; Empresa Y Varejo: 1.0, 3.0, 9.0) | [app/aggregation/indicators.py:90](../../../app/aggregation/indicators.py#L90) `calculate` — [tests/unit/aggregation/test_indicators.py:60](../../../tests/unit/aggregation/test_indicators.py#L60) (`row[0] == pytest.approx(2/3)`), `:72`, `:86-90` (todos os 4 valores golden) | ✅ PASS |
| AC2: Mês em andamento → cálculo recusado | `ValueError` explícito; nada gravado | [app/aggregation/indicators.py:37](../../../app/aggregation/indicators.py#L37) `is_month_closed` — [tests/unit/aggregation/test_indicators.py:98](../../../tests/unit/aggregation/test_indicators.py#L98) (`is_month_closed(OPEN_PERIOD) is False`) + `pytest.raises(ValueError)` na chamada de `calculate` | ✅ PASS |
| AC3: Cálculo concluído → nova versão agregada, sem sobrescrever | Nova linha em `dataset_versions` (`layer='agregado'`), lineage correto | [tests/integration/test_indicators_versioning.py:48](../../../tests/integration/test_indicators_versioning.py#L48) (`row == ("agregado", treated_version_id, "ready")`) | ✅ PASS |
| AC4: Reprodutibilidade — mesma entrada/versão → mesmo resultado | Valores numéricos idênticos entre execuções | [tests/integration/test_indicators_versioning.py:68](../../../tests/integration/test_indicators_versioning.py#L68) `test_calculate_twice_...` (`first_rows == second_rows`, apesar de `version_id` distinto) | ✅ PASS |

**Nota sobre SPEC_DEVIATION (T12/T13)**: spec.md/TDD não definem o valor literal de `resultado` para "não avaliada" — a distinção numérica entre índice oficial e estrito não é exercitada no fixture atual (ambos coincidem em 2/3, ver [app/aggregation/indicators.py:1-18](../../../app/aggregation/indicators.py#L1-L18) docstring de auto-declaração). **⚠️ Spec-precision gap confirmado**: não há teste que force `resultado` a assumir um terceiro valor (ex.: "Em Analise" dentro do mês fechado) para provar que a fórmula `oficial ≠ estrito` funciona quando os valores realmente divergem — o único registro com `resultado` fora do binário Resolvido/Nao Resolvido no fixture ("Em Analise", linha 5) está no mês **aberto**, que nunca é agregado. A lógica de `_calculate_group` (linha 64) trata esse terceiro caso, mas nenhum teste cobre esse ramo especificamente no mês fechado.

---

### P2: Versionamento e rollback (ING-11)

| Criterion | Spec-defined outcome | `file:line` + assertion | Result |
| --- | --- | --- | --- |
| AC1: 2+ versões → permite apontar qual está ativa | `activate`/`get_active` funcionam sobre `active_version` | [app/db/version_manager.py:14](../../../app/db/version_manager.py#L14) — [tests/unit/db/test_version_manager.py:34](../../../tests/unit/db/test_version_manager.py#L34), `:44` | ✅ PASS |
| AC2: Rollback → versão revertida mantida (não deletada), apenas inativa | `dataset_versions` preserva a linha; `active_version` muda | [app/db/version_manager.py:44](../../../app/db/version_manager.py#L44) `rollback` — [tests/unit/db/test_version_manager.py:77-78](../../../tests/unit/db/test_version_manager.py#L77-L78) e integração [tests/integration/test_run_ingestion.py:79](../../../tests/integration/test_run_ingestion.py#L79) (`second_still_present == 1`) | ✅ PASS |

---

### P1: Fixture CSV sintético (ING-12)

| Criterion | Spec-defined outcome | `file:line` + assertion | Result |
| --- | --- | --- | --- |
| AC1: Colunas assumidas presentes | 8 colunas exatas | [scripts/generate_fixture.py](../../../scripts/generate_fixture.py) `COLUMNS` — [tests/unit/fixtures/test_generate_fixture.py:6](../../../tests/unit/fixtures/test_generate_fixture.py#L6) (`reader.fieldnames == COLUMNS`) | ✅ PASS |
| AC2: Casos de borda mínimos (variantes empresa, duplicata exata, mês fechado/aberto, nota ausente) | Todos presentes | mesmo teste, linhas subsequentes (`empresa_variants`, `duplicate_count==1`, `len(periods)==2`, `nota_satisfacao==""`) | ✅ PASS |
| AC3: Fixture revisado quando fonte real voltar | Ação futura de processo, não comportamento de sistema testável agora | — | ⚠️ Spec-precision gap (não testável no estado atual; correto não ter teste, mas registrado explicitamente aqui) |
| AC4: Resultados esperados calculáveis manualmente a partir do fixture (golden data) | Valores batem com testes de indicadores | golden data documentado em [scripts/generate_fixture.py:1-24](../../../scripts/generate_fixture.py#L1-L24) e usado em [tests/unit/aggregation/test_indicators.py](../../../tests/unit/aggregation/test_indicators.py) | ✅ PASS |

**Status geral (Rodada 1)**: ❌ Gaps presentes (2 gaps concretos: cobertura de integração para CSV corrompido; ramo de `resultado` de terceiro valor no mês fechado não testado) + 2 spec-precision gaps já esperados (ambos documentados no próprio spec.md como decisão futura, não bugs). **Os 2 gaps concretos foram corrigidos na Rodada 2 — ver seção "Re-verificação dos 3 Gaps da Rodada 1" no topo deste documento.**

---

## Edge Cases (spec.md § Edge Cases, referência Rodada 1)

- [x] CSV vazio/corrompido → erro explícito, nada gravado — coberto no nível unitário; **parcialmente** no nível de integração (ver gap acima).
- [x] Fonte oficial indisponível ao chamar o endpoint — corretamente fora de escopo do sistema per design.md § Error Handling (endpoint só recebe referência de arquivo já local); não é um gap, é uma decisão de design documentada.
- [x] Fuzzy match ambíguo → mantém separado + sinaliza revisão — coberto.
- [x] Reingestão de mesmo período com CSV **diferente** → nova versão sem descartar a anterior — o código não distingue conteúdo (sempre cria nova versão independentemente do conteúdo, ver [app/ingestion/raw_layer.py:21](../../../app/ingestion/raw_layer.py#L21)), então o comportamento cobre a intenção do edge case. Porém os testes existentes ([tests/unit/ingestion/test_raw_layer.py:114](../../../tests/unit/ingestion/test_raw_layer.py#L114), [tests/integration/test_ingestion_endpoint.py:151](../../../tests/integration/test_ingestion_endpoint.py#L151)) reingerem o **mesmo** arquivo, não um arquivo com conteúdo diferente. ⚠️ Minor spec-precision gap — comportamento correto por construção (sem lógica de diff de conteúdo), mas o literal do edge case ("CSV diferente") nunca foi exercitado.

---

## Discrimination Sensor (Rodada 1, referência)

Todas as mutações foram aplicadas em `app/`, testadas e **revertidas antes do fim desta validação** (`git status --porcelain` e `git diff --stat` confirmados limpos após a última reversão; suite completa re-executada: 45 passed).

| # | File:line | Description | Killed? |
| - | --------- | ------------ | ------- |
| 1 | `app/aggregation/indicators.py:40` | Inverteu `is_month_closed`: `period < current_period` → `period > current_period` | ✅ Killed — 6/7 testes de `test_indicators.py` + `test_indicators_versioning.py` falharam com `ValueError: Periodo '2026-06' ainda esta em andamento` (o mês fechado passou a ser recusado) |
| 2 | `app/curation/company_matcher.py:15` | Trocou `MERGE_THRESHOLD = 92` por `60` (limiar errado) | ✅ Killed — 5 testes falharam (`test_company_matcher.py` ×3, `test_treated_layer.py` ×2), incluindo o teste que exige que "Empresa X S.A." e "Empresa Y Ltda" (score ~74) permaneçam distintas |
| 3 | `app/ingestion/raw_layer.py:32` | Removeu a criação de nova versão em `dataset_versions` ao reingerir — passou a reaproveitar a última versão `bruto` existente em vez de inserir uma nova | ✅ Killed — `test_store_raw_reingestion_of_same_period_creates_new_version_without_overwrite` (`assert 1 != 1`) e `test_post_ingest_twice_for_same_period_creates_two_versions` (`assert 1 == 2`) falharam |

**Sensor depth**: lightweight (3 mutations, default tier)
**Result**: 3/3 killed — ✅ PASS (nenhum mutante sobreviveu; a suite discrimina corretamente as 3 mudanças comportamentais de maior risco identificadas)

---

## Code Quality (Rodada 1, referência — não repetido integralmente na Rodada 2 por instrução; ver "Scope Check" no topo)

Amostra: 1 arquivo por camada (db, ingestion, curation, aggregation, pipeline).

| Principle | `app/db/version_manager.py` | `app/ingestion/raw_layer.py` | `app/curation/company_matcher.py` | `app/aggregation/indicators.py` | `app/pipeline/run_ingestion.py` |
| --- | --- | --- | --- | --- | --- |
| No features beyond what was asked | ✅ | ✅ | ✅ | ✅ | ✅ |
| No abstractions for single-use code | ✅ | ✅ | ✅ | ✅ | ✅ |
| No unnecessary "flexibility" added | ✅ | ✅ | ✅ | ✅ | ✅ |
| Only touched files required for task | ✅ | ✅ | ✅ | ✅ | ✅ |
| Didn't "improve" unrelated code | ✅ | ✅ | ✅ | ✅ | ✅ |
| Matches existing patterns/style | ✅ | ✅ | ✅ | ✅ | ✅ (reusa `endpoint.ingest` via env var em vez de duplicar lógica, conforme docstring do próprio módulo) |
| Would senior engineer approve? | ✅ | ✅ | ✅ | ⚠️ ver nota | ✅ |
| Tests map to ACs and are non-shallow | ✅ | ✅ | ✅ | ✅ | ✅ |
| Spec-anchored outcome check (valores exatos, não só "há assert") | ✅ | ✅ | ✅ | ✅ | ✅ |
| Per-layer Coverage Expectation met | ✅ | ✅ | ✅ | ⚠️ ramo `resultado` de 3º valor no mês fechado sem teste (ver gap acima) | ✅ |
| Todo teste em escopo mapeia para AC/edge case/Done-when (sem teste órfão) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Guidelines documentados seguidos | Test Coverage Matrix / coding-principles.md — seguidos | idem | idem | idem | idem |

**Nota (indicators.py)**: `_response_days` usa `datetime.strptime` sem timezone (linhas 59-60), disparando `ruff` `DTZ007` — ver Gate Check abaixo. Não é um problema de lógica (as datas são strings `YYYY-MM-DD` sem componente de hora), mas quebra o gate de lint mandatório.

**Nota (raw_layer.py / treated_layer.py)**: `_review_queues` em `treated_layer.py` é um dict de módulo (estado global mutável, cresce sem limite e não é limpo entre execuções de processo). É consistente com o SPEC_DEVIATION já documentado pelo autor, mas vale registrar como risco a resolver antes de "ING-07 = Verified" definitivo, conforme a própria tasks.md já recomenda.

---

## Gate Check (Rodada 1, referência — reprovado, corrigido na Rodada 2)

- **Gate command**: `uv run pytest && uv run ruff check .` (Build gate, tasks.md § Gate Check Commands)
- **Result**: pytest → 45 passed, 0 failed, 0 skipped. `ruff check .` → **3 errors, exit code ≠ 0**.
  - `DTZ007` × 2 em [app/aggregation/indicators.py:59](../../../app/aggregation/indicators.py#L59) e `:60` — `datetime.strptime(...)` sem timezone.
  - `DTZ011` × 1 em [scripts/generate_fixture.py:62](../../../scripts/generate_fixture.py#L62) — `date.today()` sem timezone.
- **Test count before feature**: 0 (repositório greenfield, commit `abac20f` = "Initial commit", sem código de app).
- **Test count after feature**: 45.
- **Delta**: +45 novos testes.
- **Skipped tests**: nenhum.
- **Failures**: nenhuma falha de teste; a falha é exclusivamente de lint (`ruff`), que é parte do comando de gate "Build" mandatório definido em tasks.md.

**Per o protocolo de validate.md ("Non-zero exit code = STOP"), o gate de Build FALHOU.** As demais seções (sensor, code quality) foram executadas de toda forma para produzir uma auditoria completa, mas o veredito final é FAIL até que os 3 erros de `ruff` sejam corrigidos.

---

## Fix Plans (Rodada 1 — todos os 3 gaps concretos resolvidos na Rodada 2; Fix 4 permanece em aberto como Minor, fora do escopo desta rodada)

### Fix 1: `ruff check .` falha o gate de Build (BLOQUEADOR) — ✅ Resolvido (commit `93303bc`)

- **Root cause**: `datetime.strptime` (sem `%z`) em `app/aggregation/indicators.py:59-60` e `date.today()` em `scripts/generate_fixture.py:62` disparam `DTZ007`/`DTZ011` — o projeto usa `datetime.now(UTC)` consistentemente em outros módulos (`raw_layer.py`, `version_manager.py`, `endpoint.py`, `treated_layer.py`, `indicators.py` no restante do arquivo), mas essas duas funções ficaram de fora do padrão.
- **Fix task**: em `_response_days`, trocar `datetime.strptime(data_abertura, "%Y-%m-%d")` por `date.fromisoformat(data_abertura)` (idem para `data_resposta`) — evita o aviso porque `date` não carrega noção de timezone. Em `generate_fixture.build_rows`, trocar `date.today()` por `datetime.now(UTC).date()`, consistente com o padrão já usado no resto do projeto.
- **Priority**: Blocker (gate mandatório de tasks.md).

### Fix 2 (Minor): cobertura de integração ausente para CSV corrompido no endpoint — ✅ Resolvido (commit `971ce32`)

- **Root cause**: `test_ingestion_endpoint.py` só exercita o caminho "vazio"; o caso "corrompido" só tem teste unitário em `schema_validator`.
- **Fix task**: adicionar um teste em `tests/integration/test_ingestion_endpoint.py` análogo a `test_post_ingest_with_empty_csv_distinguishes_from_invalid_schema`, mas com um CSV com aspas não fechadas (mesmo padrão de `test_validate_corrupted_file_is_distinct_from_invalid_schema`), confirmando `422` e mensagem distinguindo "corrompido" de "schema inválido" via HTTP.
- **Priority**: Minor.

### Fix 3 (Minor): ramo de `resultado` com 3º valor não testado no mês fechado — ✅ Resolvido (commit `d129366`)

- **Root cause**: o único registro do fixture com `resultado` fora de `{"Resolvido", "Nao Resolvido"}` ("Em Analise") está no mês aberto, nunca agregado — o ramo `not in (RESOLVIDO, NAO_RESOLVIDO)` de `_calculate_group` (indicators.py:68-70) nunca é exercitado por um teste no mês fechado.
- **Fix task**: adicionar uma linha ao fixture (ou um teste isolado com dados sintéticos inline) com `resultado="Em Analise"` dentro do mês fechado, e um teste que comprove numericamente que ela conta como resolvida no índice oficial e como não resolvida no estrito — provando que `oficial` e `estrito` de fato podem divergir (hoje eles sempre coincidem no golden data).
- **Priority**: Minor (spec-precision gap já auto-documentado, mas sem teste que prove a lógica implementada).

### Fix 4 (Minor): teste de reingestão usa CSV idêntico, não "CSV diferente" (edge case literal do spec.md) — ⏳ Em aberto (fora do escopo dos 3 commits desta rodada de fix)

- **Root cause**: `test_store_raw_reingestion_of_same_period_creates_new_version_without_overwrite` reingere o mesmo arquivo.
- **Fix task**: adicionar variante que reingere um CSV com conteúdo diferente (ex.: uma linha a mais) para o mesmo período e confirma nova versão com `row_count` diferente, sem sobrescrever a versão anterior.
- **Priority**: Minor.

---

## Requirement Traceability Update (Rodada 2 — final)

| Requirement ID | Status Rodada 1 | Status Rodada 2 (final) |
| --------------- | ---------------- | ------------------------ |
| ING-01 | ✅ Verified | ✅ Verified |
| ING-02 | ⚠️ Verified com gap de cobertura (Fix 2) | ✅ Verified (Fix 2 confirmado) |
| ING-03 | ✅ Verified | ✅ Verified |
| ING-04 | ✅ Verified | ✅ Verified |
| ING-05 | ✅ Verified | ✅ Verified |
| ING-06 | ✅ Verified | ✅ Verified |
| ING-07 | ⚠️ Verified com ressalva arquitetural | ⚠️ Verified com ressalva arquitetural (limitação conhecida, aceita — não é gap de teste) |
| ING-08 | ⚠️ Verified com gap de cobertura (Fix 3) | ✅ Verified (Fix 3 confirmado) |
| ING-09 | ✅ Verified | ✅ Verified |
| ING-10 | ✅ Verified | ✅ Verified |
| ING-11 | ✅ Verified | ✅ Verified |
| ING-12 | ✅ Verified | ✅ Verified |

---

## Summary (Rodada 2 — veredito final)

**Overall**: ✅ Ready — feature pode ser marcada como Verified.

**Fixes confirmados**: 3/3 (ruff, CSV corrompido no endpoint, divergência oficial/estrito), todos com evidência de `file:line` + asserção real, não apenas a mensagem do commit.
**Gate**: 47 passed / 0 failed (pytest); `ruff check .` → 0 erros, exit 0. Build gate PASS.
**Sensor**: 2/2 mutações novas (focadas nos trechos corrigidos) mortas; +3/3 mutações da Rodada 1 permanecem válidas (não re-testadas, escopo inalterado).
**Scope**: os 3 commits de fix tocaram apenas os arquivos esperados — sem scope creep.

**What works**: pipeline ponta a ponta (ingestão → tratada → agregada → rollback) continua correto e reprodutível; os 3 gaps concretos da Rodada 1 foram corrigidos com testes que exercitam exatamente o comportamento antes não coberto (lint limpo, distinção HTTP de CSV corrompido vs. schema inválido, divergência numérica real entre índice oficial e estrito, comprovada por mutação morta).

**Issues found**: nenhum gap novo nesta rodada. Restam dois itens conhecidos, não bloqueadores e fora do escopo desta rodada de fix:
1. Fix 4 da Rodada 1 (teste de reingestão com CSV literalmente "diferente") — Minor, follow-up opcional.
2. Ressalva arquitetural de ING-07 (fila de revisão do fuzzy match em memória, não persistida) — limitação já auto-documentada como `SPEC_DEVIATION`, aceita como conhecida, não é gap de teste.

**Next steps**: nenhum obrigatório. A feature pode ser marcada como Verified. Fix 4 pode virar task de follow-up de baixa prioridade em uma iteração futura, se desejado.
