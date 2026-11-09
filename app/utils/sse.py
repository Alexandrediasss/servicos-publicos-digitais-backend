"""Server-Sent Events: o formato de cada pedaço da resposta do /api/chat.

Cada evento é exatamente `event: NOME\\ndata: JSON-EM-UMA-LINHA\\n\\n` (docs/CONTRATO-API.md).
"""

from __future__ import annotations

import json
from typing import Any

SSE_HEADERS = {
    "Cache-Control": "no-cache, no-transform",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}
SSE_MEDIA_TYPE = "text/event-stream; charset=utf-8"


def format_event(name: str, data: Any) -> str:
    # json.dumps troca quebras de linha por "\n", então o JSON sempre fica numa linha só.
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f"event: {name}\ndata: {payload}\n\n"
