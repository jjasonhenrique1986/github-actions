# github-actions

Actions reutilizáveis do GitHub. Cada action fica numa pasta própria e é usada assim:

```yaml
- uses: jjasonhenrique1986/github-actions/<action>@v1
```

## Actions

| Action | O que faz | Projeto |
|---|---|---|
| [`iac-ai-review`](iac-ai-review/) | Revisa Terraform e Kubernetes de um Pull Request com IA no Amazon Bedrock e comenta no PR | [iac-ai-reviewer](https://github.com/jjasonhenrique1986/iac-ai-reviewer) |

## Regras

- **A action só orquestra.** A lógica fica no repositório do projeto, que a action busca numa versão
  fixa. Uma correção no projeto chega a todos que usam a action.
- **Versões:** tags semver (`v1.2.3`) e uma tag principal móvel (`v1`). Mudança incompatível gera uma
  nova versão principal. Para builds 100% reproduzíveis, fixe a tag completa ou o SHA.
- **Sem credenciais fixas:** acesso à AWS só por OIDC, com uma role própria por repositório.

O desenvolvimento segue o [Spec Kit](https://github.com/github/spec-kit): a constituição está em
[`.specify/memory/constitution.md`](.specify/memory/constitution.md) e as specs em [`specs/`](specs/).
