"""Carrega o índice gerado por `python -m scripts.ingest` (rag/indice/indice.json).

O arquivo é relido sozinho quando muda (a data de modificação é conferida a cada pedido), então
rodar o ingest com a API ligada já atualiza a base, sem reiniciar.
"""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.rag.keyword import KeywordIndex, build_keyword_index

INDEX_VERSION = 1
RETRIEVER_KEYWORD = "palavras-chave"

logger = logging.getLogger("guia.rag")


@dataclass(frozen=True)
class LoadedIndex:
    created_at: str | None = None
    documents: tuple[dict[str, Any], ...] = ()
    chunks: tuple[dict[str, Any], ...] = ()
    keyword: KeywordIndex = field(default_factory=lambda: build_keyword_index([]))

    @property
    def ready(self) -> bool:
        return bool(self.chunks)

    def summary(self) -> dict[str, Any]:
        """O bloco "rag" do GET /api/health."""
        return {
            "ready": self.ready,
            "documents": len(self.documents),
            "chunks": len(self.chunks),
            "createdAt": self.created_at,
            "retriever": RETRIEVER_KEYWORD,
        }


def prepare_index(raw: dict[str, Any]) -> LoadedIndex:
    chunks = tuple(chunk for chunk in raw.get("chunks") or [] if isinstance(chunk, dict))
    documents = tuple(doc for doc in raw.get("documents") or [] if isinstance(doc, dict))
    return LoadedIndex(
        created_at=raw.get("created_at"),
        documents=documents,
        chunks=chunks,
        keyword=build_keyword_index(chunks),
    )


EMPTY_INDEX = LoadedIndex()


class IndexStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.Lock()
        self._mtime: int | None = None
        self._index = EMPTY_INDEX

    def load(self) -> LoadedIndex:
        try:
            mtime = self.path.stat().st_mtime_ns
        except FileNotFoundError:
            mtime = -1

        if mtime == self._mtime:
            return self._index

        with self._lock:
            if mtime == self._mtime:
                return self._index
            if mtime == -1:
                self._index = EMPTY_INDEX
            else:
                try:
                    self._index = prepare_index(json.loads(self.path.read_text(encoding="utf-8")))
                except (OSError, ValueError) as error:
                    logger.error("Não consegui ler o índice do RAG (%s): %s", self.path, error)
                    self._index = EMPTY_INDEX
            self._mtime = mtime
            return self._index
