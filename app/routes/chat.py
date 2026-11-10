"""POST /api/chat — recebe a conversa e devolve a resposta aos pedaços (Server-Sent Events).

Fluxo: limite de uso -> tamanho do corpo -> validação -> mascaramento -> RAG -> prompt -> IA.

Eventos enviados ao frontend, nesta ordem (docs/CONTRATO-API.md):
    meta  -> {sources, retrieval, ragReady, masked}   uma vez, antes do texto
    token -> {text}                                    várias vezes
    done  -> {}                                        fim normal
    error -> {message}                                 fim com erro

PRIVACIDADE: nunca registre no log o conteúdo das mensagens. Nem em caso de erro.
"""

from __future__ import annotations

import json
import logging
import traceback
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from app.config import LlmSettings
from app.llm.client import LlmError, stream_chat
from app.prompts.system import build_messages
from app.rag.retriever import collect_sources, retrieve
from app.utils.privacy import mask_sensitive
from app.utils.rate_limit import RATE_LIMIT_MESSAGE, client_ip
from app.utils.sse import SSE_HEADERS, SSE_MEDIA_TYPE, format_event
from app.utils.validation import ERROR_MISSING, ValidationError, validate_messages

router = APIRouter()
logger = logging.getLogger("guia.chat")

ERROR_BODY_TOO_LARGE = "Sua mensagem ficou grande demais. Tente resumir."
ERROR_LLM_UNAVAILABLE = "O assistente está indisponível agora. Tente de novo em alguns minutos."
# Limite do plano gratuito do provedor (HTTP 429): muita gente perguntando ao mesmo tempo.
ERROR_LLM_BUSY = "Muita gente perguntando agora. Espere um minuto e tente de novo."
ERROR_GENERIC = "Algo deu errado ao gerar a resposta."


class BodyTooLarge(Exception):
    pass


async def read_body_limited(request: Request, limit: int) -> bytes:
    """Lê o corpo do pedido, desistindo assim que passar de `limit` bytes."""
    declared = request.headers.get("content-length", "")
    if declared.isdigit() and int(declared) > limit:
        raise BodyTooLarge
    body = bytearray()
    async for part in request.stream():
        body.extend(part)
        if len(body) > limit:
            raise BodyTooLarge
    return bytes(body)


def error_response(status: int, message: str) -> JSONResponse:
    return JSONResponse({"error": message}, status_code=status)


@router.post("/api/chat")
async def chat(request: Request):
    app_state = request.app.state
    settings = app_state.settings

    if not app_state.rate_limiter.hit(client_ip(request, settings.trust_proxy)):
        return error_response(429, RATE_LIMIT_MESSAGE)

    try:
        raw = await read_body_limited(request, settings.max_body_bytes)
    except BodyTooLarge:
        return error_response(413, ERROR_BODY_TOO_LARGE)

    try:
        body: Any = json.loads(raw)
    except ValueError:
        return error_response(400, ERROR_MISSING)

    try:
        messages = validate_messages(
            body,
            max_messages=settings.max_messages,
            max_chars=settings.max_message_chars,
            max_history=settings.max_history_messages,
        )
    except ValidationError as error:
        return error_response(400, error.message)

    # O frontend já mascara, mas o backend não confia nisso: mascara de novo.
    history: list[dict[str, str]] = []
    masked: list[str] = []
    for message in messages:
        text, found = mask_sensitive(message["content"])
        history.append({"role": message["role"], "content": text})
        masked.extend(kind for kind in found if kind not in masked)

    retrieval = retrieve(app_state.index_store.load(), history[-1]["content"], settings.top_k)
    meta = {
        "sources": collect_sources(retrieval.results),
        "retrieval": retrieval.mode,
        "ragReady": retrieval.rag_ready,
        "masked": masked,
    }
    llm_messages = build_messages(history, retrieval.results)

    return StreamingResponse(
        event_stream(meta, llm_messages, settings.llm, app_state.llm_transport),
        media_type=SSE_MEDIA_TYPE,
        headers=SSE_HEADERS,
    )


async def event_stream(
    meta: dict[str, Any],
    llm_messages: list[dict[str, str]],
    llm: LlmSettings,
    transport: Any = None,
) -> AsyncIterator[str]:
    """Gera os eventos SSE.

    Se o aluno fechar a página ou clicar em "Parar", a conexão cai e o servidor cancela este
    gerador; ao sair do `async with` do cliente HTTP, o pedido ao provedor de IA é fechado também.
    """
    yield format_event("meta", meta)
    try:
        async for text in stream_chat(llm_messages, llm, transport=transport):
            yield format_event("token", {"text": text})
        yield format_event("done", {})
    except LlmError as error:
        # Só detalhes técnicos no log (status e resposta do provedor), nunca a pergunta.
        logger.error("Falha no provedor de IA (%s): %s %s", llm.provider, error, error.detail)
        message = ERROR_LLM_BUSY if error.status == 429 else ERROR_LLM_UNAVAILABLE
        yield format_event("error", {"message": message})
    except Exception as error:  # noqa: BLE001 - qualquer outro erro vira mensagem genérica
        # Registra o tipo do erro e onde aconteceu, mas não a mensagem (ela poderia citar o texto).
        frame = traceback.extract_tb(error.__traceback__)[-1] if error.__traceback__ else None
        where = f"{frame.filename}:{frame.lineno}" if frame else "?"
        logger.error("Erro ao gerar a resposta: %s em %s", type(error).__name__, where)
        yield format_event("error", {"message": ERROR_GENERIC})
