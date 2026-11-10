"""Gera o índice do RAG a partir dos documentos em rag/documentos.

Uso (na raiz do projeto, com o ambiente virtual ativado):

    python -m scripts.ingest

Resultado: rag/indice/indice.json. Se a API estiver rodando, ela recarrega o índice sozinha.
O índice vai para o Git junto com os documentos (o Render não roda este script).
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import CHUNK_OVERLAP, CHUNK_SIZE, DOCUMENTS_DIR, INDEX_FILE
from app.rag.chunker import chunk_markdown
from app.rag.frontmatter import parse_frontmatter
from app.rag.store import INDEX_VERSION

VALID_CATEGORIES = {"educacao", "trabalho", "saude", "cidadania", "financas", "seguranca", "geral"}
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)


def is_document(path: Path) -> bool:
    """Só .md e .txt. Arquivos que começam com "_" (como o _MODELO.md) e o README são ignorados."""
    return (
        path.is_file()
        and path.suffix.lower() in {".md", ".txt"}
        and not path.name.startswith("_")
        and path.name.lower() != "readme.md"
    )


def build_index(
    documents_dir: Path,
    *,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
    now: datetime | None = None,
) -> tuple[dict[str, Any], list[str]]:
    """Lê os documentos e monta o índice. Devolve (índice, avisos)."""
    documents: list[dict[str, Any]] = []
    chunks: list[dict[str, Any]] = []
    warnings: list[str] = []

    files = sorted(path for path in documents_dir.iterdir() if is_document(path)) if documents_dir.exists() else []
    for path in files:
        meta, raw_body = parse_frontmatter(path.read_text(encoding="utf-8"))
        body = _HTML_COMMENT.sub("", raw_body).strip()  # comentários não vão para o índice
        doc_id = path.stem
        title = meta.get("titulo") or doc_id
        source = meta.get("fonte", "")
        category = meta.get("categoria", "")

        if not meta.get("titulo"):
            warnings.append(f'{path.name}: sem "titulo" no cabeçalho (usei o nome do arquivo).')
        if not source:
            warnings.append(f'{path.name}: sem "fonte". Todo documento precisa de uma fonte oficial.')
        if category and category not in VALID_CATEGORIES:
            warnings.append(f'{path.name}: categoria "{category}" fora da lista ({", ".join(sorted(VALID_CATEGORIES))}).')
        if not body:
            warnings.append(f"{path.name}: arquivo vazio, ignorado.")
            continue
        if meta.get("status", "").lower() == "rascunho":
            warnings.append(f"{path.name}: ainda é rascunho. Confira na fonte e troque para status: revisado.")

        pieces = chunk_markdown(body, size=chunk_size, overlap=chunk_overlap)
        documents.append(
            {
                "id": doc_id,
                "file": path.name,
                "title": title,
                "source": source,
                "category": category,
                "updated_at": meta.get("atualizado_em", ""),
                "status": meta.get("status", ""),
                "chunks": len(pieces),
            }
        )
        for number, piece in enumerate(pieces, start=1):
            chunks.append(
                {
                    "id": f"{doc_id}#{number}",
                    "doc_id": doc_id,
                    "title": title,
                    "heading": piece.heading,
                    "source": source,
                    "category": category,
                    "text": piece.text,
                }
            )

    created = (now or datetime.now(timezone.utc)).replace(microsecond=0)
    index = {
        "version": INDEX_VERSION,
        "created_at": created.isoformat().replace("+00:00", "Z"),
        "documents": documents,
        "chunks": chunks,
    }
    return index, warnings


def main() -> int:
    # O ingest não depende da configuração da IA: roda mesmo sem .env ou sem chave.
    index, warnings = build_index(DOCUMENTS_DIR)
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(json.dumps(index, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    for warning in warnings:
        print(f"Aviso: {warning}")
    if not index["documents"]:
        print("Nenhum documento encontrado em rag/documentos. O índice foi salvo vazio.")
        print("Veja docs/RAG.md para saber como escrever os documentos.")
        return 0
    print(
        f"Índice salvo em rag/indice/indice.json: {len(index['documents'])} documento(s), "
        f"{len(index['chunks'])} trecho(s), busca por palavras-chave."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
