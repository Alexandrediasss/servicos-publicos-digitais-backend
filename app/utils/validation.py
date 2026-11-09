"""Validação do corpo do POST /api/chat.

As mensagens de erro são mostradas DIRETO para o aluno pelo frontend: por isso são em português
simples. Os textos fazem parte do contrato da API (docs/CONTRATO-API.md); não mude sem combinar.
"""

from __future__ import annotations

from typing import Any

ERROR_MISSING = 'Envie a conversa no campo "messages".'
ERROR_TOO_LONG = "Conversa longa demais. Comece uma nova."
ERROR_FORMAT = "Formato de mensagem inválido."
ERROR_LAST_NOT_USER = "A última mensagem precisa ser da pessoa usuária."

ALLOWED_ROLES = ("user", "assistant")


class ValidationError(Exception):
    """Pedido inválido. `message` vai para o aluno."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def validate_messages(
    body: Any,
    *,
    max_messages: int = 40,
    max_chars: int = 1000,
    max_history: int = 8,
) -> list[dict[str, str]]:
    """Confere e limpa a conversa. Devolve só as últimas `max_history` mensagens.

    Cada `content` passa por trim e é cortado em `max_chars` caracteres; mensagens vazias somem.
    """
    messages = body.get("messages") if isinstance(body, dict) else None
    if not isinstance(messages, list) or not messages:
        raise ValidationError(ERROR_MISSING)
    if len(messages) > max_messages:
        raise ValidationError(ERROR_TOO_LONG)

    clean: list[dict[str, str]] = []
    for message in messages:
        if (
            not isinstance(message, dict)
            or message.get("role") not in ALLOWED_ROLES
            or not isinstance(message.get("content"), str)
        ):
            raise ValidationError(ERROR_FORMAT)
        content = message["content"].strip()[:max_chars]
        if content:
            clean.append({"role": message["role"], "content": content})

    if not clean or clean[-1]["role"] != "user":
        raise ValidationError(ERROR_LAST_NOT_USER)
    return clean[-max_history:]
