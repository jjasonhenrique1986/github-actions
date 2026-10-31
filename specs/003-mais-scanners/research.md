# Research: mais scanners além do checkov

**Data**: 2026-10-31 · Execução local nos 10 arquivos de `iac-ai-review/examples/`.

## Versões testadas

| Ferramenta | Versão | Publicada em | Verificação do download |
|---|---|---|---|
| checkov | 3.4.0 | 2026-10-28 | PyPI |
| Trivy | v0.76.0 | 2026-10-14 | `trivy_0.76.0_checksums.txt` (OK) |
| kube-linter | v0.8.3 | 2026-03-10 | só bundle sigstore publicado; sem arquivo de checksum |
| kubeconform | v0.8.0 | 2026-06-04 | `CHECKSUMS` (OK) |

SHA-256 dos pacotes baixados (para fixar na action):

```text
e24b1c51293c1b15e4ba8d45bbc7891ba053f90278ec2698f3562c993e145fe7  trivy_0.76.0_Linux-64bit.tar.gz
1a6d8419b11971372971fdbc22682b684ebfb7cf1c39591662d1b6ca736c41df  kube-linter-linux.tar.gz
9bc2bffbf71f261128533edaf912153948b7ff238f9a531ae6d34466ec287883  kubeconform-linux-amd64.tar.gz
```

## Comandos

```bash
trivy config --quiet --format json .
kube-linter lint k8s --format json                       # regras padrão
kube-linter lint k8s --add-all-built-in --format json    # todas as regras
kube-linter lint k8s --include cluster-admin-role-binding,exposed-services
kubeconform -strict -summary -output json k8s
checkov -d . --framework terraform kubernetes --compact --quiet --soft-fail
```

## Cobertura dos riscos principais

✅ = aponta o risco · ❌ = não aponta. "IA" = gpt-oss-120b com só o checkov, no PR #4 do antigo
iac-ai-reviewer e em 3 execuções locais; o SSH aberto vem do job `com-aws` (fixture), já que o
`terraform/main.tf` não mudou no PR #4.

| Risco (arquivo) | checkov | Trivy | kube-linter padrão | kube-linter + extras | IA |
|---|---|---|---|---|---|
| SSH aberto para `0.0.0.0/0` (`terraform/main.tf`) | ✅ CKV_AWS_24 | ✅ AWS-0107 | — | — | ✅ |
| Política IAM `*` em `*` (`terraform/iam`) | ✅ CKV_AWS_62/63 | ❌ só AWS-0143 (política em usuário) | — | — | ✅ |
| Bucket com acesso público (`terraform/s3-publico`) | ✅ CKV_AWS_53–56 | ✅ AWS-0086/87/91/93 | — | — | ✅ |
| RDS público e sem criptografia (`terraform/rds`) | ✅ CKV_AWS_17 | ✅ AWS-0180, AWS-0080 | — | — | ✅ |
| Endpoint do EKS aberto (`terraform/eks`) | ✅ CKV_AWS_38/39 | ✅ AWS-0040/41 | — | — | ✅ |
| Container privilegiado, `hostNetwork`, `hostPID` | ✅ CKV_K8S_16/17/19 | ✅ KSV-0017/09/10 | ✅ | ✅ | ✅ |
| ServiceAccount com `cluster-admin` | ❌ | ✅ KSV-0111 | ❌ | ✅ `cluster-admin-role-binding` | ✅ |
| Senha num ConfigMap (`banco-exposto`) | ❌ | ✅ KSV-0109 | ❌ | ❌ | ✅ |
| PostgreSQL num `LoadBalancer` (`banco-exposto`) | ❌ | ❌ | ❌ | ✅ `exposed-services` | ✅ |
| Ingress sem TLS (`ingress-sem-tls`) | ❌ | ❌ | ❌ | ❌ (só `dangling-ingress`) | ✅ |
| Schema dos manifests | — | — | — | — | — |

kubeconform: os 8 objetos dos exemplos são válidos (`valid: 8, invalid: 0`). Ele não procura riscos
de segurança; o valor dele é pegar `apiVersion` removida, campo inexistente ou tipo errado, que os
outros não pegam.

## Conclusões

- **Trivy** complementa o checkov: pega o `cluster-admin` e a senha no ConfigMap. Perde a política
  IAM `*`, que o checkov pega bem. Os dois juntos cobrem mais do que cada um sozinho.
- **kube-linter** só agrega com regras além das padrão: `cluster-admin-role-binding` e
  `exposed-services`. Com `--add-all-built-in` ele fica ruidoso (`sorted-keys`,
  `required-label-owner`, `minimum-three-replicas`), então a proposta é padrão + essas duas.
- **kubeconform** é validação de schema, não de segurança.
- **Ingress sem TLS**: nenhum scanner pega; só a IA. Fica como exemplo de que a IA continua útil.
- **Tamanho**: a saída em tabela do Trivy (MEDIUM+) tem 64 KB, o checkov 32 KB. Somados ao diff,
  chegam perto do `MAX_DIFF_CHARS` (150 000). As saídas precisam ser resumidas (uma linha por achado)
  antes de ir para o modelo.
- **Rede em execução**: o Trivy baixa o bundle de regras na primeira execução (do registro de
  containers da Aqua). Isso precisa de rede no runner, que o `ubuntu-latest` tem.
