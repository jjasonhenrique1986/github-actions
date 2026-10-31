# Tasks: Código do revisor junto da action

## Phase 1: Pré-requisitos

- [x] T001 Merge dos PRs #3 e #4 do iac-ai-reviewer (usuário), ou confirmação para importar a branch — usuário escolheu importar a `mais-exemplos`
  `mais-exemplos`

## Phase 2: User Story 1 - Uma versão só (P1)

- [x] T002 [US1] Importar o iac-ai-reviewer com histórico para `iac-ai-review/` (decisões 1 e 2)
- [x] T003 [US1] `action.yml`: remover o passo de download e o input `reviewer-version`; usar
  `github.action_path`
- [x] T004 [US1] Workflow de teste: remover `REVIEWER_VERSION` e o job `versao-inexistente`

## Phase 3: User Story 2 - Desenvolver aqui (P2)

- [x] T005 [US2] Job `pytest` (`working-directory: iac-ai-review`) no workflow de teste
- [x] T006 [US2] Conferir `git log --follow iac-ai-review/reviewer/review.py`

## Phase 4: User Story 3 - Lugar novo (P3)

- [x] T007 [P] [US3] README da action incorporando o README do iac-ai-reviewer; README da raiz
- [x] T008 [US3] iac-ai-reviewer: README de aviso, fechar #3 e #4 com comentário, arquivar
- [x] T009 [P] [US3] Posts do blog (PR #10): links para `github-actions/iac-ai-review` e uso pela action
  na parte 3

## Phase 5: Fechamento

- [x] T010 `apply` da role `gh-github-actions` (usuário), secret `AWS_ROLE_ARN` e variável `MODEL_ID`;
  rodar o CI completo
- [x] T011 Merge do PR (usuário); tags `v1.0.0` e `v1`
- [ ] T012 Remover a role `gh-iac-ai-reviewer` do `aws-iam-baseline` (`plan` por mim, `apply` pelo usuário)
