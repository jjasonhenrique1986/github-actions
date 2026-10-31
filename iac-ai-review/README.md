# iac-ai-review

Revisa as mudanças de Terraform e Kubernetes de um Pull Request com IA no **Amazon Bedrock** e publica
a revisão como comentário no PR. A action roda o
[iac-ai-reviewer](https://github.com/jjasonhenrique1986/iac-ai-reviewer) numa versão fixa:

1. Confere que o evento é `pull_request` e que o checkout tem o histórico completo.
2. Procura mudanças em `.tf`, `.tfvars`, `.yaml` e `.yml`. **Sem mudanças, não assume a role nem
   chama o modelo**: o comentário só avisa que não há nada para revisar.
3. Busca o iac-ai-reviewer fora do workspace, então o código dele não entra no diff nem no checkov.
4. Roda o checkov, assume a role por OIDC e chama o modelo.
5. Publica a revisão num comentário fixo, atualizado a cada push.

A IA explica os riscos. Ela **não aprova nem bloqueia** o PR.

## Uso

`.github/workflows/ai-review.yml`:

```yaml
name: Revisão de IaC com IA

on:
  pull_request:
    paths: ["**.tf", "**.tfvars", "**.yaml", "**.yml"]

permissions:
  id-token: write       # token OIDC para assumir a role na AWS
  contents: read
  pull-requests: write  # comentar no PR

jobs:
  review:
    # PRs de forks não recebem o token OIDC
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

## Pré-requisitos

- **Uma role IAM só para o repositório**, com trust policy OIDC presa ao `sub` do repositório e
  ao evento `pull_request`, e permissão só para os modelos que você vai usar. O passo a passo e as
  políticas estão no [README do iac-ai-reviewer](https://github.com/jjasonhenrique1986/iac-ai-reviewer#configuração).
- **Secret** `AWS_ROLE_ARN` com o ARN da role, por exemplo
  `arn:aws:iam::111122223333:role/github-meu-repo`.
- **Acesso ao modelo** no Bedrock: acordo aceito e cota maior que zero. O
  `python reviewer/review.py --list-models --test` do iac-ai-reviewer mostra o que está liberado.

## Inputs

| Input | Obrigatório | Padrão | Descrição |
|---|---|---|---|
| `role-to-assume` | sim | — | ARN da role IAM do repositório (use um secret) |
| `aws-region` | não | `us-east-1` | região do Bedrock |
| `model-id` | não | padrão do revisor | modelo da revisão; a lista aceita está no iac-ai-reviewer |
| `reviewer-version` | não | `v1.0.0` | tag ou SHA do iac-ai-reviewer |
| `base-ref` | não | `origin/<base do PR>` | ref base do diff |
| `checkov` | não | `true` | roda o checkov e envia o resultado ao modelo |
| `checkov-version` | não | `3.3.29` | versão do checkov |
| `comment` | não | `true` | publica o comentário no PR |

## Saída

| Saída | Descrição |
|---|---|
| `review-file` | caminho do Markdown com a revisão, para usar em outro passo |

## Segurança

- Use `pull_request`, **nunca** `pull_request_target`: a action recusa outros eventos.
- O ID da conta AWS é mascarado nos logs, e nenhuma access key é usada.
- O diff e a saída do checkov vão para o Bedrock da sua conta. Confira a política da sua empresa
  antes de usar em repositórios com dados sensíveis.
- A action usa o `actions/setup-python` com Python 3.12, o que muda o `python` dos passos seguintes
  do job.
