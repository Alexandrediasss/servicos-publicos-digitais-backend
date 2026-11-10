"""Encontra os trechos da base de conhecimento mais parecidos com a pergunta.

Hoje só existe a busca por palavras-chave (BM25). Se um dia entrarem embeddings (busca por
significado), o lugar de escolher entre um e outro é aqui, voltando para BM25 se falhar.

A nota BM25 sozinha não basta, então a escolha final segue três regras (docs/RAG.md):
1. Documento citado pelo nome na pergunta ("ENEM", "Pé-de-Meia", "título") entra primeiro, com o seu
   melhor trecho. Assim, uma pergunta sobre três serviços traz os três.
2. No máximo MAX_CHUNKS_PER_DOC trechos do mesmo documento, para sobrar espaço para outros.
3. Trechos com nota menor que MIN_SCORE_RATIO da melhor nota são descartados: eles viravam "Fontes
   consultadas" sem relação com a pergunta e gastavam tokens à toa.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.rag.keyword import search_keyword, tokenize
from app.rag.store import RETRIEVER_KEYWORD, LoadedIndex

MODE_NO_BASE = "sem-base"
MAX_CHUNKS_PER_DOC = 2
# Calibrado com as perguntas de teste de tests/test_rag_base.py: 0,4 tira o ENEM da pergunta sobre
# CPF cancelado (nota 36% da melhor) e mantém a UBS na pergunta sobre vacinas (53%).
MIN_SCORE_RATIO = 0.4


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


def retrieve(
    index: LoadedIndex,
    query: str,
    top_k: int = 4,
    *,
    max_per_doc: int = MAX_CHUNKS_PER_DOC,
    min_score_ratio: float = MIN_SCORE_RATIO,
) -> Retrieval:
    if not index.ready:
        return Retrieval(MODE_NO_BASE, ())

    candidates = search_keyword(index.keyword, query, top_k=len(index.chunks))
    if not candidates:
        return Retrieval(RETRIEVER_KEYWORD, ())

    terms = set(tokenize(query))
    named = {doc_id for doc_id, names in index.doc_names.items() if any(name <= terms for name in names)}
    min_score = candidates[0][1] * min_score_ratio

    picked: list[tuple[int, float]] = []
    per_doc: dict[str, int] = {}

    def take(position: int, score: float) -> None:
        doc_id = index.chunks[position].get("doc_id", "")
        if len(picked) < top_k and per_doc.get(doc_id, 0) < max_per_doc and (position, score) not in picked:
            picked.append((position, score))
            per_doc[doc_id] = per_doc.get(doc_id, 0) + 1

    # 1) O melhor trecho de cada documento citado pelo nome (mesmo com nota baixa).
    for position, score in candidates:
        if index.chunks[position].get("doc_id") in named and not per_doc.get(index.chunks[position].get("doc_id"), 0):
            take(position, score)
    # 2) O resto por nota, respeitando o limite por documento e o corte relativo.
    for position, score in candidates:
        if score >= min_score:
            take(position, score)

    picked.sort(key=lambda item: item[1], reverse=True)
    return Retrieval(
        RETRIEVER_KEYWORD,
        tuple(SearchResult(index.chunks[position], score) for position, score in picked),
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
