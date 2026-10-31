# Feature Specification: Código do revisor junto da action

**Feature Branch**: `001-action-iac-ai-review` (mesmo PR da implementação da 001, ainda não mesclado)

**Created**: 2026-10-31

**Status**: Draft

**Input**: Decisão do usuário: "o código do iac-ai-reviewer [pode] estar junto da action e nos meus
outros repos eu apenas crio um workflow com a action", escolhendo mover o código para este repositório
(`github-actions/iac-ai-review/`) em vez de pôr a action no iac-ai-reviewer.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Uma versão só (Priority: P1)

Quem usa a action informa só a versão da action (`@v1`). O código do revisor que roda é o da mesma
versão, sem um segundo input de versão e sem baixar outro repositório.

**Why this priority**: é o pedido. Elimina a dupla de versões e o download em tempo de execução.

**Independent Test**: rodar o workflow de teste e conferir no log que nenhum repositório externo é
baixado e que a revisão sai igual à da 001.

**Acceptance Scenarios**:

1. **Given** um repositório com o workflow mínimo, **When** um PR altera Terraform, **Then** o
   comentário é publicado usando o código de `iac-ai-review/` da versão da action.
2. **Given** a action, **When** se procura um input de versão do revisor, **Then** ele não existe.

---

### User Story 2 - Desenvolver o revisor neste repositório (Priority: P2)

Quem mantém o revisor muda o prompt, os modelos ou os testes em `iac-ai-review/` e o CI deste
repositório roda o `pytest` e revisa os exemplos com a própria action.

**Why this priority**: o código só pode viver aqui se o desenvolvimento dele também viver aqui.

**Independent Test**: um PR que altera `iac-ai-review/reviewer/review.py` roda o `pytest` e o job
`com-aws` com o código alterado.

**Acceptance Scenarios**:

1. **Given** um PR que muda o revisor, **When** o CI roda, **Then** `pytest` e `com-aws` usam o código
   do PR.
2. **Given** o histórico do iac-ai-reviewer, **When** se roda `git log --follow` num arquivo movido,
   **Then** os commits antigos aparecem.

---

### User Story 3 - Leitores e usuários antigos chegam no lugar novo (Priority: P3)

Quem abre o repositório iac-ai-reviewer, por um link antigo ou pelos posts do blog, encontra um aviso
apontando para `github-actions/iac-ai-review`.

**Why this priority**: o repositório antigo é público e é citado nos posts que vão ao ar em 01/11.

**Independent Test**: abrir o README do iac-ai-reviewer e os posts e conferir os links.

**Acceptance Scenarios**:

1. **Given** o iac-ai-reviewer, **When** alguém abre o repositório, **Then** ele está arquivado
   (somente leitura) e o README aponta para o caminho novo.
2. **Given** os 3 posts da série, **When** publicados, **Then** os links de código apontam para
   `github-actions/iac-ai-review` e a parte 3 mostra o uso pela action.

---

### Edge Cases

- **PRs abertos no iac-ai-reviewer (#3 e #4)**: o conteúdo deles precisa estar na importação; depois
  eles são fechados com um comentário apontando para o repositório novo.
- **Arquivos `.tf`/`.yaml` dos exemplos dentro deste repositório**: o job `com-aws` continua revisando
  só o fixture (commit local com `base-ref: HEAD~1`); os exemplos não podem disparar revisões em todo
  PR deste repositório.
- **Checkov dos usuários**: o código da action fica em `github.action_path`, fora do workspace do
  usuário, então não entra no diff nem no checkov dele.
- **Role antiga** `gh-iac-ai-reviewer` e o secret do iac-ai-reviewer ficam sem uso.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `iac-ai-review/` MUST conter `action.yml`, `reviewer/` (código e `requirements.txt`),
  `tests/`, `examples/`, `requirements-dev.txt` e `README.md`.
- **FR-002**: A action MUST executar `reviewer/review.py` da própria pasta e MUST NOT baixar código de
  outro repositório.
- **FR-003**: O input `reviewer-version` MUST ser removido; os demais inputs e a saída `review-file` da
  001 permanecem.
- **FR-004**: O histórico de commits do iac-ai-reviewer MUST ser preservado na importação.
- **FR-005**: O CI MUST rodar `pytest` de `iac-ai-review/` em todo PR, além dos jobs da 001.
- **FR-006**: O README da action MUST trazer o conteúdo útil do README do iac-ai-reviewer (como
  funciona, configuração da role, modelos, exemplos, segurança), ajustado para o uso pela action.
- **FR-007**: O iac-ai-reviewer MUST receber um README de aviso e ser arquivado; os PRs abertos dele
  MUST ser fechados com comentário.
- **FR-008**: Os posts da série no blog MUST apontar para o caminho novo antes de serem publicados.
- **FR-009**: As specs do iac-ai-reviewer (`001-selecao-de-modelo`) MUST ser preservadas como histórico.

### Key Entities

- **Pasta da action** `iac-ai-review/`: unidade autocontida e versionada com o repositório.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Um repositório usa a revisão com um workflow de até 25 linhas e um único número de versão.
- **SC-002**: Os 26 testes do revisor passam no CI deste repositório.
- **SC-003**: Nenhuma execução da action baixa código de outro repositório (verificável no log).
- **SC-004**: Nenhum link dos 3 posts aponta para o iac-ai-reviewer como lugar do código.

## Assumptions

- O usuário faz o merge dos PRs #3 e #4 do iac-ai-reviewer antes da importação, para importar a `main`
  completa. Se preferir, a importação usa a branch `mais-exemplos`, que já contém os dois.
- Arquivar o iac-ai-reviewer é feito por mim depois da aprovação desta spec (é reversível no GitHub).
- A role `gh-iac-ai-reviewer` é removida do `aws-iam-baseline` numa mudança separada, com `apply` do
  usuário, depois que a action estiver funcionando.
- A role `gh-github-actions` (plano já pronto) continua só com o gpt-oss.
