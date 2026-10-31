# Implementation Plan: Mais scanners além do checkov

**Branch**: `003-mais-scanners` | **Date**: 2026-10-31 | **Spec**: [spec.md](spec.md) |
**Research**: [research.md](research.md)

## Summary

A action passa a rodar até quatro scanners (checkov, Trivy, kube-linter, kubeconform) e o revisor
recebe um relatório resumido de cada um, numa tag própria do prompt.

## Technical Context

**Language/Version**: Python 3.12 (revisor), Bash e YAML (action)
**Primary Dependencies**: checkov 3.3.29 (PyPI), Trivy v0.76.0, kube-linter v0.8.3, kubeconform
v0.8.0 (binários do GitHub Releases, SHA-256 fixado)
**Testing**: `pytest` com amostras reais de saída em `iac-ai-review/tests/fixtures/scanners/`
**Constraints**: prompt total abaixo de `MAX_DIFF_CHARS`; nenhum scanner pode derrubar a revisão

## Constitution Check (2.0.0)

| Princípio | Como o plano atende |
|---|---|
| I. Action autocontida | Conversores no `review.py` da pasta da action; os scanners são ferramentas externas fixadas, como o checkov já era. |
| II. Versões fixadas | Versão e SHA-256 de cada binário no `action.yml`; checkov por versão exata. |
| III. Sem credenciais fixas | Nenhum scanner usa credencial. |
| IV. Permissões mínimas | Nenhuma permissão nova. |
| V. Testada | Amostras reais de cada formato em testes; job `com-aws` com os quatro scanners. |
| Regras da iac-ai-review | Scanner que falha vira aviso no rodapé (a IA não inventa); prompt continua tratando relatórios como dado não confiável. |

## Decisões

1. **Formato de entrada no revisor**: novo argumento repetível `--scan NOME=ARQUIVO` (JSON nativo do
   scanner) e `--scan-failed NOME`. O `--checkov ARQUIVO` atual continua aceito (texto), para não
   quebrar uso local. Com `--scan`, o checkov passa a gerar JSON (`-o json`).
2. **Conversores** (um por scanner) produzem linhas `arquivo:linha [SEVERIDADE] ID título`:
   - checkov: `results.failed_checks[]` (`file_path`, `file_line_range`, `check_id`, `check_name`,
     `severity` quando houver).
   - Trivy: `Results[].Misconfigurations[]` com `Status == FAIL` (`Target`, `CauseMetadata.StartLine`,
     `Severity`, `ID`, `Title`); filtro `--severity MEDIUM,HIGH,CRITICAL` já na execução.
   - kube-linter: `Reports[]` (`Object.Metadata.FilePath`, `Check`, `Diagnostic.Message`).
   - kubeconform: `resources[]` com `status` `statusInvalid`/`statusError` (`filename`, `kind`,
     `name`, `msg`).
   Caminhos relativos à raiz do repositório. Linhas repetidas são removidas.
3. **Prompt**: `<scanners>` com uma subtag por scanner (`<trivy>…</trivy>`); o system prompt troca
   "relatório do checkov" por "relatórios dos scanners" e pede para unir achados equivalentes.
4. **Instalação**: um passo por scanner com `continue-on-error: true` e `id`; um passo final monta os
   argumentos `--scan`/`--scan-failed` a partir do `outcome` de cada um. Binários vão para
   `$RUNNER_TEMP/bin`; o `sha256sum -c` roda antes de extrair.
5. **Input**: `scanners` (padrão `checkov,trivy,kube-linter,kubeconform`), validado contra a lista;
   `checkov: false` remove o checkov (FR-002).
6. **Rodapé**: `Scanners: checkov, trivy, kube-linter, kubeconform` e, se houver,
   `⚠️ não rodaram: trivy`.
7. **Release**: `v1.1.0` e mover `v1`.

## Project Structure

```text
iac-ai-review/
├── action.yml                          # input scanners, passos por scanner
├── reviewer/review.py                  # --scan, conversores, prompt, rodapé
├── tests/test_scanners.py              # novo
└── tests/fixtures/scanners/            # saídas reais (JSON) dos 4 scanners nos exemplos
specs/003-mais-scanners/
```
