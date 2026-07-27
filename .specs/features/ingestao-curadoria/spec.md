# Ingestão e Curadoria de Dados (Fase 1) Specification

## Problem Statement

O Consumidor.gov.br publica mensalmente um CSV de reclamações finalizadas, mas sem
tratamento ele é inutilizável para responder perguntas de qualidade de atendimento:
nomes de empresa não padronizados, encoding inconsistente e nenhuma metodologia
declarada de índice de solução. Sem uma camada de ingestão e curadoria confiável, todo o
resto do produto (camada de dados, agente conversacional, interface) não tem uma base
de dado em que se apoiar.

## Goals

- [ ] CSV oficial mensal ingerido sem alteração em uma camada bruta versionada, com
      validação de schema que falha de forma visível em caso de mudança.
- [ ] Dados normalizados (empresa via fuzzy match, datas, encoding) e deduplicados em
      uma camada tratada.
- [ ] Indicadores agregados (índice de solução oficial e estrita, tempo médio de
      resposta, nota média) calculados por empresa/segmento/mês, apenas para meses
      fechados.
- [ ] Cada execução gera uma versão nova da camada agregada, permitindo rollback.

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature                                              | Reason                                                         |
| ----------------------------------------------------- | ----------------------------------------------------------------- |
| Camada de acesso a dados (operações de consulta)       | Fase 2 do TDD — depende desta fase estar concluída                |
| Agente conversacional e regras de grounding            | Fase 3 do TDD                                                     |
| Interface/chat                                         | Fase 4 do TDD                                                     |
| Testes de regressão do agente e E2E                    | Fase 5/6 do TDD                                                   |
| Agendamento automático (cron) da ingestão              | Disparo é via endpoint manual, conforme decisão registrada abaixo |
| Cálculo de indicadores para o mês corrente (em aberto) | Regra de negócio é mês fechado (ver Assumptions)                  |

---

## Assumptions & Open Questions

Every ambiguity is resolved or recorded here — nothing is left silently unclear.

