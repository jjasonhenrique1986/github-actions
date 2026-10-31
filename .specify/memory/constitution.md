<!--
Sync Impact Report
- Version change: template → 1.0.0 (primeira adoção)
- Princípios definidos: I. Action fina, lógica no projeto; II. Versões fixadas; III. Sem credenciais
  fixas; IV. Permissões mínimas; V. Testada no próprio repositório; VI. Documentação em português
- Seções adicionadas: Restrições de plataforma; Fluxo de desenvolvimento; Governance
- Seções removidas: nenhuma
- TODOs: nenhum
-->

# github-actions Constitution

Repositório público que guarda actions reutilizáveis do GitHub. Cada action fica numa pasta própria
(`<nome>/action.yml`) e é usada como `jjasonhenrique1986/github-actions/<nome>@<versão>`.

## Core Principles

### I. Action fina, lógica no projeto

Uma action MUST só orquestrar: preparar o ambiente, buscar o código do projeto que ela representa e
chamá-lo. A lógica de negócio (por exemplo, montar o prompt ou validar a revisão) MUST ficar no
repositório do projeto, nunca copiada para cá. Cada action documenta qual projeto ela chama.

Racional: uma correção no projeto chega a todos os usuários da action sem duplicar código.

### II. Versões fixadas

O código do projeto chamado pela action MUST ser buscado numa versão fixa (tag ou SHA), escolhida por
um input com valor padrão. Actions de terceiros MUST ser fixadas por tag de versão. As actions deste
repositório são publicadas com tags semver (`v1.2.3`) e uma tag de versão principal móvel (`v1`).
Mudança incompatível nos inputs ou no comportamento MUST gerar uma nova versão principal.

Racional: quem usa a action precisa de builds reproduzíveis e de controle sobre quando atualizar.

### III. Sem credenciais fixas

Nenhuma action MAY exigir access key, token de longa duração ou senha. O acesso à AWS MUST ser por
OIDC (`role-to-assume`), com o ID da conta mascarado nos logs. O token do GitHub usado é o
`github.token` do próprio job.

Racional: o mesmo da constituição do iac-ai-reviewer; chave fixa vazada dá acesso até alguém perceber.

### IV. Permissões mínimas

O README de cada action MUST listar as `permissions` mínimas que o workflow que a usa precisa e
MUST NOT pedir mais do que isso. Cada repositório que usa uma action com AWS MUST ter a sua própria
role IAM (regra do `aws-iam-baseline`), nunca reaproveitar a role de outro repositório.

Racional: um repositório comprometido só alcança o que a role e o token dele permitem.

### V. Testada no próprio repositório

Cada action MUST ter um workflow de teste neste repositório que roda a action de verdade. Os testes
que não dependem da AWS MUST rodar em todo PR; os que chamam a AWS rodam só em PRs do próprio
repositório (forks não recebem o token OIDC).

Racional: uma action quebrada afeta todos os repositórios que a usam de uma vez.

### VI. Documentação em português

README, inputs, mensagens, specs e commits MUST ser em português do Brasil. Exemplos MUST usar
valores fictícios (`111122223333`, `meu-usuario/meu-repo`), nunca IDs reais.

Racional: o repositório acompanha o blog, que é em português, e é público.

## Restrições de plataforma

- Tipo de action: composite (`runs.using: composite`), sem imagem Docker própria e sem código
  JavaScript compilado neste repositório.
- Runner: `ubuntu-latest` do GitHub.
- State de qualquer IaC de apoio fica em `s3://terraform-projetos/<projeto>/`; mudanças de IAM ficam
  no `aws-iam-baseline`, não aqui.

## Fluxo de desenvolvimento

- Toda action nova ou mudança de comportamento segue o Spec Kit: `spec.md` → `plan.md` →
  `tasks.md` → implementação, com aprovação entre a spec e a implementação.
- Todo PR MUST passar no workflow de teste e no `actionlint`.
- Release: tag semver + atualização da tag principal, depois do merge na `main`.

## Governance

Esta constituição prevalece sobre outras práticas do repositório. Emendas são feitas por PR que altera
este arquivo, com o motivo na descrição e a versão atualizada por semver: MAJOR para remover ou
redefinir um princípio, MINOR para adicionar princípio ou seção, PATCH para ajustes de texto.
Toda spec e todo plano MUST passar pelo "Constitution Check" do `plan.md` antes da implementação.

**Version**: 1.0.0 | **Ratified**: 2026-10-31 | **Last Amended**: 2026-10-31
