# Feature Specification: Mais scanners além do checkov

**Feature Branch**: `003-mais-scanners`

**Created**: 2026-10-31

**Status**: Draft

**Input**: Pergunta do usuário: "além do checkov dá pra usar outros mecanismos?", seguida de "pode
rodar os três nos exemplos e escrever a spec 003" (Trivy, kube-linter e kubeconform). Resultados em
[research.md](research.md).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Trivy como segunda base de regras (Priority: P1)

Quem recebe a revisão quer que ela se apoie em mais de uma ferramenta determinística, para que riscos
que o checkov não conhece (ServiceAccount com `cluster-admin`, senha em ConfigMap) cheguem ao modelo
como evidência, e não dependam só da leitura da IA.

**Why this priority**: nos exemplos, o Trivy foi o que mais acrescentou ao checkov.

**Independent Test**: PR com `examples/k8s/rbac-cluster-admin.yaml`; o relatório enviado ao modelo
contém o achado do Trivy (KSV-0111) e o comentário cita o risco.

**Acceptance Scenarios**:

1. **Given** um PR com Terraform ou Kubernetes, **When** a action roda com o Trivy ligado, **Then** os
   achados do Trivy de severidade média ou maior chegam ao modelo, identificados como do Trivy.
2. **Given** checkov e Trivy apontando o mesmo risco, **When** o modelo revisa, **Then** o comentário
   traz o risco uma vez só.

---

### User Story 2 - kube-linter para riscos específicos de Kubernetes (Priority: P2)

Quem altera manifests quer que exposições de serviço (`LoadBalancer`) e bindings de `cluster-admin`
sejam apontados por uma regra, não só pela IA.

**Why this priority**: só o kube-linter, com duas regras extras, pegou o `LoadBalancer` público.

**Independent Test**: PR com `examples/k8s/banco-exposto.yaml`; o relatório contém
`exposed-services`.

**Acceptance Scenarios**:

1. **Given** um PR com manifests, **When** a action roda com o kube-linter ligado, **Then** ele usa as
   regras padrão mais `cluster-admin-role-binding` e `exposed-services`.
2. **Given** um PR só com Terraform, **When** a action roda, **Then** o kube-linter não gera achados nem
   erro.

---

### User Story 3 - kubeconform para manifests inválidos (Priority: P3)

Quem altera manifests quer saber, no mesmo comentário, se algum objeto não passa no schema da API do
Kubernetes (campo inexistente, `apiVersion` removida, tipo errado).

**Why this priority**: não é segurança, mas evita que um manifest quebrado passe pela revisão.

**Independent Test**: PR com um manifest com campo inexistente; o comentário aponta o erro de schema.

**Acceptance Scenarios**:

1. **Given** um manifest inválido no PR, **When** a action roda, **Then** o erro do kubeconform chega
   ao modelo e aparece no comentário.
2. **Given** só manifests válidos, **When** a action roda, **Then** nada sobre schema aparece.

---

### User Story 4 - Escolher os scanners (Priority: P3)

Quem usa a action quer ligar e desligar scanners por um input, por exemplo para economizar tempo num
repositório só de Terraform.

**Acceptance Scenarios**:

1. **Given** o input de scanners sem valor, **When** a action roda, **Then** os quatro rodam.
2. **Given** o input com só `checkov`, **When** a action roda, **Then** só o checkov roda.
3. **Given** um nome de scanner desconhecido, **When** a action roda, **Then** ela falha no início com
   mensagem listando os nomes aceitos.

---

### Edge Cases

- **Scanner falha** (download, execução, saída ilegível): a revisão continua com os outros scanners e
  o comentário diz qual scanner não rodou. A action não inventa achados nem falha o job por isso.
- **Saídas grandes**: os relatórios são resumidos (uma linha por achado) antes de ir para o modelo, e o
  tamanho total continua limitado pelo `MAX_DIFF_CHARS`; acima dele, o comportamento atual se mantém
  (aviso, sem chamar o modelo).
- **Achados fora das linhas alteradas**: os scanners analisam o repositório inteiro; o prompt continua
  pedindo para focar no diff.
- **Download adulterado**: binário com hash diferente do esperado não é executado (scanner conta como
  falha).
- **PR sem infraestrutura**: nenhum scanner roda (comportamento atual).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A action MUST suportar os scanners `checkov`, `trivy`, `kube-linter` e `kubeconform`,
  escolhidos por um input com os quatro como padrão.
- **FR-002**: O input `checkov` (booleano) da v1 MUST continuar funcionando: `false` tira o checkov da
  lista. Ele passa a ser documentado como obsoleto.
- **FR-003**: Cada scanner MUST rodar numa versão fixa, e binários baixados MUST ter o SHA-256
  conferido antes de rodar.
- **FR-004**: O Trivy MUST enviar só achados de severidade média, alta e crítica.
- **FR-005**: O kube-linter MUST usar as regras padrão mais `cluster-admin-role-binding` e
  `exposed-services`.
- **FR-006**: O revisor MUST receber o relatório de cada scanner separado e identificado, resumido em
  uma linha por achado (arquivo, linha quando houver, severidade, ID da regra, título).
- **FR-007**: O prompt MUST tratar os relatórios como evidência, pedir para não repetir o mesmo risco
  apontado por mais de um scanner e manter a regra de ignorar instruções dentro deles.
- **FR-008**: O comentário MUST listar no rodapé os scanners que rodaram e os que falharam.
- **FR-009**: Os testes sem AWS MUST cobrir a conversão de cada formato de relatório e o caso de
  scanner que falhou, com amostras reais geradas a partir dos exemplos.
- **FR-010**: O README MUST documentar os scanners, o input e a tabela de cobertura do research.

### Key Entities

- **Scanner**: nome, versão fixa, forma de instalação, comando e conversor de saída.
- **Relatório de scanner**: lista de achados resumidos ou o motivo da falha.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Nos exemplos, os relatórios enviados ao modelo apontam o `cluster-admin`, a senha no
  ConfigMap e o `LoadBalancer` público (hoje nenhum dos três vem do checkov).
- **SC-002**: Com os quatro scanners, o prompt dos exemplos fica abaixo de 150 000 caracteres.
- **SC-003**: Um PR com manifests leva no máximo 2 minutos a mais do que hoje.
- **SC-004**: Uma falha simulada de um scanner gera revisão com os outros e aviso no rodapé.

## Assumptions

- Lançado como `v1.1.0` (compatível com a v1: inputs antigos continuam valendo; o comentário ganha
  informação). A tag `v1` passa a apontar para ela.
- O Trivy baixa o bundle de regras em execução; o runner tem rede.
- O kube-linter não publica arquivo de checksum, só bundle sigstore. A action confere o SHA-256 fixado
  no próprio `action.yml` (o mesmo método vale para os três binários).
- Fora do escopo: `terraform plan` (precisaria de role com leitura da infraestrutura), Infracost
  (precisa de API key), conftest/OPA (políticas a escrever), TFLint.