| Assumption / decision                                                                                   | Chosen default                                                                                     | Rationale                                                                                                     | Confirmed? |
| ---------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | ---------- |
| Fonte do CSV                                                                                             | [dados.mj.gov.br/dataset/reclamacoes-do-consumidor-gov-br](https://dados.mj.gov.br/dataset/reclamacoes-do-consumidor-gov-br) | Fonte oficial citada no TDD                                                                                          | y          |
| Layout exato de colunas do CSV                                                                           | Assumir os campos já citados no TDD (empresa, segmento, assunto, prazos, resultado do atendimento, UF, data) até confirmação | Site oficial está **fora do ar em 2026-07-26**, impossível inspecionar o CSV real agora; validação de schema (ING-02) deve ser ajustada assim que uma amostra real estiver disponível | n — revisar quando o site voltar |
| Forma de disparo da ingestão                                                                             | Endpoint HTTP, chamado manualmente (não agendado/cron)                                              | Alinhado com ADR-002 ("disparado manualmente por script/endpoint")                                                   | y          |
| Regra de período para cálculo de indicadores                                                             | Mês fechado — mês corrente em andamento nunca é agregado                                            | Resolve a ambiguidade de arredondamento de período já sinalizada como Questão em Aberto no TDD                       | y          |
| Algoritmo de normalização/dedupe de nome de empresa                                                       | Fuzzy match (correspondência aproximada de string), com revisão amostral                            | Decisão do usuário; parâmetros exatos (biblioteca, limiar de similaridade) ficam para a fase de Design              | y — detalhes técnicos pendentes de Design |
| Payload do endpoint de disparo (arquivo por upload vs. referência de mês a processar)                    | Fica em aberto para Design                                                                          | Não é uma decisão de escopo/requisito, é decisão de contrato técnico                                                 | n — tratar em Design |
| Dado de entrada enquanto a fonte oficial está fora do ar                                                  | Gerar um CSV sintético (fake) seguindo o layout assumido, com casos de borda representativos (ver ING-12) | Desbloqueia a implementação de ING-01 a ING-11 sem depender do site voltar; substituído/ajustado quando o layout real for confirmado | y — fixture provisório, revisar quando a fonte voltar |

**Open questions:** nenhuma bloqueante para a especificação — os dois itens não confirmados (layout exato do CSV e payload do endpoint) estão registrados acima com plano de resolução (revisão quando a fonte voltar / decisão em Design).

---

## User Stories

### P1: Ingestão bruta com validação de schema ⭐ MVP

**User Story**: Como operador do pipeline, quero ingerir o CSV oficial mensal em uma
camada bruta versionada e imutável, disparando o processo via endpoint, para que os
dados de origem fiquem rastreáveis e qualquer mudança de schema seja detectada antes de
corromper as camadas seguintes.

**Why P1**: Sem ingestão bruta confiável, nenhuma etapa seguinte (normalização,
indicadores) tem uma base válida.

**Acceptance Criteria**:

1. WHEN o endpoint de ingestão é chamado com um CSV válido THEN o sistema SHALL
   armazenar o conteúdo sem alteração em uma nova versão da camada bruta.
2. WHEN o CSV recebido não contém todas as colunas esperadas, ou contém colunas
   renomeadas/adicionais incompatíveis THEN o sistema SHALL rejeitar a execução com um
   erro explícito identificando a(s) coluna(s) divergente(s), sem gravar dado na camada
   bruta.
3. WHEN a ingestão é concluída com sucesso THEN o sistema SHALL registrar a versão da
   execução (timestamp, quantidade de linhas, hash/checksum do arquivo de origem).
4. WHEN o endpoint é chamado novamente para o mesmo período já ingerido THEN o sistema
   SHALL criar uma nova versão em vez de sobrescrever a anterior.

**Independent Test**: Chamar o endpoint com um CSV de amostra íntegro e confirmar que
uma nova versão aparece na camada bruta; chamar novamente com um CSV com uma coluna
removida e confirmar que a execução falha com erro explícito e nada é gravado.

---

### P1: Normalização e curadoria (camada tratada)

**User Story**: Como operador do pipeline, quero que os dados brutos sejam normalizados
(nome de empresa, datas, encoding) e deduplicados, para que os indicadores calculados
não fragmentem/fundam empresas incorretamente nem sejam distorcidos por inconsistência
de formato.

**Why P1**: Indicadores calculados sobre dado não normalizado (ex.: mesma empresa
contada como duas) invalidam o valor central do produto — comparação e evolução
confiáveis.

**Acceptance Criteria**:

1. WHEN um registro da camada bruta é processado THEN o sistema SHALL normalizar
   encoding e formato de data para um padrão único antes de gravar na camada tratada.
2. WHEN dois ou mais registros referenciam nomes de empresa distintos, mas
   suficientemente similares (fuzzy match acima do limiar definido em Design) THEN o
   sistema SHALL tratá-los como a mesma entidade empresa na camada tratada.
3. WHEN um registro é identificado como duplicata exata (mesma reclamação) THEN o
   sistema SHALL remover a duplicata, mantendo apenas uma ocorrência.
4. WHEN o processo de normalização é concluído THEN o sistema SHALL disponibilizar uma
   amostra dos agrupamentos de empresa resultantes do fuzzy match, para revisão amostral
   humana (conforme risco já mapeado no TDD).

**Independent Test**: Processar um lote sintético com nomes de empresa grafados de
formas diferentes (ex.: "Empresa X S.A.", "EMPRESA X SA") e confirmar que são agrupados
como uma única entidade na camada tratada, com a amostra de revisão disponível.

---

### P1: Cálculo de indicadores agregados (camada agregada)

**User Story**: Como operador do pipeline, quero calcular índice de solução (oficial e
estrita), tempo médio de resposta e nota média de satisfação por empresa/segmento/mês,
apenas para meses fechados, para que a Fase 2 (Camada de Acesso a Dados) tenha uma base
agregada confiável e auditável para consultar.

**Why P1**: É o entregável central da Fase 1 — sem indicadores agregados corretos, não
há produto.

**Acceptance Criteria**:

1. WHEN a camada tratada de um mês fechado está disponível THEN o sistema SHALL
   calcular índice de solução oficial, índice de solução estrito, tempo médio de
   resposta e nota média de satisfação, agrupados por empresa e por segmento.
2. WHEN o mês de referência ainda está em andamento (não fechado) THEN o sistema SHALL
   recusar o cálculo de indicadores para esse mês.
3. WHEN o cálculo de indicadores é concluído THEN o sistema SHALL gravar o resultado
   como uma nova versão da camada agregada, sem sobrescrever versões anteriores.
4. WHEN um indicador é consultado THEN o valor SHALL ser reproduzível — mesma entrada,
   mesma versão da camada tratada, mesmo resultado.

**Independent Test**: Rodar o cálculo sobre um mês fechado sintético com valores
conhecidos e confirmar que o índice de solução oficial, o índice de solução estrito, o
tempo médio de resposta e a nota média batem com o valor calculado manualmente para a
mesma amostra.

---

### P2: Versionamento e rollback da camada agregada

**User Story**: Como operador do pipeline, quero poder reverter a camada agregada para
uma versão anterior, para que um erro detectado após uma execução não fique exposto às
fases seguintes até ser corrigido.

**Why P2**: Importante para operação segura, mas o produto funciona com uma única
versão publicada enquanto o mecanismo de rollback não existe — não bloqueia o
MVP da Fase 1.

**Acceptance Criteria**:

1. WHEN existem duas ou mais versões da camada agregada THEN o sistema SHALL permitir
   apontar qual versão está "ativa" (a que seria consultada pela Fase 2).
2. WHEN um rollback é executado THEN o sistema SHALL manter a versão revertida
   disponível (não deletada), apenas marcada como inativa.

**Independent Test**: Gerar duas versões da camada agregada, reverter para a primeira e
confirmar que ela passa a ser a versão ativa, com a segunda ainda presente mas inativa.

---

### P1: Fixture CSV sintético para desenvolvimento ⭐ desbloqueia implementação

**User Story**: Como desenvolvedor do pipeline, quero um CSV sintético (fake) que segue
o layout de colunas assumido (empresa, segmento, assunto, UF, data de abertura, data de
resposta, resultado, nota de satisfação), com casos de borda representativos, para que a
implementação e os testes de ING-01 a ING-11 possam começar antes que a fonte oficial
(dados.mj.gov.br) volte ao ar.

**Why P1**: A fonte oficial está indisponível desde 2026-07-26 (ver Assumptions); sem um
fixture, nenhuma tarefa de ingestão, curadoria ou cálculo de indicadores pode ser
implementada ou testada de ponta a ponta.

**Acceptance Criteria**:

1. WHEN o fixture é gerado THEN o sistema SHALL produzir um CSV contendo o conjunto de
   colunas assumido em Assumptions (empresa, segmento, assunto, UF, data de abertura,
   data de resposta, resultado do atendimento, nota de satisfação).
2. WHEN o fixture é gerado THEN o conjunto de dados SHALL incluir, no mínimo: duas ou
   mais variantes de grafia do nome da mesma empresa (para exercitar o fuzzy match),
   uma duplicata exata de reclamação, registros pertencentes a um mês fechado e a um
   mês em andamento (mês corrente), e ao menos um registro sem nota de satisfação
   preenchida.
3. WHEN a fonte oficial voltar ao ar e o layout real de colunas for confirmado THEN o
   fixture SHALL ser revisado e ajustado para refletir o schema real, sem que isso
   invalide o trabalho de implementação já feito sobre o fixture provisório.
4. WHEN o fixture é usado para validar as histórias ING-01 a ING-10 THEN os resultados
   esperados de cada Independent Test SHALL ser calculáveis manualmente a partir do
   fixture, servindo como dado de referência ("golden") para os testes.

**Independent Test**: Gerar o fixture e confirmar que contém as colunas esperadas e os
casos de borda listados (variantes de empresa, duplicata exata, mês aberto/fechado, nota
ausente); confirmar que o índice de solução calculado manualmente a partir do fixture
bate com o valor que os testes de ING-08 esperam.

---

## Edge Cases

- WHEN o CSV de origem está vazio ou corrompido (não parseável) THEN o sistema SHALL
  rejeitar a execução com erro explícito, sem gravar nenhuma camada.
- WHEN a fonte oficial (dados.mj.gov.br) está indisponível no momento da chamada ao
  endpoint (cenário observado em 2026-07-26) THEN o sistema SHALL retornar um erro
  claro distinguindo "fonte indisponível" de "schema inválido".
  > Nota de escopo: se o endpoint apenas recebe o CSV (não busca a fonte diretamente),
  > este caso se aplica ao processo/operador que baixa o arquivo antes de chamá-lo — a
  > decisão exata do contrato do endpoint fica para Design (ver Assumptions).
- WHEN o fuzzy match de empresa tem confiança baixa/ambígua para um par de nomes THEN o
  sistema SHALL manter os registros como entidades separadas (evitar fusão incorreta) e
  sinalizar o par na amostra de revisão, em vez de decidir silenciosamente.
- WHEN um mesmo período é reingerido com um CSV diferente do anterior (ex.: correção da
  Senacon) THEN o sistema SHALL tratar como nova versão da camada bruta, sem descartar a
  versão anterior.

---

## Requirement Traceability

Each requirement gets a unique ID for tracking across design, tasks, and validation.

| Requirement ID | Story                                          | Phase  | Status    |
| -------------- | ----------------------------------------------- | ------ | --------- |
| ING-01         | P1: Ingestão bruta — armazenar sem alteração     | Tasks  | ✅ Verified |
| ING-02         | P1: Ingestão bruta — validação de schema         | Tasks  | ✅ Verified |
| ING-03         | P1: Ingestão bruta — versionamento da execução   | Tasks  | ✅ Verified |
| ING-04         | P1: Normalização — encoding e datas              | Tasks  | ✅ Verified |
| ING-05         | P1: Normalização — fuzzy match de empresa        | Tasks  | ✅ Verified |
| ING-06         | P1: Normalização — dedupe de reclamação exata    | Tasks  | ✅ Verified |
| ING-07         | P1: Normalização — amostra de revisão            | Tasks  | ⚠️ Verified (ressalva arquitetural: fila em memória) |
| ING-08         | P1: Indicadores — cálculo por empresa/segmento   | Tasks  | ✅ Verified |
| ING-09         | P1: Indicadores — regra de mês fechado           | Tasks  | ✅ Verified |
| ING-10         | P1: Indicadores — versionamento e reprodutibilidade | Tasks | ✅ Verified |
| ING-11         | P2: Rollback — versão ativa/inativa              | Tasks  | ✅ Verified |
| ING-12         | P1: Fixture CSV sintético para desenvolvimento   | Tasks  | ✅ Verified |

**ID format:** `ING-[NUMBER]`

**Status values:** Pending → In Design → In Tasks → Implementing → Verified

**Coverage:** 12 total, 12 mapped a componentes/data models em `design.md`, 12 mapeados a tarefas em `tasks.md` (T1-T14)

---

## Success Criteria

How we know the feature is successful:

- [ ] Uma execução completa (endpoint → bruto → tratado → agregado) roda de ponta a
      ponta sobre um CSV de amostra sem intervenção manual.
- [ ] Mudança de schema simulada é rejeitada com erro visível, sem gravar dado
      incorreto em nenhuma camada.
- [ ] Indicador calculado bate com valor de referência calculado manualmente para uma
      amostra conhecida (ver Estratégia de Testes do TDD).
- [ ] Mesma entrada, mesma versão da camada tratada → mesmo resultado agregado
      (reprodutibilidade).
- [ ] Fixture CSV sintético cobre os casos de borda necessários (variantes de empresa,
      duplicata exata, mês aberto/fechado, nota ausente) para validar ING-01 a ING-11
      sem depender da fonte oficial estar no ar.
