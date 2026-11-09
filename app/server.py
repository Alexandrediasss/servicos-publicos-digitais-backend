"""Monta a aplicação FastAPI: CORS, rotas e respostas de erro em português.

`create_app()` recebe a configuração pronta, o que deixa os testes criarem uma API com
configurações diferentes sem mexer no `.env`. Quem sobe o servidor usa `app/main.py`.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import Settings
from app.rag.store import IndexStore
from app.routes import chat, health
from app.utils.rate_limit import RateLimiter

logger = logging.getLogger("guia")

ERROR_NOT_FOUND = "Rota não encontrada."
ERROR_INTERNAL = "Algo deu errado no servidor. Tente de novo em alguns minutos."


def configure_logging() -> None:
    """Log simples no terminal. Só avisos e erros, mais o resumo de quando a API liga."""
    if logger.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s [%(name)s] %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


def create_app(settings: Settings, *, llm_transport: Any = None) -> FastAPI:
    """`llm_transport` existe só para os testes simularem o provedor de IA."""
    app = FastAPI(
        title="Guia do Cidadão Digital — API do assistente",
        # Sem páginas de documentação automática: a API só serve o site.
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.state.settings = settings
    app.state.index_store = IndexStore(settings.index_file)
    app.state.rate_limiter = RateLimiter(settings.rate_limit_per_minute)
    app.state.llm_transport = llm_transport

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    app.include_router(health.router)
    app.include_router(chat.router)

    @app.exception_handler(StarletteHTTPException)
    async def http_error(_request: Request, error: StarletteHTTPException) -> JSONResponse:
        message = ERROR_NOT_FOUND if error.status_code in (404, 405) else ERROR_INTERNAL
        return JSONResponse({"error": message}, status_code=error.status_code)

    @app.exception_handler(Exception)
    async def unexpected_error(_request: Request, error: Exception) -> JSONResponse:
        logger.error("Erro inesperado: %s", type(error).__name__)
        return JSONResponse({"error": ERROR_INTERNAL}, status_code=500)

    return app


def log_startup(settings: Settings, index_store: IndexStore) -> None:
    index = index_store.load()
    logger.info("API do Guia do Cidadão Digital pronta.")
    logger.info("  IA: %s (%s)", settings.llm.provider, settings.llm.model)
    if index.ready:
        logger.info("  RAG: %d documento(s), %d trecho(s)", len(index.documents), len(index.chunks))
    else:
        logger.info('  RAG: base vazia. Escreva documentos em rag/documentos e rode "python -m scripts.ingest".')
    if settings.llm.provider == "mock":
        logger.info("  Modo de demonstração: as respostas não usam IA. Veja o README.")
