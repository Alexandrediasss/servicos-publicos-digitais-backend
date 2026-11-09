"""Ponto de entrada para o Uvicorn: `uvicorn app.main:app`.

No computador, prefira `python -m app` (porta 3001, recarrega sozinho ao salvar).
No Render: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --no-access-log`.
"""

from __future__ import annotations

import sys

from app.config import ConfigError, load_settings
from app.server import configure_logging, create_app, log_startup

configure_logging()

try:
    settings = load_settings()
except ConfigError as error:
    print(f"\n{error}\n", file=sys.stderr)
    raise SystemExit(1) from None

app = create_app(settings)
log_startup(settings, app.state.index_store)
