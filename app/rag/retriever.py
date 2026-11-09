"""Encontra os trechos da base de conhecimento mais parecidos com a pergunta.

Hoje só existe a busca por palavras-chave (BM25). Se um dia entrarem embeddings (busca por
significado), o lugar de escolher entre um e outro é aqui, voltando para BM25 se falhar.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.rag.keyword import search_keyword
from app.rag.store import RETRIEVER_KEYWORD, LoadedIndex

MODE_NO_BASE = "sem-base"


@dataclass(frozen=True)
class SearchResult:
    chunk: dict[str, Any]
    score: float


@dataclass(frozen=True)
class Retrieval:
    mode: str  # "palavras-chave" | "sem-base" (no futuro: "embeddings")
    results: tuple[SearchResult, ...]

    @property
    def rag_ready(self) -> bool:
        return self.mode != MODE_NO_BASE


def retrieve(index: LoadedIndex, query: str, top_k: int = 4) -> Retrieval:
    if not index.ready:
        return Retrieval(MODE_NO_BASE, ())
    found = search_keyword(index.keyword, query, top_k)
    return Retrieval(
        RETRIEVER_KEYWORD,
        tuple(SearchResult(index.chunks[position], score) for position, score in found),
    )


def collect_sources(results: tuple[SearchResult, ...]) -> list[dict[str, Any]]:
    """Documentos de onde vieram os trechos, SEM repetir documento (vira "Fontes consultadas")."""
    sources: list[dict[str, Any]] = []
    seen: set[str] = set()
    for result in results:
        chunk = result.chunk
        doc_id = chunk.get("doc_id") or chunk.get("title") or ""
        if doc_id in seen:
            continue
        seen.add(doc_id)
        sources.append(
            {
                "title": chunk.get("title") or doc_id,
                "url": chunk.get("source") or None,
                "category": chunk.get("category") or None,
            }
        )
    return sources
