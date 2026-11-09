"""GET /api/health — diz se a API está no ar, qual IA está ligada e como está a base do RAG.

O frontend usa isto para mostrar "Assistente conectado", "Modo de demonstração" ou
"base de conhecimento em construção". Formato em docs/CONTRATO-API.md.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/api/health")
def health(request: Request) -> dict:
    settings = request.app.state.settings
    index = request.app.state.index_store.load()
    return {
        "ok": True,
        "llm": {"provider": settings.llm.provider, "model": settings.llm.model},
        "rag": index.summary(),
    }
