# ADR-001: Execução local com Docker Compose (sem provisionamento de cloud)

- **Data**: 2026-07-26
- **Status**: Accepted
- **Decisores**: @Kaue
- **Tags**: architecture, infrastructure, cost

## Contexto e Definição do Problema

O Radar Consumidor é um produto greenfield ([TDD](../tdd-radar-consumidor.md)) que deixou
em aberto a escolha de cloud provider. A equipe é de uma pessoa, o produto ainda está em
fase de validação de valor, e os dados de entrada (reclamações do Consumidor.gov.br) são
públicos, atualizados em batch mensal, sem exigência de alta disponibilidade nesta fase.
Era preciso decidir onde e como o produto roda antes de destravar a escolha da stack de
processamento de dados.

## Decision Drivers

- Custo de infraestrutura deve ser zero durante a fase de validação.
- Equipe pequena (1 pessoa) sem capacidade de operar infraestrutura cloud.
- Necessidade de iterar rápido e rodar o produto em qualquer máquina de desenvolvimento.
- Dados de entrada não têm requisito de tempo real nem de alta disponibilidade.
- A arquitetura lógica (camadas bruto/tratado/agregado, camada de acesso a dados, agente,
  banco de aplicação) deve continuar válida se o produto migrar para cloud no futuro.

## Considered Options

- Cloud gerenciada (AWS/GCP/Azure) desde o início.
- Execução local com Docker Compose.
- Híbrido (parte local, parte cloud).

## Decision Outcome

Opção escolhida: **Execução local com Docker Compose**, porque elimina custo de
infraestrutura e complexidade operacional na fase atual, mantendo a arquitetura em
camadas do TDD intacta para uma migração futura, se necessária.

### Positive Consequences

- Custo de infraestrutura zero na fase de validação.
- Setup reproduzível em qualquer máquina com Docker (`docker compose up`).
- Ciclo de iteração rápido, sem depender de provisionamento de nuvem.
- Fácil de demonstrar o produto localmente para stakeholders.

### Negative Consequences

- Sem alta disponibilidade nem escalabilidade horizontal.
- Agendamento de ingestão e operação em geral dependem de execução manual (ver
  [ADR-002](002-stack-processamento-dados-local.md) e Plano de Implementação do TDD).
- Será necessário um plano de migração para cloud caso o produto cresça além da
  capacidade de uma máquina local (volume de dado, usuários concorrentes, disponibilidade).

## Pros and Cons of the Options

### Execução local com Docker Compose ✅ Escolhido

- ✅ Custo zero de infraestrutura
- ✅ Portável — roda em qualquer máquina com Docker
- ✅ Sem operação de infraestrutura cloud a manter
- ❌ Sem alta disponibilidade
- ❌ Escalabilidade limitada à máquina local

### Cloud gerenciada desde o início

- ✅ Alta disponibilidade e escalabilidade nativas
- ❌ Custo de infraestrutura antes de validar o produto
- ❌ Complexidade operacional incompatível com equipe de 1 pessoa

### Híbrido

- ✅ Flexibilidade de mover partes específicas para cloud
- ❌ Complexidade de manter dois ambientes sem ganho claro nesta fase

## Links

- [TDD - Radar Consumidor](../tdd-radar-consumidor.md)
- Relacionado: [ADR-002: Stack de processamento e armazenamento de dados local](002-stack-processamento-dados-local.md)
