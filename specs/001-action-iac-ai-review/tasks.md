# Tasks: Action de revisão de IaC com IA

**Input**: [spec.md](spec.md), [plan.md](plan.md)

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

- [ ] T001 Criar o repositório público `jjasonhenrique1986/github-actions` no GitHub e publicar a `main`
  com o Spec Kit, a constituição e esta spec
- [ ] T002 [P] `README.md` na raiz: o que é o repositório, índice das actions, regra de versões

## Phase 2: Foundational (pré-requisitos externos)

- [ ] T003 iac-ai-reviewer: merge dos PRs #3 e #4 (usuário) e release `v1.0.0` (tag na `main`)
- [ ] T004 [P] IAM: role `gh-github-actions` em `aws-iam-baseline/github-oidc.tf` pelo módulo
  `github-oidc-role` (sub imutável do novo repositório, só `pull_request`, só `bedrock:InvokeModel`
  no gpt-oss); `plan` por mim, `apply` pelo usuário
- [ ] T005 Secret `AWS_ROLE_ARN` e variável `MODEL_ID=openai.gpt-oss-120b-1:0` no novo repositório
  (depende de T004)

## Phase 3: User Story 1 - Revisar PRs de outro repositório (P1) 🎯 MVP

- [ ] T006 [US1] `iac-ai-review/action.yml`: inputs, validações (evento, checkout raso), busca do
  revisor em `$RUNNER_TEMP`, setup-python, venv do revisor, checkov em venv próprio,
  configure-aws-credentials com `mask-aws-account-id`, `review.py`, comentário fixo, saída `review-file`
- [ ] T007 [P] [US1] `tests/fixtures/sg-ssh-aberto.tf` (Security Group com SSH aberto)
- [ ] T008 [US1] Job `com-aws` em `.github/workflows/test-iac-ai-review.yml`: commit local do fixture,
  `base-ref: HEAD~1`, confere que o `review-file` tem "Risco geral" e publica o comentário

## Phase 4: User Story 2 - Controlar a versão do revisor (P2)

- [ ] T009 [US2] Input `reviewer-version` (padrão `v1.0.0`), versão impressa no log e erro claro para
  versão inexistente
- [ ] T010 [US2] Job de teste que roda com uma versão inexistente e confere que o passo falha com a
  mensagem esperada (`continue-on-error` + checagem do resultado)

## Phase 5: User Story 3 - Não gastar com PRs sem infraestrutura (P3)

- [ ] T011 [US3] Passo de detecção de mudanças com saída `has-changes`; checkov e credenciais
  condicionados a ele
- [ ] T012 [US3] Job `sem-aws`: `base-ref: HEAD`, `comment: false`, role fictícia; confere que o
  `review-file` diz "Nenhuma mudança" e que nenhum passo de credencial rodou

## Phase 6: Polish

- [ ] T013 [P] Job `actionlint` no mesmo workflow (versão fixada)
- [ ] T014 [P] README da action: workflow mínimo, permissions, forks, role (link para o
  iac-ai-reviewer), tabela de inputs e saída
- [ ] T015 PR no novo repositório; conferir os 3 jobs; merge pelo usuário; tags `v1.0.0` e `v1`
- [ ] T016 Validar SC-002: comparar o comentário do job `com-aws` com o do iac-ai-reviewer para o
  mesmo fixture

## Dependencies & Execution Order

- T001 → todo o resto. T003 e T004 são externos e podem andar em paralelo com T006–T014.
- T008 depende de T005 e T006. T009–T012 dependem de T006. T015 depende de todos.
- O MVP (US1) já funciona apontando `reviewer-version` para um SHA, se a tag `v1.0.0` atrasar.

## Implementation Strategy

Fazer T001–T002, escrever a action e os testes sem AWS (T006, T009–T014) e abrir o PR. O job com AWS
passa a valer quando a role (T004/T005) e a tag do revisor (T003) existirem.
