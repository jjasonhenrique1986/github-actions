# iac-ai-reviewer

Revisão automática de Pull Requests de infraestrutura (Terraform e Kubernetes)
com o **Claude no Amazon Bedrock**, rodando no **GitHub Actions** sem access keys.

A cada PR o workflow:

1. Roda o **checkov** no repositório, para ter achados determinísticos.
2. Assume uma role IAM via **OIDC** (credenciais temporárias).
3. Envia o diff dos arquivos `.tf`, `.tfvars`, `.yaml` e `.yml` e a saída do
   checkov para o Claude, que devolve uma revisão em **JSON validado** (Pydantic).
4. Publica a revisão como comentário no PR, atualizando o mesmo comentário a cada push.

A IA explica os riscos. Ela **não aprova nem bloqueia** o PR.

## Estrutura

```
.github/workflows/ai-review.yml   workflow do GitHub Actions
reviewer/review.py                script que monta o prompt, chama o Claude e gera o Markdown
iam/trust-policy.json             trust policy da role (OIDC do GitHub)
iam/bedrock-policy.json           permissão para chamar o Claude no Bedrock
examples/                         Terraform e manifest K8s com problemas, para testar
tests/                            testes sem AWS (um servidor local simula o Bedrock)
```

## Configuração

### 1. Acesso ao modelo no Bedrock

Confira em **Amazon Bedrock → Model access** se a conta tem acesso ao modelo
que você vai usar. O padrão é `anthropic.claude-opus-5-5`, e o modelo reserva
para recusas é `anthropic.claude-opus-4-8`.

### 2. Role IAM

O identity provider do GitHub precisa estar cadastrado no IAM (uma vez por conta).
Troque `111122223333` e `meu-usuario/meu-repo` nos arquivos de `iam/` e crie a role:

```bash
aws iam create-role \
  --role-name github-iac-ai-reviewer \
  --assume-role-policy-document file://iam/trust-policy.json

aws iam put-role-policy \
  --role-name github-iac-ai-reviewer \
  --policy-name bedrock-claude \
  --policy-document file://iam/bedrock-policy.json
```

O `sub` da trust policy é `repo:meu-usuario/meu-repo:pull_request`, ou seja, só
workflows disparados por pull requests desse repositório assumem a role.

### 3. Variáveis do repositório

Em **Settings → Secrets and variables → Actions → Variables**:

| Variável | Obrigatória | Exemplo |
|---|---|---|
| `AWS_ROLE_ARN` | sim | `arn:aws:iam::111122223333:role/github-iac-ai-reviewer` |
| `AWS_REGION` | não (padrão `us-east-1`) | `us-east-1` |
| `MODEL_ID` | não (padrão `anthropic.claude-opus-5-5`) | `anthropic.claude-sonnet-5-5` |

Não há nenhum secret: a autenticação é toda por OIDC.

## Rodando localmente

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt checkov

pytest                       # testes, sem chamar a AWS

checkov -d . --framework terraform kubernetes --compact --quiet --soft-fail > checkov.txt
python reviewer/review.py --base origin/main --checkov checkov.txt   # usa suas credenciais AWS
```

Outras variáveis aceitas pelo script: `FALLBACK_MODEL_ID` e `MAX_DIFF_CHARS`
(padrão 150000). Se o diff passar do limite, o script **não corta o conteúdo**:
ele avisa no comentário e não chama o modelo.

## Segurança

- **PRs de forks não são revisados.** O GitHub não entrega o token OIDC para eles,
  e o job é pulado.
- **O diff é tratado como dado não confiável.** Ele vai dentro de tags `<diff>`, e o
  prompt manda ignorar instruções que apareçam ali. Isso reduz, mas não elimina, o
  risco de prompt injection. Por isso o job só tem permissão para ler o código e
  comentar no PR.
- **Use `pull_request`, nunca `pull_request_target`**, para não rodar código do PR
  com permissões do repositório base.
- **O conteúdo do PR vai para o Bedrock.** Confira a política da sua empresa antes
  de usar em repositórios com dados sensíveis.
