# github-actions

Actions reutilizáveis do GitHub. Cada action fica numa pasta própria e é usada assim:

```yaml
- uses: jjasonhenrique1986/github-actions/<action>@v1
```

## Actions

| Action | O que faz |
|---|---|
| [`iac-ai-review`](iac-ai-review/) | Revisa Terraform e Kubernetes de um Pull Request com IA no Amazon Bedrock (Claude ou gpt-oss) e comenta no PR |

## Regras

- **Cada action é autocontida.** Código, testes, exemplos e documentação ficam na pasta dela. O
  repositório que usa a action só cria um workflow; nada é copiado nem baixado de outro lugar.
- **Versões:** tags semver (`v1.2.3`) e uma tag principal móvel (`v1`). Mudança incompatível gera uma
  nova versão principal. Para builds 100% reproduzíveis, fixe a tag completa ou o SHA.
- **Sem credenciais fixas:** acesso à AWS só por OIDC, com uma role própria por repositório.

O desenvolvimento segue o [Spec Kit](https://github.com/github/spec-kit): a constituição está em
[`.specify/memory/constitution.md`](.specify/memory/constitution.md) e as specs em [`specs/`](specs/).
