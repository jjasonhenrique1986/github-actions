# Implementation Plan: Action de revisão de IaC com IA

**Branch**: `001-action-iac-ai-review` | **Date**: 2026-10-31 | **Spec**: [spec.md](spec.md)

## Summary

Action composite `iac-ai-review` no repositório público `jjasonhenrique1986/github-actions`. Ela busca
o iac-ai-reviewer numa versão fixa, roda o checkov e o `reviewer/review.py` contra o diff do PR do
repositório que a usa e publica o comentário fixo. Sem mudanças de infraestrutura, não assume a role
nem chama o modelo.

## Technical Context

**Language/Version**: YAML de action composite + Bash; o revisor é Python 3.12 (iac-ai-reviewer)
**Primary Dependencies**: `actions/setup-python@v7`, `aws-actions/configure-aws-credentials@v6`,
`marocchino/sticky-pull-request-comment@v3.0.5` (as mesmas versões do workflow do iac-ai-reviewer), checkov
**Storage**: N/A
**Testing**: workflow de teste no próprio repositório + `actionlint`
**Target Platform**: GitHub Actions, `ubuntu-latest`
**Project Type**: action reutilizável
**Performance Goals**: PR sem infraestrutura em menos de 3 minutos (SC-003)
**Constraints**: sem access key; código do revisor fora do workspace do usuário
**Scale/Scope**: uma action, um workflow de teste, um README

## Constitution Check

| Princípio | Como o plano atende |
|---|---|
| I. Action fina | A action só busca o iac-ai-reviewer e chama `reviewer/review.py`; nenhum prompt ou validação copiado. |
| II. Versões fixadas | Input `reviewer-version` com padrão `v1.0.0`; actions de terceiros por tag; release `v1.0.0` + `v1`. |
| III. Sem credenciais fixas | Só `role-to-assume` (OIDC) com `mask-aws-account-id: true`; token do GitHub = `github.token`. |
| IV. Permissões mínimas | README lista `id-token: write`, `contents: read`, `pull-requests: write`; role própria `gh-github-actions` para o teste. |
| V. Testada | Job sem AWS em todo PR; job com AWS só em PR do próprio repositório; `actionlint`. |
| VI. Português | README, descrições dos inputs, mensagens e commits em português; exemplos com valores fictícios. |

Sem violações.

## Decisões

1. **Onde fica o código do revisor**: `git fetch --depth 1 origin <versão>` num diretório em
   `$RUNNER_TEMP`, não com `actions/checkout`, que só aceita caminhos dentro do workspace. Assim o
   código não entra no diff nem no checkov do usuário (edge case "código do revisor no workspace"), e
   o `fetch` aceita tag ou SHA (US2).
2. **Detectar mudanças antes da AWS**: um passo roda `git diff --name-only <base>...HEAD` com os mesmos
   padrões do revisor (`*.tf`, `*.tfvars`, `*.yaml`, `*.yml`) e expõe `has-changes`. Os passos de
   checkov e de credenciais têm `if: has-changes == 'true'`. O `review.py` roda sempre: com diff vazio
   ele já escreve "Nenhuma mudança em Terraform ou YAML" sem chamar a AWS (US3).
3. **Dois venvs**: um para o revisor (`reviewer/requirements.txt`) e outro para o checkov. Instalados
   juntos, o checkov rebaixou o `boto3` e quebrou o `--list-models` num teste local.
4. **Validações no início**: evento diferente de `pull_request`/`pull_request_target` → erro;
   `git rev-parse --is-shallow-repository` = `true` → erro pedindo `fetch-depth: 0`; versão do revisor
   não encontrada → erro com o nome da versão.
5. **Comentário**: mesmo header (`ai-iac-review`) do iac-ai-reviewer; input `comment: false` desliga a
   publicação (usado no teste sem AWS). Saída `review-file` com o caminho do Markdown (FR-009).
6. **Teste com AWS determinístico**: o job cria um commit local com um arquivo de `tests/fixtures/`
   e usa `base-ref: HEAD~1`, então o diff revisado é sempre o fixture, não importa o que o PR altera.
7. **Role do teste**: `gh-github-actions` no `aws-iam-baseline`, pelo módulo `github-oidc-role`, com
   `sub` imutável do novo repositório, `subjects = ["pull_request"]` e só `bedrock:InvokeModel` no
   gpt-oss. O `apply` é do usuário.

## Project Structure

### Documentation (this feature)

```text
specs/001-action-iac-ai-review/
├── spec.md
├── plan.md
├── tasks.md
└── checklists/requirements.md
```

### Source Code (repository root)

```text
iac-ai-review/
└── action.yml                      # a action composite
tests/fixtures/
└── sg-ssh-aberto.tf                # fixture inseguro para o teste com AWS
.github/workflows/
└── test-iac-ai-review.yml          # actionlint + teste sem AWS + teste com AWS
README.md                           # índice das actions + uso da iac-ai-review
```

### Inputs e saída

| Input | Obrigatório | Padrão | Descrição |
|---|---|---|---|
| `role-to-assume` | sim | — | ARN da role IAM do repositório (use um secret) |
| `aws-region` | não | `us-east-1` | região do Bedrock |
| `model-id` | não | padrão do revisor | `MODEL_ID` do iac-ai-reviewer |
| `reviewer-version` | não | `v1.0.0` | tag ou SHA do iac-ai-reviewer |
| `base-ref` | não | `origin/<base do PR>` | ref base do diff |
| `checkov` | não | `true` | roda o checkov e envia o resultado |
| `comment` | não | `true` | publica o comentário no PR |

| Saída | Descrição |
|---|---|
| `review-file` | caminho do Markdown com a revisão |

### Uso esperado (SC-001)

```yaml
name: Revisão de IaC com IA
on:
  pull_request:
    paths: ["**.tf", "**.tfvars", "**.yaml", "**.yml"]
permissions:
  id-token: write
  contents: read
  pull-requests: write
jobs:
  review:
    if: github.event.pull_request.head.repo.full_name == github.repository
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
        with:
          fetch-depth: 0
      - uses: jjasonhenrique1986/github-actions/iac-ai-review@v1
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          model-id: ${{ vars.MODEL_ID }}
```

## Complexity Tracking

Nenhuma violação a justificar.
