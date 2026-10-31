"""Testes sem acesso à AWS: um servidor HTTP local faz o papel do Bedrock."""

import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest
from anthropic import AnthropicBedrockMantle, BetaRefusalFallbackMiddleware

sys.path.insert(0, str(Path(__file__).parent.parent / "reviewer"))
import review  # noqa: E402

REVIEW_JSON = {
    "summary": "O Security Group libera SSH para a internet.",
    "risk": "alto",
    "findings": [
        {
            "file": "examples/terraform/main.tf",
            "severity": "alta",
            "title": "SSH aberto para 0.0.0.0/0",
            "explanation": "Qualquer IP da internet pode tentar acessar a porta 22.",
            "suggestion": "Restrinja o cidr_blocks ou use o Session Manager.",
        }
    ],
}


def message(model: str, stop_reason: str, text: str) -> dict:
    content = [{"type": "text", "text": text}] if text else []
    return {
        "id": "msg_test",
        "type": "message",
        "role": "assistant",
        "model": model,
        "content": content,
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "stop_details": {"type": "refusal", "category": None, "explanation": None} if stop_reason == "refusal" else None,
        "usage": {"input_tokens": 10, "output_tokens": 10},
    }


@pytest.fixture
def fake_bedrock():
    """Responde com recusa para os modelos em `refuse` e com a revisão para os demais."""
    state = {"requests": [], "refuse": set()}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            state["requests"].append(body)
            if body["model"] in state["refuse"]:
                data = message(body["model"], "refusal", "")
            else:
                data = message(body["model"], "end_turn", json.dumps(REVIEW_JSON))
            payload = json.dumps(data).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    client = AnthropicBedrockMantle(
        aws_region="us-east-1",
        base_url=f"http://127.0.0.1:{server.server_port}",
        skip_auth=True,
        max_retries=0,
        middleware=[BetaRefusalFallbackMiddleware([{"model": review.DEFAULT_FALLBACK_MODEL}])],
    )
    yield client, state
    server.shutdown()


def test_review_is_parsed(fake_bedrock):
    client, state = fake_bedrock
    result = review.ask_claude(client, review.DEFAULT_MODEL, review.build_prompt("diff", ""))

    assert isinstance(result, review.Review)
    assert result.risk == "alto"
    request = state["requests"][0]
    assert request["model"] == review.DEFAULT_MODEL
    assert request["output_config"]["effort"] == "medium"
    assert request["output_config"]["format"]["type"] == "json_schema"


def test_refusal_falls_back_to_other_model(fake_bedrock):
    client, state = fake_bedrock
    state["refuse"].add(review.DEFAULT_MODEL)
    result = review.ask_claude(client, review.DEFAULT_MODEL, review.build_prompt("diff", ""))

    assert isinstance(result, review.Review)
    assert [r["model"] for r in state["requests"]] == [review.DEFAULT_MODEL, review.DEFAULT_FALLBACK_MODEL]


def test_refusal_on_every_model(fake_bedrock):
    client, state = fake_bedrock
    state["refuse"].update({review.DEFAULT_MODEL, review.DEFAULT_FALLBACK_MODEL})
    result = review.ask_claude(client, review.DEFAULT_MODEL, review.build_prompt("diff", ""))

    assert result == "O modelo recusou a revisão deste Pull Request."


def test_prompt_wraps_untrusted_content():
    prompt = review.build_prompt("+ resource {}", "Check: CKV_AWS_24")
    assert "<diff>\n+ resource {}\n</diff>" in prompt
    assert "<checkov>\nCheck: CKV_AWS_24\n</checkov>" in prompt
    assert "<checkov>" not in review.build_prompt("+ resource {}", "")


def test_render():
    text = review.render(review.Review.model_validate(REVIEW_JSON), "anthropic.claude-opus-5-5")
    assert "🔴 alto" in text
    assert "### 🔴 SSH aberto para 0.0.0.0/0" in text
    assert "`examples/terraform/main.tf`" in text
    assert "⚠️ algo deu errado" in review.render("algo deu errado", "m")
