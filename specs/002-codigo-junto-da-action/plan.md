# Implementation Plan: Código do revisor junto da action

**Date**: 2026-10-31 | **Spec**: [spec.md](spec.md)

## Summary

Importar o iac-ai-reviewer com histórico para `iac-ai-review/`, trocar o download do revisor por
`github.action_path`, adicionar `pytest` ao CI, arquivar o repositório antigo e atualizar os posts.

## Constitution Check (2.0.0)

| Princípio | Como o plano atende |
|---|---|
| I. Action autocontida | Código, testes e exemplos em `iac-ai-review/`; sem download em execução. |
| II. Versões fixadas | `requirements.txt` já fixa versões; actions de terceiros por tag; release `v1.0.0`/`v1`. |
| III. Sem credenciais fixas | Inalterado (OIDC, conta mascarada). |
| IV. Permissões mínimas | Inalterado; role do teste só com gpt-oss. |
| V. Testada | `pytest` + `actionlint` + `sem-aws` + `com-aws`. |
| VI. Português | Inalterado. |
| Regras da iac-ai-review | O código do revisor é movido sem mudança de comportamento. |

## Decisões

1. **Importação com histórico**: num clone temporário do iac-ai-reviewer, um commit move tudo para
   `iac-ai-review/` (`git mv`); depois `git merge --allow-unrelated-histories` nesta branch. O
   `git log --follow` encontra os commits antigos.
2. **O que vai e o que não vai**:
   - Vão para `iac-ai-review/`: `reviewer/`, `tests/`, `examples/`, `iam/`, `requirements-dev.txt`,
     README (reescrito como README da action).
   - Specs antigas: `specs/001-selecao-de-modelo` → `iac-ai-review/docs/specs/001-selecao-de-modelo`
     (histórico; as specs novas continuam em `specs/` na raiz).
   - Não vão: `.github/workflows/ai-review.yml` (substituído pelos jobs deste repositório), `.specify/`
     e `.claude/` do repositório antigo (este já tem os seus), constituição antiga (incorporada).
3. **Testes**: o `conftest`/imports dos testes usam caminhos relativos ao arquivo; o job `pytest` roda
   com `working-directory: iac-ai-review`.
4. **Exemplos sem gatilho**: este repositório não tem workflow de revisão em `pull_request` com filtro
   de `paths`, então os exemplos não disparam nada sozinhos.
5. **Arquivamento**: commit no iac-ai-reviewer com README de aviso, fechar #3 e #4 com comentário,
   `gh repo archive`. O secret e a variável dele ficam (repositório arquivado não roda workflows).

## Project Structure

```text
iac-ai-review/
├── action.yml
├── README.md
├── requirements-dev.txt
├── reviewer/            # review.py, requirements.txt
├── tests/               # pytest (sem AWS)
├── examples/            # Terraform e K8s inseguros
├── iam/                 # políticas de exemplo
└── docs/specs/001-selecao-de-modelo/
tests/fixtures/          # fixture do job com-aws (inalterado)
.github/workflows/test-iac-ai-review.yml   # + job pytest
```
