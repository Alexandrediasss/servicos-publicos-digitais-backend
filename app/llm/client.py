"""Cliente de chat no formato da API da OpenAI (/chat/completions com stream=true).

Funciona com o Ollama e com qualquer provedor compatível (provedor "custom"). O provedor "mock"
devolve um texto de demonstração, para testar o site sem nenhuma IA ligada.
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from collections.abc import AsyncIterator

import httpx

from app.config import LlmSettings


class LlmError(Exception):
    """O provedor de IA falhou, demorou demais ou recusou o pedido.

    `detail` tem a parte técnica: vai só para o log do servidor, nunca para o aluno.
    """

    def __init__(self, message: str, *, status: int | None = None, detail: str = "") -> None:
        super().__init__(message)
        self.status = status
        self.detail = detail


async def stream_chat(
    messages: list[dict[str, str]],
    llm: LlmSettings,
    *,
    transport: httpx.AsyncBaseTransport | None = None,
) -> AsyncIterator[str]:
    """Envia as mensagens ao modelo e devolve o texto aos pedaços, conforme ele escreve.

    `transport` existe só para os testes simularem o provedor.
    """
    if llm.provider == "mock":
        async for piece in mock_stream(messages, llm.mock_delay_seconds):
            yield piece
        return

    headers = {"Content-Type": "application/json"}
    if llm.api_key:
        headers["Authorization"] = f"Bearer {llm.api_key}"
    payload = {
        "model": llm.model,
        "messages": messages,
        "stream": True,
        "temperature": llm.temperature,
        "max_tokens": llm.max_tokens,
    }
    # O timeout do httpx vale para cada etapa (conectar, esperar cada pedaço); o `deadline` limita
    # o tempo total da resposta.
    deadline = time.monotonic() + llm.timeout_seconds
    url = f"{llm.base_url}/chat/completions"

    try:
        async with httpx.AsyncClient(timeout=llm.timeout_seconds, transport=transport) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                if response.status_code != 200:
                    detail = (await response.aread()).decode("utf-8", "replace")[:500]
                    raise LlmError(
                        f"O provedor de IA respondeu com erro {response.status_code}.",
                        status=response.status_code,
                        detail=detail,
                    )
                async for line in response.aiter_lines():
                    if time.monotonic() > deadline:
                        raise LlmError("O modelo demorou demais para responder.", status=504)
                    text = parse_stream_line(line)
                    if text is _DONE:
                        return
                    if text:
                        yield text
    except httpx.TimeoutException as error:
        raise LlmError("O modelo demorou demais para responder.", status=504, detail=repr(error)) from error
    except httpx.HTTPError as error:
        raise LlmError(
            f"Não foi possível conectar ao provedor de IA em {llm.base_url}.",
            status=502,
            detail=repr(error),
        ) from error


_DONE = object()


def parse_stream_line(line: str) -> str | object | None:
    """Lê uma linha do streaming do provedor.

    Devolve o pedaço de texto, `_DONE` no fim, ou None para linhas sem texto (comentários, vazias,
    JSON incompleto). Erro enviado pelo provedor no meio do caminho vira LlmError.
    """
    line = line.strip()
    if not line.startswith("data:"):
        return None
    data = line[5:].strip()
    if data == "[DONE]":
        return _DONE
    try:
        parsed = json.loads(data)
    except ValueError:
        return None
    if not isinstance(parsed, dict):
        return None
    if parsed.get("error"):
        raise LlmError("O provedor de IA interrompeu a resposta.", detail=json.dumps(parsed["error"])[:500])
    choices = parsed.get("choices") or [{}]
    delta = (choices[0] or {}).get("delta") or {}
    content = delta.get("content")
    return content if isinstance(content, str) and content else None


_SOURCE_TITLE = re.compile(r"^\[\d+\] (.+?) — fonte:", re.MULTILINE)


async def mock_stream(messages: list[dict[str, str]], delay: float = 0.015) -> AsyncIterator[str]:
    """Resposta de demonstração, em Markdown, entregue palavra por palavra."""
    question = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
    system = next((m["content"] for m in messages if m["role"] == "system"), "")
    titles = list(dict.fromkeys(_SOURCE_TITLE.findall(system)))

    found = (
        f"Trechos encontrados na base de conhecimento: {'; '.join(titles)}."
        if titles
        else "A base de conhecimento ainda não tem documentos sobre isso."
    )
    text = "\n".join(
        [
            "**Modo de demonstração:** nenhum modelo de IA está conectado agora.",
            "",
            f'Você perguntou: "{question[:160]}"',
            "",
            found,
            "",
            "Para respostas de verdade, coloque `LLM_PROVIDER=groq` (com a chave) ou `LLM_PROVIDER=ollama` "
            "no arquivo `.env` da API (veja o README).",
        ]
    )
    for piece in re.split(r"(\s+)", text):
        if not piece:
            continue
        if delay:
            await asyncio.sleep(delay)
        yield piece
