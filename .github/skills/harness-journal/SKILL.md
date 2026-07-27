---
name: harness-journal
description: Logs, in a chronological and didactic journal, how the harness (skills, instructions, subagents, modes) was used together with the AI throughout a project's implementation, and which decisions were made along the way — producing a shareable artifact meant to be read and reused in other projects. Use when a task/phase is completed, right after an architecture decision is made, after notable use of a skill/subagent/instruction, or when the user says "log this in the journal", "document this step", "registra isso no journal", "documenta esse passo". Do NOT use for the architecture decision itself (use create-adr), for feature specification/planning (use tlc-spec-driven), or for generic reference documentation like README or TDD.
license: CC-BY-4.0
metadata:
  author: Kaue
  version: '1.0.0'
---

# Harness Journal

Registra, de forma cronológica e didática, como o harness (skills, instructions, subagents, modos de execução) foi usado em conjunto com a IA ao longo da implementação de um projeto. O resultado é um artefato compartilhável: alguém lendo depois, de fora, deve entender não só o que foi feito, mas qual peça do harness foi usada, por que essa peça e não outra, e o que aprender para reaproveitar em outro projeto.

Esta skill é intencionalmente **genérica e reaproveitável entre projetos**. Nunca hardcode o nome de um projeto específico nas instruções abaixo — o arquivo de journal gerado é que é específico de cada repositório.

## Quando registrar (gatilho híbrido)

**Dispare automaticamente** (registre e apenas avise em 1 linha que o journal foi atualizado, sem pedir permissão a cada vez):

- Ao concluir uma tarefa ou fase considerada fechada.
- Logo após uma decisão relevante ser tomada (formalizada em ADR ou não).
- Após o uso notável de uma peça do harness que moldou o resultado (uma skill foi invocada, um subagent foi lançado, uma troca de modo foi necessária, uma instruction mudou o comportamento padrão).

**Dispare sob comando explícito** do usuário: "registra isso", "documenta esse passo", "anota no journal", "coloca isso no harness journal".

**NÃO dispare para:**

- Cada mensagem ou tool call individual — isso é ruído, não sinal, e queima tokens à toa.
- Leituras/buscas triviais sem valor de decisão ou ensino.
- Conteúdo que duplica um ADR já escrito — nesse caso, referencie o ADR em vez de repetir o conteúdo.

Se estiver em dúvida se um passo é marco suficiente, prefira registrar de forma resumida a deixar de registrar — mas nunca registre no meio de uma tarefa ainda em andamento.

## Passo 1: Localizar ou criar o arquivo do journal

Caminho padrão: `docs/harness-journal.md`, na raiz de documentação do projeto atual (mesma convenção de `docs/adr/`, se existir). Se o arquivo não existir, crie-o com este cabeçalho:

```markdown
# Harness Journal

Registro cronológico de como o harness (skills, instructions, subagents, modos) foi usado
neste projeto, e das decisões tomadas ao longo do caminho. Pensado para ser lido por quem
quiser reaproveitar este harness em outro projeto.

---
```

## Passo 2: Sempre acrescentar, nunca reescrever

Para manter o custo de contexto baixo, **não releia o arquivo inteiro** antes de escrever — leia apenas a última entrada (final do arquivo) para manter numeração/formatação consistentes, e acrescente a nova entrada ao final. Nunca reordene ou edite entradas passadas, exceto para corrigir um link quebrado.

## Passo 3: Formato de cada entrada

```markdown
## [YYYY-MM-DD] {Título curto da entrada}

**Tarefa**: {o que foi feito, em 1-2 frases}

**Harness usado**: {skill / instruction / subagent / modo usado} — {por que essa peça em vez de outra, ou por que nenhuma peça formal foi necessária}

**Decisão** (se houver): {decisão tomada, em 1 frase} → {link para o ADR, se foi formalizada em um}

**Resultado**: {o que funcionou, o que não funcionou, ajustes feitos}

**Lição para reaproveitar**: {o que alguém replicando esse harness em outro projeto deveria saber}
```

Omita campos que genuinamente não se aplicam (ex.: nem toda entrada tem uma "Decisão"), mas nunca omita "Lição para reaproveitar" — é o motivo da skill existir.

## Passo 4: Idioma

Escreva a entrada no mesmo idioma da conversa com o usuário. Não traduza automaticamente entradas já escritas.

## Exemplo (example)

Usuário diz: "registra isso no journal — acabamos de decidir usar SQLite em vez de Postgres".

Ação: ler a última entrada de `docs/harness-journal.md` (ou criar o arquivo se for a primeira), acrescentar:

```markdown
## [2026-07-26] Escolha de armazenamento local

**Tarefa**: Decidir a stack de processamento/armazenamento de dados para rodar 100% local.

**Harness usado**: skill `create-adr` — formalizar a decisão como ADR em vez de só descrever em texto solto, já que impacta arquitetura e precisa ser rastreável depois.

**Decisão**: Python + SQLite como armazenamento único, em vez de Postgres em container → [ADR-002](adr/002-stack-processamento-dados-local.md).

**Resultado**: decisão registrada e referenciada no TDD.

**Lição para reaproveitar**: quando uma decisão de arquitetura é tomada em conversa, formalize com `create-adr` antes de registrar no journal — o journal referencia o ADR, não repete o raciocínio completo.
```

## Tratamento de erros (error handling)

- **`docs/adr/` ou `docs/` não existem ainda**: crie `docs/harness-journal.md` mesmo assim; não é obrigatório que outras pastas de documentação já existam.
- **Arquivo do journal muito grande para localizar a última entrada rapidamente**: procure pelo último cabeçalho `## [` a partir do fim do arquivo em vez de ler o arquivo inteiro do início.
- **Não está claro se o passo atual é marco suficiente**: prefira uma entrada curta a não registrar nada — nunca pare a tarefa em andamento só para decidir isso.
- **Decisão mencionada não tem ADR formal**: registre mesmo assim, deixando o campo de link vazio ou observando "não formalizado em ADR"; não bloqueie o registro esperando a formalização.

## Anti-padrões a evitar

- ❌ Registrar toda chamada de ferramenta ou busca — vira barulho, não narrativa didática.
- ❌ Duplicar o conteúdo inteiro de um ADR na entrada — linkar é suficiente.
- ❌ Parágrafos longos — cada entrada deve ser lida em poucos segundos.
- ❌ Reescrever ou reordenar entradas antigas.
- ❌ Assumir que é a única skill carregada — quando uma decisão já foi (ou deveria ser) formalizada via `create-adr`, `create-rfc` ou `tlc-spec-driven`, referencie o artefato gerado por elas em vez de duplicar.
