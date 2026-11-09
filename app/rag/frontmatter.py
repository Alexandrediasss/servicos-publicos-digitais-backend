"""Lê o cabeçalho simples (frontmatter) dos documentos do RAG.

    ---
    titulo: ENEM — inscrição e resultados
    fonte: https://www.gov.br/inep/...
    categoria: educacao
    atualizado_em: 2026-11-08
    ---
    texto do documento...

É de propósito um leitor simples (uma linha "chave: valor" por campo), sem depender de YAML.
"""

from __future__ import annotations

import re

_FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n?", re.DOTALL)


def parse_frontmatter(raw: str) -> tuple[dict[str, str], str]:
    """Separa o cabeçalho do texto. Devolve (campos, corpo)."""
    text = str(raw).removeprefix("﻿").replace("\r\n", "\n")
    match = _FRONTMATTER.match(text)
    if not match:
        return {}, text.strip()

    meta: dict[str, str] = {}
    for line in match.group(1).split("\n"):
        key, separator, value = line.partition(":")
        key = key.strip().lower()
        if not separator or not key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        meta[key] = value
    return meta, text[match.end() :].strip()
