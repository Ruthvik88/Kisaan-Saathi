"""Deploy-readiness tests: CORS origins + /ask rate limiting (no API calls)."""

import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

import context as ctx
import llm
import main as app_module
import stt
import tts
from llm import LlmResult
from stt import TranscriptionResult


def _install_mocks(monkeypatch):
    """Replace all external calls (STT/LLM/TTS/weather) with fakes."""
    monkeypatch.setattr(
        stt,
        "transcribe",
        lambda audio_bytes, lang="hi": TranscriptionResult(
            text="आज मौसम कैसा रहेगा?",
            metrics_available=False,
        ),
    )
    monkeypatch.setattr(
        llm,
        "ask",
        lambda question, lang, context_block, history=None, best_effort=False: LlmResult(
            intent="in_domain", reply="आज मौसम साफ रहेगा।"
        ),
    )
    monkeypatch.setattr(
        tts, "synthesize", lambda text, lang="hi": io.BytesIO(b"fake-audio-bytes")
    )
    monkeypatch.setattr(
        ctx, "build_context_string", lambda: "WEATHER: test\n\nMSP: test"
    )


def _ask(client):
    return client.post(
        "/ask",
        files={"audio": ("q.webm", b"fake-audio", "audio/webm")},
        data={"lang": "hi"},
    )


def test_cors_preflight_allowed_origin(monkeypatch):
    _install_mocks(monkeypatch)
    client = TestClient(app_module.app)
    allowed = app_module.ALLOWED_ORIGINS[0]
    resp = client.options(
        "/ask",
        headers={
            "Origin": allowed,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert resp.headers.get("access-control-allow-origin") == allowed


def test_cors_preflight_disallowed_origin(monkeypatch):
    _install_mocks(monkeypatch)
    client = TestClient(app_module.app)
    resp = client.options(
        "/ask",
        headers={
            "Origin": "http://evil.example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert "access-control-allow-origin" not in resp.headers


def test_ask_rate_limited_after_burst(monkeypatch):
    _install_mocks(monkeypatch)
    client = TestClient(app_module.app)
    limit_spec = os.getenv("RATE_LIMIT_ASK", "10/minute")
    limit_count = int(limit_spec.split("/")[0])
    codes = []
    for _ in range(limit_count + 1):
        resp = _ask(client)
        codes.append(resp.status_code)
    assert codes[:limit_count] == [200] * limit_count
    assert codes[limit_count] == 429
    assert resp.json()["detail"] == (
        "Too many requests. Please wait a minute and try again."
    )


def test_health_not_rate_limited(monkeypatch):
    _install_mocks(monkeypatch)
    client = TestClient(app_module.app)
    for _ in range(15):
        resp = client.get("/health")
        assert resp.status_code == 200
