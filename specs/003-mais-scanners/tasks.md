# Tasks: Mais scanners além do checkov

## Phase 1: Setup

- [x] T001 Gerar as amostras reais (JSON) dos 4 scanners nos exemplos em
  `iac-ai-review/tests/fixtures/scanners/` (versões do plano)

## Phase 2: Foundational

- [x] T002 [P] Testes dos conversores com as amostras (um por scanner) e de remoção de duplicadas
- [x] T003 Conversores e `--scan`/`--scan-failed` no `review.py`, mantendo `--checkov`
- [x] T004 Prompt com `<scanners>` e subtags; system prompt atualizado; teste do prompt
- [x] T005 Rodapé com scanners que rodaram e que falharam; teste do render

## Phase 3: User Story 1 - Trivy (P1) 🎯 MVP

- [x] T006 [US1] Passo de instalação do Trivy (download, `sha256sum -c`) e execução com
  `--severity MEDIUM,HIGH,CRITICAL --format json`

## Phase 4: User Story 2 - kube-linter (P2)

- [x] T007 [US2] Passo do kube-linter com `--include cluster-admin-role-binding,exposed-services`

## Phase 5: User Story 3 - kubeconform (P3)

- [x] T008 [US3] Passo do kubeconform (`-strict -output json`) só sobre arquivos YAML
- [x] T009 [P] [US3] Fixture inválido no teste: manifest com campo inexistente

## Phase 6: User Story 4 - Escolher os scanners (P3)

- [x] T010 [US4] Input `scanners` com validação; compatibilidade com `checkov: false`
- [x] T011 [US4] Job de teste: scanner inválido falha. Scanner que falha vira aviso: coberto por teste unitário (`test_main_sends_scans_and_reports_failures`); simular hash errado no CI exigiria um input só para teste, então ficou de fora

## Phase 7: Polish

- [x] T012 [P] README: scanners, input, tabela de cobertura do research
- [x] T013 Medir: resumos dos 4 scanners nos exemplos = 16 268 caracteres (SC-002); job `com-aws` 55 s com os 4 scanners contra 56 s na v1.0 (SC-003)
- [ ] T014 PR, CI verde (inclusive `com-aws`), merge pelo usuário, tags `v1.1.0` e `v1`

## Dependencies

T001 → T002 → T003–T005 → T006–T011 → T012–T014.
