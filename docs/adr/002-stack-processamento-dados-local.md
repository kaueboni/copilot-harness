# ADR-002: Stack de processamento e armazenamento de dados local (Python + SQLite)

- **Data**: 2026-07-26
- **Status**: Accepted
- **Decisores**: @Kaue
- **Tags**: architecture, data, database

## Contexto e Definição do Problema

Com a decisão de rodar 100% localmente via Docker Compose
([ADR-001](001-execucao-local-com-docker-compose.md)), plataformas de dados gerenciadas
como Databricks deixam de fazer sentido — elas pressupõem infraestrutura cloud. Era
preciso escolher uma stack de processamento e armazenamento que rode inteiramente em
containers locais, suporte as camadas bruto/tratado/agregado definidas no
[TDD](../tdd-radar-consumidor.md) e sirva também como banco de aplicação (conversas e
feedback do agente conversacional).

## Decision Drivers

- Deve rodar inteiramente dentro de containers Docker locais, sem serviço gerenciado.
- Volume de dado (reclamações mensais da Senacon) cabe em processamento single-node.
- Simplicidade operacional — sem servidor de banco de dados adicional para manter.
- Equipe já tem familiaridade com Python para manipulação de dados.
- Facilidade de inspecionar/versionar os dados localmente durante o desenvolvimento.

## Considered Options

- Databricks/Spark.
- Python (pandas/polars) + Postgres em container.
- Python (pandas/polars) + DuckDB/Parquet em arquivo.
- Python (pandas/polars) + SQLite em arquivo.

## Decision Outcome

Opção escolhida: **Python (pandas/polars) para o pipeline de ingestão/curadoria, com
SQLite como armazenamento único**, porque é a opção mais simples de operar localmente,
sem exigir um servidor de banco adicional, mantendo os arquivos de dado fáceis de
inspecionar e versionar durante o desenvolvimento.

**Organização física dos dados**:

- `analytics.db` (SQLite): tabelas das camadas bruta, tratada e agregada. Único writer:
  o processo de ingestão (disparado manualmente por script/endpoint, conforme Plano de
  Implementação do TDD).
- `app.db` (SQLite, arquivo separado): conversas, histórico e feedback do agente
  conversacional. Único writer: o serviço do agente.
- Separar os dois arquivos evita concorrência de escrita entre ingestão e agente, que é
  a principal limitação do SQLite.

### Positive Consequences

- Um único motor de banco de dados para todo o produto, sem servidor a manter.
- Arquivos fáceis de inspecionar, copiar e versionar durante o desenvolvimento.
- Zero configuração adicional no Docker Compose (sem container de banco de dados).
- Pipeline em Python reaproveita bibliotecas maduras (pandas/polars) para normalização e
  cálculo dos indicadores.

### Negative Consequences

- SQLite tem suporte limitado a escrita concorrente — mitigado ao restringir cada
  arquivo a um único processo escritor (ingestão vs. agente).
- Sem os tipos analíticos e otimizações de leitura colunar que o DuckDB ofereceria para
  consultas agregadas maiores.
- Se o volume de dado ou a concorrência de acesso crescer, será necessária uma migração
  para Postgres ou DuckDB (a arquitetura em camadas do TDD permanece válida nessa
  migração).

## Pros and Cons of the Options

### Python + SQLite ✅ Escolhido

- ✅ Sem servidor de banco adicional no Docker Compose
- ✅ Arquivo único, fácil de inspecionar/versionar
- ✅ Suficiente para o volume de dado da fase atual
- ❌ Escrita concorrente limitada (mitigado por separação de arquivos por escritor)
- ❌ Sem otimizações analíticas colunares

### Python + DuckDB/Parquet

- ✅ Melhor performance para consultas agregadas colunares
- ✅ Ainda em arquivo, sem servidor adicional
- ❌ Ecossistema e tooling menos maduro que SQLite para o caso de uso atual
- ❌ Complexidade adicional não justificada pelo volume de dado atual

### Python + Postgres em container

- ✅ Suporta melhor concorrência de escrita/leitura
- ✅ Caminho de migração natural se o produto crescer
- ❌ Exige container e configuração adicional no Docker Compose
- ❌ Overhead operacional não justificado na fase atual

### Databricks/Spark

- ✅ Escalabilidade e recursos analíticos avançados
- ❌ Pressupõe infraestrutura cloud gerenciada — incompatível com
  [ADR-001](001-execucao-local-com-docker-compose.md)
- ❌ Custo e complexidade incompatíveis com a fase atual do produto

## Links

- [TDD - Radar Consumidor](../tdd-radar-consumidor.md)
- Depende de: [ADR-001: Execução local com Docker Compose](001-execucao-local-com-docker-compose.md)
