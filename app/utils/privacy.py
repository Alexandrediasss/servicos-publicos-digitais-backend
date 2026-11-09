"""Mascara dados pessoais antes de qualquer texto sair do servidor para o provedor de IA.

O frontend faz a mesma coisa (frontend/src/lib/privacy.js no repositório do site), mas o backend
não pode confiar nisso. Mantenha as regras IGUAIS às do frontend.

Por que `re.ASCII`: no JavaScript, `\\d`, `\\w` e `\\b` só reconhecem caracteres ASCII. No Python, sem
essa opção, eles também reconhecem dígitos e letras de outros alfabetos e o resultado ficaria diferente.
Já o `\\s` do JavaScript reconhece espaços Unicode (como o espaço "inquebrável" que vem ao copiar do
WhatsApp); por isso a lista `_SPACE` abaixo põe esses espaços de volta.
"""

from __future__ import annotations

import re

# Equivalente ao `\s` do JavaScript (para usar dentro de colchetes).
_S = r"\s   -     　﻿"

# Ordem importa: CPF primeiro, depois cartão, depois e-mail (igual ao frontend).
_RULES: tuple[tuple[str, str, re.Pattern[str]], ...] = (
    (
        "cpf",
        "[CPF ocultado]",
        re.compile(rf"\b\d{{3}}[.{_S}]?\d{{3}}[.{_S}]?\d{{3}}[-.{_S}]?\d{{2}}\b", re.ASCII),
    ),
    (
        "cartao",
        "[número de cartão ocultado]",
        re.compile(r"\b(?:\d[ -]?){13,19}\b", re.ASCII),
    ),
    (
        "email",
        "[e-mail ocultado]",
        re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", re.ASCII),
    ),
)


def mask_sensitive(text: str) -> tuple[str, list[str]]:
    """Troca CPF, número de cartão e e-mail por marcadores.

    Devolve o texto mascarado e a lista de tipos encontrados ("cpf", "cartao", "email"), sem repetir.
    """
    found: list[str] = []
    result = str(text or "")
    for kind, label, pattern in _RULES:
        result, count = pattern.subn(label, result)
        if count and kind not in found:
            found.append(kind)
    return result, found
