# Feature Specification: Action de revisão de IaC com IA

**Feature Branch**: `001-action-iac-ai-review`

**Created**: 2026-10-31

**Status**: Aprovada (2026-10-31)

**Input**: Descrição do usuário: "sobre o projeto podemos criar uma action do github e apenas
direcionar para esse projeto; nesse caso crie um repo para armazenar as actions". O projeto é o
[iac-ai-reviewer](https://github.com/jjasonhenrique1986/iac-ai-reviewer).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Revisar PRs de outro repositório com poucas linhas (Priority: P1)

Quem mantém um repositório com Terraform ou Kubernetes quer a revisão com IA nos Pull Requests sem
copiar o script, o prompt e os passos do workflow do iac-ai-reviewer. Ele adiciona um workflow curto
que chama a action, informa a role da AWS e recebe o mesmo comentário que o iac-ai-reviewer gera.

**Why this priority**: é o motivo da action existir. Hoje, para usar o revisor em outro repositório,
é preciso copiar o código, e cada cópia fica desatualizada.

**Independent Test**: num repositório de teste, um workflow com o passo de checkout e o passo da
action, com a role do repositório e `MODEL_ID` de um modelo liberado; abrir um PR que altera um
arquivo `.tf` e conferir o comentário.

**Acceptance Scenarios**:

1. **Given** um repositório com role IAM própria e o workflow que usa a action, **When** um PR altera
   arquivos Terraform ou YAML, **Then** o PR recebe um comentário de revisão igual ao do
   iac-ai-reviewer (risco geral, achados, rodapé com o modelo).
2. **Given** um PR com novos pushes, **When** a action roda de novo, **Then** o mesmo comentário é
   atualizado, em vez de um comentário novo.
3. **Given** o mesmo workflow, **When** o usuário troca o modelo por um input, **Then** a revisão usa
   o modelo informado, dentro da lista aceita pelo iac-ai-reviewer.

---

### User Story 2 - Controlar a versão do revisor (Priority: P2)

Quem usa a action quer saber exatamente qual versão do iac-ai-reviewer está rodando e atualizar
quando quiser, sem ser surpreendido por uma mudança no projeto.

**Why this priority**: sem versão fixa, uma mudança no iac-ai-reviewer muda o comportamento de todos
os repositórios de uma vez (Princípio II).

**Independent Test**: rodar a action sem informar versão e conferir no log a versão padrão; rodar
com uma versão informada e conferir que ela foi usada.

**Acceptance Scenarios**:

1. **Given** a action numa versão (`@v1`), **When** o usuário não informa a versão do revisor,
   **Then** é usada a versão do iac-ai-reviewer fixada naquela versão da action.
2. **Given** um input com outra tag ou SHA do iac-ai-reviewer, **When** a action roda, **Then** essa
   versão é usada e aparece no log.

---

### User Story 3 - Não gastar com PRs sem infraestrutura (Priority: P3)

Quem usa a action não quer pagar chamada de modelo nem precisar de credencial da AWS quando o PR não
altera nenhum arquivo de infraestrutura.

**Why this priority**: reduz custo e permite testar a action no próprio repositório sem AWS
(Princípio V).

**Independent Test**: PR que só altera um `README.md`, com o workflow sem role válida; a action
termina com sucesso e o comentário diz que não há mudanças de Terraform ou YAML.

**Acceptance Scenarios**:

1. **Given** um PR sem mudanças em `.tf`, `.tfvars`, `.yaml` ou `.yml`, **When** a action roda,
   **Then** ela não assume a role, não chama o modelo e publica o aviso de que não há mudanças.

---

### Edge Cases

- **PR de fork**: o GitHub não entrega o token OIDC. O README MUST mostrar a condição que pula o job,
  e a action, se rodar mesmo assim, MUST falhar com mensagem clara sobre a falta de credencial.
- **Checkout raso**: sem histórico, o diff contra a branch base não funciona. A action MUST detectar
  e falhar com mensagem dizendo para usar `fetch-depth: 0`.
- **Role sem permissão ou modelo sem cota**: o comentário mostra a mensagem do iac-ai-reviewer
  (acesso negado, cota), e o job não falha por isso (Princípio III do iac-ai-reviewer).
- **Versão do revisor inexistente**: a action MUST falhar no início com mensagem dizendo qual versão
  não foi encontrada.
- **Código do revisor no workspace**: o código buscado não pode entrar no diff nem na análise do
  checkov do repositório que usa a action.
- **Evento que não é pull request**: a action MUST falhar com mensagem clara, porque não existe PR
  para comentar.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A action MUST ficar num repositório público próprio para actions, numa pasta com o nome
  da action, e ser usada pelo caminho `dono/repositório/pasta@versão`.
- **FR-002**: A action MUST executar o iac-ai-reviewer, sem copiar a lógica dele (Princípio I).
- **FR-003**: A action MUST receber a role da AWS a assumir (obrigatório), a região (padrão
  `us-east-1`) e o modelo (opcional; sem ele vale o padrão do iac-ai-reviewer).
- **FR-004**: A action MUST receber a versão do iac-ai-reviewer, com um valor padrão fixo em cada
  versão da action (FR de versão, US2).
- **FR-005**: A action MUST rodar o checkov no repositório do usuário e enviar o resultado ao revisor,
  com um input para desligar essa etapa.
- **FR-006**: A action MUST publicar a revisão como comentário fixo no PR, atualizado a cada execução.
- **FR-007**: Sem mudanças de infraestrutura no PR, a action MUST NOT assumir a role nem chamar o
  modelo (US3).
- **FR-008**: A action MUST mascarar o ID da conta AWS nos logs e MUST NOT pedir access key.
- **FR-009**: A action MUST expor como saída o caminho do arquivo com a revisão em Markdown, para
  quem quiser usar a revisão em outro passo.
- **FR-010**: O README MUST mostrar o workflow mínimo de uso, as `permissions` necessárias, a condição
  de forks, a criação da role (com link para o iac-ai-reviewer) e a tabela de inputs e saídas.
- **FR-011**: O repositório MUST ter um workflow de teste que roda a action num PR sem mudanças de
  infraestrutura (sem AWS) e um que roda com mudanças reais (com AWS, só no próprio repositório).
- **FR-012**: As versões da action MUST seguir tags semver com tag principal móvel (`v1`).

### Key Entities

- **Action `iac-ai-review`**: a unidade publicada; tem inputs, uma saída e uma versão.
- **Versão do revisor**: tag ou SHA do iac-ai-reviewer usada numa execução.
- **Repositório usuário**: repositório que chama a action; tem a sua própria role IAM.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Um repositório novo passa a ter revisão com IA adicionando um workflow de no máximo
  25 linhas, sem copiar nenhum arquivo do iac-ai-reviewer.
- **SC-002**: O comentário gerado pela action no PR de teste tem o mesmo formato do comentário gerado
  pelo workflow do próprio iac-ai-reviewer para o mesmo diff.
- **SC-003**: Um PR sem mudanças de infraestrutura termina em menos de 3 minutos, sem nenhuma chamada
  à AWS.
- **SC-004**: A versão do iac-ai-reviewer usada aparece no log de toda execução.

## Assumptions

- O iac-ai-reviewer terá uma tag de release (`v1.0.0`) depois do merge dos PRs #3 e #4; ela será a
  versão padrão da primeira versão da action.
- O teste com AWS deste repositório usa uma role própria (`gh-github-actions`) criada no
  `aws-iam-baseline` pelo módulo `github-oidc-role`, com permissão só para o gpt-oss; o `apply` é
  feito pelo usuário.
- Enquanto a cota do Claude estiver zerada na conta, os testes usam `openai.gpt-oss-120b-1:0`.
- O workflow do próprio iac-ai-reviewer continua usando o script local, para testar as mudanças do
  PR; migrar ele para a action está fora do escopo.
- Fora do escopo: outras actions além da `iac-ai-review`, publicação no GitHub Marketplace.
