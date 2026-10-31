# iac-ai-review

Revisa as mudanças de Terraform e Kubernetes de um Pull Request com **IA no Amazon Bedrock** (Claude
ou OpenAI gpt-oss) e publica a revisão como comentário no PR, sem access keys.

A cada execução, a action:

1. Confere que o evento é `pull_request` e que o checkout tem o histórico completo.
2. Procura mudanças em `.tf`, `.tfvars`, `.yaml` e `.yml`. **Sem mudanças, não assume a role nem
   chama o modelo**: o comentário só avisa que não há nada para revisar.
3. Roda os **scanners** (checkov, Trivy, kube-linter e kubeconform) no repositório, para ter
   achados determinísticos.
4. Assume uma role IAM via **OIDC** (credenciais temporárias).
5. Envia o diff e um resumo de cada scanner para o modelo, que devolve uma revisão em **JSON validado**
   (Pydantic).
6. Publica a revisão num comentário fixo, atualizado a cada push.

A IA explica os riscos. Ela **não aprova nem bloqueia** o PR.

> Este código era o repositório
> [iac-ai-reviewer](https://github.com/jjasonhenrique1986/iac-ai-reviewer), hoje arquivado. O
> histórico de commits foi preservado aqui.

## Uso

No repositório que vai ser revisado, crie `.github/workflows/ai-review.yml`:

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

Nenhum arquivo do revisor é copiado para o seu repositório: o código roda da pasta da action, na
versão da tag que você usa (`@v1`, `@v1.0.0` ou um SHA).

## Inputs

| Input | Obrigatório | Padrão | Descrição |
|---|---|---|---|
| `role-to-assume` | sim | — | ARN da role IAM do repositório (use um secret) |
| `aws-region` | não | `us-east-1` | região do Bedrock |
| `model-id` | não | `anthropic.claude-opus-5-5` | modelo da revisão (veja a lista abaixo) |
| `base-ref` | não | `origin/<base do PR>` | ref base do diff |
| `scanners` | não | `checkov,trivy,kube-linter,kubeconform` | scanners que rodam antes do modelo |
| `checkov-version` | não | `3.3.29` | versão do checkov |
| `checkov` | não | `true` | **obsoleto**: `false` tira o checkov da lista; use `scanners` |
| `comment` | não | `true` | publica o comentário no PR |

## Saída

| Saída | Descrição |
|---|---|
| `review-file` | caminho do Markdown com a revisão, para usar em outro passo |

## Configuração

### 1. Escolha do modelo

| `model-id` | Provedor | Observação |
|---|---|---|
| `anthropic.claude-opus-5-5` | Anthropic | padrão |
| `anthropic.claude-opus-4-8` | Anthropic | reserva para recusas do Claude |
| `openai.gpt-oss-120b-1:0` | OpenAI | modelo aberto |
| `openai.gpt-oss-20b-1:0` | OpenAI | modelo aberto, menor e mais barato |

Um modelo fora da lista não é chamado: o comentário explica e mostra os modelos aceitos. Os Claude
usam o SDK da Anthropic (saída estruturada nativa e modelo reserva para recusas). Os gpt-oss usam a
API Converse do Bedrock, com uma ferramenta forçada cujo input é a revisão; se a resposta não seguir
o formato, o revisor tenta mais uma vez, e achados que vierem cortados são descartados com aviso no
comentário.

Para ver quais modelos estão liberados na sua conta (veja [Rodando localmente](#rodando-localmente)):

```bash
python reviewer/review.py --list-models          # status do acordo de cada modelo
python reviewer/review.py --list-models --test   # e uma chamada mínima a cada um
```

O acordo aceito não garante uso: a cota do modelo também precisa ser maior que zero. Para liberar um
modelo, aceite o acesso em **Amazon Bedrock → Model catalog** e confira as cotas em
**Service Quotas → Amazon Bedrock**.

### 2. Role IAM

Crie **uma role só para o repositório que usa a action**. O identity provider do GitHub precisa estar
cadastrado no IAM (uma vez por conta). A política em [`iam/bedrock-policy.json`](iam/bedrock-policy.json)
libera os modelos da lista; deixe só os que você usa. Os Claude precisam de
`bedrock-mantle:CreateInference`; os gpt-oss, de `bedrock:InvokeModel` no ARN de cada modelo.
Troque `111122223333` e `meu-usuario/meu-repo` nos arquivos de [`iam/`](iam/) e crie a role:

```bash
aws iam create-role \
  --role-name github-meu-repo \
  --assume-role-policy-document file://iam/trust-policy.json

aws iam put-role-policy \
  --role-name github-meu-repo \
  --policy-name bedrock-modelos \
  --policy-document file://iam/bedrock-policy.json
```

O `sub` da trust policy é `repo:meu-usuario/meu-repo:pull_request`, ou seja, só workflows
disparados por pull requests desse repositório assumem a role.

> **Confira o formato do `sub` no seu repositório.** Se o repositório usa o *subject imutável*, o
> `sub` inclui os IDs numéricos do dono e do repositório, como
> `repo:meu-usuario@123456/meu-repo@7891011:pull_request`, e a trust policy acima recusa o token
> (`Not authorized to perform sts:AssumeRoleWithWebIdentity`). Para ver o prefixo que o GitHub usa:
>
> ```bash
> gh api repos/meu-usuario/meu-repo/actions/oidc/customization/sub --jq .sub_claim_prefix
> ```
>
> Na trust policy, use esse prefixo seguido de `:pull_request`.

### 3. Secret e variáveis do repositório

Em **Settings → Secrets and variables → Actions**:

| Nome | Tipo | Obrigatório | Exemplo |
|---|---|---|---|
| `AWS_ROLE_ARN` | Secret | sim | `arn:aws:iam::111122223333:role/github-meu-repo` |
| `MODEL_ID` | Variable | não | `openai.gpt-oss-120b-1:0` |

O ARN da role não é uma credencial: ele fica como secret só para o ID da conta não aparecer no
repositório nem nos logs. A action também mascara o ID da conta.

## Scanners

| Scanner | Versão | O que olha |
|---|---|---|
| [checkov](https://www.checkov.io/) | `3.3.29` (input `checkov-version`) | Terraform e Kubernetes |
| [Trivy](https://trivy.dev/) (`trivy config`) | `v0.76.0` | Terraform e Kubernetes, só severidade média ou maior |
| [kube-linter](https://github.com/stackrox/kube-linter) | `v0.8.3` | Kubernetes: regras padrão + `cluster-admin-role-binding` e `exposed-services` |
| [kubeconform](https://github.com/yannh/kubeconform) | `v0.8.0` | schema dos manifests (`-strict`), não segurança |

Os binários são baixados do GitHub Releases e só rodam se o SHA-256 bater com o fixado no
`action.yml`. Cada relatório é resumido em uma linha por achado antes de ir para o modelo. Se um
scanner falhar, a revisão sai com os outros, e o rodapé do comentário diz qual não rodou.

Por que mais de um? Nos [exemplos](#exemplos), cada scanner pega coisas diferentes:

| Risco | checkov | Trivy | kube-linter |
|---|---|---|---|
| SSH aberto, S3 público, RDS público, EKS aberto | ✅ | ✅ | — |
| Política IAM `*` em `*` | ✅ | ❌ | — |
| ServiceAccount com `cluster-admin` | ❌ | ✅ | ✅ |
| Senha num ConfigMap | ❌ | ✅ | ❌ |
| PostgreSQL num `LoadBalancer` público | ❌ | ❌ | ✅ |
| Ingress sem TLS | ❌ | ❌ | ❌ |

O Ingress sem TLS nenhum scanner aponta; só o modelo. A comparação completa está na
[pesquisa da spec 003](../specs/003-mais-scanners/research.md).

## Exemplos

A pasta [`examples/`](examples/) tem arquivos **propositalmente inseguros** para testar o revisor.
Não aplique nenhum deles numa conta ou num cluster de verdade.

| Arquivo | Problemas |
|---|---|
| `terraform/main.tf` | Security Group com SSH aberto para `0.0.0.0/0`; bucket S3 sem configuração |
| `terraform/rds/main.tf` | RDS público, sem criptografia, senha no código e sem backup |
| `terraform/iam/main.tf` | usuário IAM com access key e política `Action: "*"` em `Resource: "*"` |
| `terraform/s3-publico/main.tf` | bloqueio de acesso público desligado e leitura liberada para `Principal: "*"` |
| `terraform/eks/main.tf` | endpoint da API aberto para `0.0.0.0/0`, sem logs do control plane e sem KMS nos Secrets |
| `k8s/deployment.yaml` | imagem `latest`, senha em variável de ambiente, sem limites de recursos |
| `k8s/pod-privilegiado.yaml` | DaemonSet privilegiado, como root, com `hostNetwork`, `hostPID` e `/` do nó montado |
| `k8s/rbac-cluster-admin.yaml` | ServiceAccount de aplicação com `cluster-admin` |
| `k8s/banco-exposto.yaml` | PostgreSQL num `LoadBalancer` público e senha num ConfigMap |
| `k8s/ingress-sem-tls.yaml` | painel administrativo publicado por HTTP, sem TLS e sem autenticação |

Para testar, copie um desses arquivos para o repositório que usa a action e abra um PR.

## Estrutura

```
action.yml                 a action (composite)
reviewer/review.py         monta o prompt, chama o modelo e gera o Markdown
reviewer/requirements.txt  dependências do revisor, com versões fixadas
iam/                       trust policy e política de exemplo da role
examples/                  Terraform e manifests K8s inseguros, para testar
tests/                     testes sem AWS (dublês do Bedrock e saídas reais dos scanners)
docs/                      constituição e spec do antigo iac-ai-reviewer (histórico)
```

## Rodando localmente

Dentro de `iac-ai-review/`:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

pytest                       # testes, sem chamar a AWS
```

Para revisar um repositório local com as suas credenciais (perfil SSO, sem access key), rode a partir
da raiz desse repositório. Use um venv separado para o checkov, que pode rebaixar o `boto3`:

```bash
checkov -d . --framework terraform kubernetes --quiet --soft-fail -o json > checkov.json
trivy config --quiet --severity MEDIUM,HIGH,CRITICAL --format json -o trivy.json .
python caminho/para/iac-ai-review/reviewer/review.py --base origin/main \
  --scan checkov=checkov.json --scan trivy=trivy.json
```

Outras variáveis aceitas pelo script: `MODEL_ID`, `AWS_REGION`, `FALLBACK_MODEL_ID` e
`MAX_DIFF_CHARS` (padrão 150000). Se o diff passar do limite, o script **não corta o conteúdo**: ele
avisa no comentário e não chama o modelo.

## Segurança

- **PRs de forks não são revisados.** O GitHub não entrega o token OIDC para eles, e a condição `if`
  do workflow pula o job.
- **Use `pull_request`, nunca `pull_request_target`**: a action recusa outros eventos, para não rodar
  código do PR com permissões do repositório base.
- **O diff é tratado como dado não confiável.** Ele vai dentro de tags `<diff>`, e o prompt manda
  ignorar instruções que apareçam ali. Isso reduz, mas não elimina, o risco de prompt injection. Por
  isso o job só tem permissão para ler o código e comentar no PR, e a role só chama o modelo.
- **O conteúdo do PR vai para o Bedrock** da sua conta. Confira a política da sua empresa antes de
  usar em repositórios com dados sensíveis.
- A action usa o `actions/setup-python` com Python 3.12, o que muda o `python` dos passos seguintes
  do job.
