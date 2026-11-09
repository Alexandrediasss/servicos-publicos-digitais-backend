"""Limite de uso: no máximo N pedidos por minuto para cada IP.

Fica só na memória (sem banco de dados) e some quando a API reinicia. O IP fica guardado por no
máximo um minuto, só para contar os pedidos, e nunca vai para o log.
"""

from __future__ import annotations

import time
from collections.abc import Callable

from starlette.requests import Request

RATE_LIMIT_MESSAGE = "Muitas perguntas em pouco tempo. Espere um minuto e tente de novo."


class RateLimiter:
    """Janela fixa de `window_seconds` por chave (IP)."""

    def __init__(
        self,
        limit: int,
        window_seconds: float = 60.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.limit = limit
        self.window = window_seconds
        self._clock = clock
        self._hits: dict[str, tuple[float, int]] = {}
        self._last_cleanup = clock()

    def hit(self, key: str) -> bool:
        """Conta um pedido. Devolve False quando a chave passou do limite."""
        if self.limit <= 0:  # 0 desliga o limite
            return True
        now = self._clock()
        self._cleanup(now)
        started, count = self._hits.get(key, (now, 0))
        if now - started >= self.window:
            started, count = now, 0
        count += 1
        self._hits[key] = (started, count)
        return count <= self.limit

    def _cleanup(self, now: float) -> None:
        if now - self._last_cleanup < self.window:
            return
        self._last_cleanup = now
        expired = [key for key, (started, _) in self._hits.items() if now - started >= self.window]
        for key in expired:
            del self._hits[key]


def client_ip(request: Request, trust_proxy: bool) -> str:
    """IP de quem fez o pedido.

    No Render, a API fica atrás de um proxy: o IP que chega na conexão é o do proxy, e o IP real
    vem no cabeçalho X-Forwarded-For (o primeiro da lista). Só confiamos nesse cabeçalho com
    TRUST_PROXY=1, porque no computador qualquer um poderia inventá-lo.
    """
    if trust_proxy:
        forwarded = request.headers.get("x-forwarded-for", "")
        first = forwarded.split(",")[0].strip()
        if first:
            return first
    return request.client.host if request.client else "desconhecido"
