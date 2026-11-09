"""Divide um documento Markdown em trechos ("chunks") de tamanho parecido.

Regras:
- Um título (#, ##, ...) sempre começa um trecho novo; o trecho guarda o título da seção.
- Cada trecho tem no máximo ~`size` caracteres. Parágrafos maiores são cortados por frases.
- Se o último parágrafo de um trecho for curto (até `overlap` caracteres), ele é repetido no começo
  do trecho seguinte da mesma seção. Isso evita perder contexto no corte.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_BLANK_LINE = re.compile(r"\n\s*\n")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
_HEADING = re.compile(r"^#{1,6}\s+(.+)$")


@dataclass(frozen=True)
class TextChunk:
    heading: str
    text: str


def _split_long_block(block: str, size: int) -> list[str]:
    if len(block) <= size:
        return [block]
    parts: list[str] = []
    current = ""
    for sentence in _SENTENCE_END.split(block):
        if len(sentence) > size:
            if current:
                parts.append(current)
            current = ""
            parts.extend(sentence[i : i + size] for i in range(0, len(sentence), size))
            continue
        if current and len(current) + len(sentence) + 1 > size:
            parts.append(current)
            current = ""
        current = f"{current} {sentence}" if current else sentence
    if current:
        parts.append(current)
    return parts


def chunk_markdown(markdown: str, *, size: int = 900, overlap: int = 200) -> list[TextChunk]:
    blocks = [
        block.strip()
        for block in _BLANK_LINE.split(str(markdown).replace("\r\n", "\n"))
        if block.strip()
    ]

    chunks: list[TextChunk] = []
    heading = ""
    parts: list[str] = []
    length = 0

    def flush(keep_overlap: bool) -> None:
        nonlocal parts, length
        if parts:
            chunks.append(TextChunk(heading=heading, text="\n\n".join(parts)))
        last = parts[-1] if parts else ""
        parts = [last] if keep_overlap and last and len(last) <= overlap else []
        length = sum(len(part) + 2 for part in parts)

    for block in blocks:
        lines = block.split("\n")
        match = _HEADING.match(lines[0])
        if match:
            flush(False)
            heading = match.group(1).strip()
            block = "\n".join(lines[1:]).strip()
            if not block:
                continue
        for piece in _split_long_block(block, size):
            if length and length + len(piece) > size:
                flush(True)
            parts.append(piece)
            length += len(piece) + 2
    flush(False)
    return chunks
