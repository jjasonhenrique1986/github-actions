# Tasks: Mais scanners além do checkov

## Phase 1: Setup

- [ ] T001 Gerar as amostras reais (JSON) dos 4 scanners nos exemplos em
  `iac-ai-review/tests/fixtures/scanners/` (versões do plano)

## Phase 2: Foundational

- [ ] T002 [P] Testes dos conversores com as amostras (um por scanner) e de remoção de duplicadas
- [ ] T003 Conversores e `--scan`/`--scan-failed` no `review.py`, mantendo `--checkov`
- [ ] T004 Prompt com `<scanners>` e subtags; system prompt atualizado; teste do prompt
- [ ] T005 Rodapé com scanners que rodaram e que falharam; teste do render

## Phase 3: User Story 1 - Trivy (P1) 🎯 MVP

- [ ] T006 [US1] Passo de instalação do Trivy (download, `sha256sum -c`) e execução com
  `--severity MEDIUM,HIGH,CRITICAL --format json`

## Phase 4: User Story 2 - kube-linter (P2)

- [ ] T007 [US2] Passo do kube-linter com `--include cluster-admin-role-binding,exposed-services`

## Phase 5: User Story 3 - kubeconform (P3)

- [ ] T008 [US3] Passo do kubeconform (`-strict -output json`) só sobre arquivos YAML
- [ ] T009 [P] [US3] Fixture inválido no teste: manifest com campo inexistente

## Phase 6: User Story 4 - Escolher os scanners (P3)

- [ ] T010 [US4] Input `scanners` com validação; compatibilidade com `checkov: false`
- [ ] T011 [US4] Job de teste: scanner inválido falha; scanner com hash errado vira aviso

## Phase 7: Polish

- [ ] T012 [P] README: scanners, input, tabela de cobertura do research
- [ ] T013 Medir o prompt dos exemplos com os 4 scanners (SC-002) e o tempo do job (SC-003)
- [ ] T014 PR, CI verde (inclusive `com-aws`), merge pelo usuário, tags `v1.1.0` e `v1`

## Dependencies

T001 → T002 → T003–T005 → T006–T011 → T012–T014.
