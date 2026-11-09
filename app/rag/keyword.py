"""Busca por palavras-chave (BM25). É o modo padrão do RAG.

Não precisa de nenhum modelo extra e funciona bem para uma base pequena (dezenas de documentos).
BM25 dá nota maior para um trecho quando ele tem as palavras da pergunta, principalmente as
palavras raras na base (ex.: "enem" vale mais que "servico").
"""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass

# Palavras vazias do português (já sem acento): aparecem em quase toda frase e não ajudam a achar
# o documento certo.
STOPWORDS = frozenset(
    """
    a o e de da do das dos em no na nos nas um uma uns umas para pra pro por com sem que se ao aos as
    os ou como mais mas eu meu minha meus minhas voce seu sua seus suas ele ela eles elas isso isto
    este esta esse essa ter tem tenho qual quais quando onde ja nao sim me te lhe vos foi ser sou
    estou muito pouco bem so sobre ate entre depois antes tambem quero queria preciso fazer faco
    posso pode
    """.split()
)

_COMBINING_MARKS = re.compile(r"[̀-ͯ]")
_NON_WORD = re.compile(r"[^a-z0-9]+")
_PLURAL_ES = re.compile(r"(res|zes|les)$")


def normalize(text: str) -> str:
    """Minúsculas e sem acentos: "Inscrição" -> "inscricao"."""
    return _COMBINING_MARKS.sub("", unicodedata.normalize("NFD", str(text).lower()))


def stem(token: str) -> str:
    """"Stemming" bem simples: tira plural e algumas terminações comuns."""
    if len(token) > 5 and token.endswith("oes"):
        return f"{token[:-3]}ao"  # inscricoes -> inscricao
    if len(token) > 4 and _PLURAL_ES.search(token):
        return token[:-2]  # mulheres -> mulher
    if len(token) > 3 and token.endswith("s"):
        return token[:-1]  # vacinas -> vacina
    return token


def tokenize(text: str) -> list[str]:
    return [
        stem(token)
        for token in _NON_WORD.split(normalize(text))
        if len(token) > 1 and token not in STOPWORDS
    ]


@dataclass(frozen=True)
class KeywordIndex:
    term_frequencies: tuple[Counter[str], ...]
    lengths: tuple[int, ...]
    document_frequency: Counter[str]
    average_length: float

    @property
    def size(self) -> int:
        return len(self.lengths)


def build_keyword_index(chunks: Iterable[dict]) -> KeywordIndex:
    """Cada item precisa de "text"; "title" e "heading" são opcionais."""
    frequencies: list[Counter[str]] = []
    lengths: list[int] = []
    for chunk in chunks:
        title = chunk.get("title") or ""
        # O título conta duas vezes: ajuda a achar o documento certo.
        tokens = tokenize(f"{title} {title} {chunk.get('heading') or ''} {chunk.get('text') or ''}")
        frequencies.append(Counter(tokens))
        lengths.append(len(tokens))

    document_frequency: Counter[str] = Counter()
    for counter in frequencies:
        document_frequency.update(counter.keys())

    average = sum(lengths) / len(lengths) if lengths else 0.0
    return KeywordIndex(tuple(frequencies), tuple(lengths), document_frequency, average)


def search_keyword(
    index: KeywordIndex,
    query: str,
    top_k: int = 4,
    *,
    k1: float = 1.4,
    b: float = 0.75,
) -> list[tuple[int, float]]:
    """Devolve (posição do trecho, nota), do mais relevante ao menos. Sem resultado -> lista vazia."""
    terms = list(dict.fromkeys(tokenize(query)))  # sem repetir, mantendo a ordem
    if not terms or not index.size:
        return []

    average = index.average_length or 1.0
    results: list[tuple[int, float]] = []
    for position, (frequencies, length) in enumerate(zip(index.term_frequencies, index.lengths)):
        score = 0.0
        for term in terms:
            frequency = frequencies.get(term, 0)
            if not frequency:
                continue
            df = index.document_frequency.get(term, 0)
            idf = math.log(1 + (index.size - df + 0.5) / (df + 0.5))
            score += (idf * frequency * (k1 + 1)) / (frequency + k1 * (1 - b + b * length / average))
        if score > 0:
            results.append((position, score))

    results.sort(key=lambda item: item[1], reverse=True)
    return results[:top_k]
