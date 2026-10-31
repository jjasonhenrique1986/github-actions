"""Conversores dos relatórios dos scanners, com saídas reais geradas a partir de `examples/`.

As amostras em `fixtures/scanners/` foram reduzidas aos campos que os conversores leem; os valores
são os da execução real (checkov 3.4.0, Trivy v0.76.0, kube-linter v0.8.3, kubeconform v0.8.0).
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "reviewer"))
import review  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures" / "scanners"
RUNNER_ROOT = Path("/home/runner/work/repo/repo")


def summary(name: str, root: Path = RUNNER_ROOT) -> str:
    return review.summarize_scan(name, FIXTURES / f"{name}.json", root)


def test_checkov_lines():
    text = summary("checkov")
    assert "terraform/main.tf:16 CKV_AWS_24 Ensure no security groups allow ingress from 0.0.0.0:0 to port 22" in text
    assert "CKV_AWS_62" in text  # política IAM "*" em "*"
    assert not any(line.startswith("/") for line in text.splitlines())


def test_trivy_finds_what_checkov_misses():
    text = summary("trivy")
    assert "k8s/rbac-cluster-admin.yaml" in text and "KSV-0111" in text  # cluster-admin
    assert "KSV-0109" in text  # senha num ConfigMap
    assert "[CRITICAL] AWS-0041" in text  # EKS aberto para 0.0.0.0/0
    assert "[LOW]" not in text  # só MEDIUM ou mais


def test_kube_linter_paths_are_relative_and_extra_rules_present():
    text = summary("kube-linter")
    assert "k8s/rbac-cluster-admin.yaml cluster-admin-role-binding" in text
    assert "k8s/banco-exposto.yaml exposed-services" in text
    assert "/home/runner" not in text


def test_kubeconform_reports_invalid_manifest():
    text = summary("kubeconform")
    assert text.startswith("k8s-invalido.yaml [INVALID] Deployment/invalido")
    assert "additional properties 'portas' not allowed" in text


def test_summary_without_findings(tmp_path):
    report = tmp_path / "kubeconform.json"
    report.write_text('{"resources": [], "summary": {"valid": 8}}')
    assert review.summarize_scan("kubeconform", report, tmp_path) == "nenhum achado"


def test_duplicate_lines_are_removed(tmp_path):
    report = tmp_path / "kube-linter.json"
    item = {"Check": "latest-tag", "Diagnostic": {"Message": "imagem latest"},
            "Object": {"Metadata": {"FilePath": str(tmp_path / "k8s/app.yaml")}}}
    report.write_text(review.json.dumps({"Reports": [item, item]}))
    assert review.summarize_scan("kube-linter", report, tmp_path) == "k8s/app.yaml latest-tag imagem latest"


@pytest.mark.parametrize("content", ["", "não é json", '{"Results": [{"Misconfigurations": [{"Status": "FAIL"}]}]}'])
def test_unreadable_report_raises(tmp_path, content):
    report = tmp_path / "trivy.json"
    report.write_text(content)
    with pytest.raises(ValueError):
        review.summarize_scan("trivy", report, tmp_path)


def test_prompt_has_one_tag_per_scanner():
    prompt = review.build_prompt("diff", "", {"trivy": "a", "kube-linter": "b"})
    assert "<scanners>\n<trivy>\na\n</trivy>\n<kube-linter>\nb\n</kube-linter>\n</scanners>" in prompt
    assert "<scanners>" in review.SYSTEM_PROMPT
    assert "<scanners>" not in review.build_prompt("diff", "")


def test_render_footer_lists_scanners():
    rev = review.Review(summary="ok", risk="baixo", findings=[])
    text = review.render(rev, "m", ["checkov", "kubeconform"], ["trivy"])
    assert "Scanners: checkov, kubeconform · ⚠️ não rodaram: trivy" in text
    assert "Scanners" not in review.render(rev, "m")


def test_scan_arg_validation():
    assert review.parse_scan_arg("trivy=t.json") == ("trivy", Path("t.json"))
    for bad in ("trivy", "tfsec=x.json", "trivy="):
        with pytest.raises(review.argparse.ArgumentTypeError):
            review.parse_scan_arg(bad)


def test_main_sends_scans_and_reports_failures(monkeypatch, tmp_path):
    prompts = []
    monkeypatch.setattr(review, "get_diff", lambda base: "+ resource {}")
    monkeypatch.setattr(review, "run_review", lambda model, prompt, *a: prompts.append(prompt)
                        or review.Review(summary="ok", risk="baixo", findings=[]))
    monkeypatch.chdir(tmp_path)
    broken = tmp_path / "kube-linter.json"
    broken.write_text("{")
    output = tmp_path / "review.md"
    monkeypatch.setattr(sys, "argv", [
        "review.py", "--base", "main", "--output", str(output),
        "--scan", f"trivy={FIXTURES / 'trivy.json'}", "--scan", f"kube-linter={broken}", "--scan-failed", "checkov",
    ])
    monkeypatch.setenv("MODEL_ID", "openai.gpt-oss-120b-1:0")
    review.main()
    assert "<trivy>" in prompts[0] and "KSV-0111" in prompts[0]
    assert "<kube-linter>" not in prompts[0]
    assert "Scanners: trivy · ⚠️ não rodaram: checkov, kube-linter" in output.read_text()


def test_main_counts_scans_in_size_limit(monkeypatch, tmp_path):
    monkeypatch.setattr(review, "get_diff", lambda base: "+ resource {}")
    monkeypatch.setattr(review, "run_review", lambda *a: pytest.fail("não deveria chamar o modelo"))
    monkeypatch.setenv("MAX_DIFF_CHARS", "100")
    output = tmp_path / "review.md"
    monkeypatch.setattr(sys, "argv", ["review.py", "--base", "main", "--output", str(output),
                                      "--scan", f"checkov={FIXTURES / 'checkov.json'}"])
    review.main()
    assert "acima do limite de 100" in output.read_text()
