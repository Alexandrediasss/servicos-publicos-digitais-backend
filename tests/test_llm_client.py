"""Cliente da IA, com o provedor simulado (sem internet e sem Ollama)."""

import asyncio
import dataclasses
import json

import httpx
import pytest

from app.config import load_settings
from app.llm.client import LlmError, mock_stream, parse_stream_line, stream_chat

LLM = load_settings({"LLM_PROVIDER": "ollama"}).llm


def collect(llm, transport, messages=None):
    async def run():
        return [piece async for piece in stream_chat(messages or [{"role": "user", "content": "oi"}], llm, transport=transport)]

    return asyncio.run(run())


def openai_stream(*pieces: str) -> str:
    lines = [f"data: {json.dumps({'choices': [{'delta': {'content': p}}]})}" for p in pieces]
    return "\n\n".join([*lines, "data: [DONE]"]) + "\n\n"


def test_le_o_streaming_no_formato_openai():
    sent = {}

    def handler(request: httpx.Request) -> httpx.Response:
        sent["url"] = str(request.url)
        sent["body"] = json.loads(request.content)
        sent["auth"] = request.headers.get("authorization")
        return httpx.Response(200, text=openai_stream("Olá", ", tudo ", "bem?"))

    pieces = collect(LLM, httpx.MockTransport(handler))
    assert pieces == ["Olá", ", tudo ", "bem?"]
    assert sent["url"] == "http://localhost:11434/v1/chat/completions"
    assert sent["body"]["stream"] is True
    assert sent["body"]["model"] == "llama3.1:8b"
    assert sent["body"]["temperature"] == 0.2
    assert sent["body"]["max_tokens"] == 700
    assert sent["auth"] is None  # Ollama local não usa chave


def test_envia_a_chave_quando_existe():
    llm = dataclasses.replace(LLM, api_key="chave-de-teste")
    seen = {}

    def handler(request):
        seen["auth"] = request.headers.get("authorization")
        return httpx.Response(200, text=openai_stream("ok"))

    collect(llm, httpx.MockTransport(handler))
    assert seen["auth"] == "Bearer chave-de-teste"


def test_erro_http_do_provedor_vira_llm_error():
    transport = httpx.MockTransport(lambda request: httpx.Response(404, json={"error": "model not found"}))
    with pytest.raises(LlmError) as caught:
        collect(LLM, transport)
    assert caught.value.status == 404
    assert "model not found" in caught.value.detail


def test_provedor_fora_do_ar_vira_llm_error():
    def handler(request):
        raise httpx.ConnectError("Connection refused")

    with pytest.raises(LlmError) as caught:
        collect(LLM, httpx.MockTransport(handler))
    assert caught.value.status == 502


def test_demora_demais_vira_llm_error():
    def handler(request):
        raise httpx.ReadTimeout("timeout")

    with pytest.raises(LlmError) as caught:
        collect(LLM, httpx.MockTransport(handler))
    assert caught.value.status == 504


def test_erro_no_meio_do_streaming():
    body = openai_stream("Começo")[: -len("data: [DONE]\n\n")] + 'data: {"error": {"message": "rate limit"}}\n\n'
    with pytest.raises(LlmError):
        collect(LLM, httpx.MockTransport(lambda request: httpx.Response(200, text=body)))


def test_parse_stream_line_ignora_linhas_sem_texto():
    assert parse_stream_line("") is None
    assert parse_stream_line(": comentário") is None
    assert parse_stream_line("data: {incompleto") is None
    assert parse_stream_line('data: {"choices": [{"delta": {"role": "assistant"}}]}') is None
    assert parse_stream_line('data: {"choices": []}') is None


def test_mock_mostra_pergunta_e_trechos():
    messages = [
        {"role": "system", "content": "regras\n\nCONTEXTO:\n[1] ENEM (Isenção) — fonte: x\ntexto\n\n[2] ENEM — fonte: y\nt"},
        {"role": "user", "content": "Como faço o ENEM?"},
    ]

    async def run():
        return "".join([piece async for piece in mock_stream(messages, delay=0)])

    text = asyncio.run(run())
    assert text.startswith("**Modo de demonstração:** nenhum modelo de IA está conectado agora.")
    assert 'Você perguntou: "Como faço o ENEM?"' in text
    assert "Trechos encontrados na base de conhecimento: ENEM (Isenção); ENEM." in text


def test_mock_sem_trechos():
    async def run():
        return "".join([p async for p in mock_stream([{"role": "user", "content": "oi"}], delay=0)])

    assert "A base de conhecimento ainda não tem documentos sobre isso." in asyncio.run(run())
