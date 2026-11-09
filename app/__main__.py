"""Roda a API no computador: `python -m app`.

- Porta 3001 (é para onde o site, em desenvolvimento, encaminha as chamadas /api).
- Recarrega sozinho quando você salva um arquivo .py.
- Sem log de acesso (ele grava o IP de quem acessa; só registramos erros).
"""

from __future__ import annotations

import sys

import uvicorn

from app.config import ConfigError, load_settings


def main() -> None:
    try:
        settings = load_settings()
    except ConfigError as error:
        print(f"\n{error}\n", file=sys.stderr)
        sys.exit(1)

    print(f"API em http://localhost:{settings.port}  (Ctrl+C para parar)")
    uvicorn.run(
        "app.main:app",
        host="localhost",
        port=settings.port,
        reload=True,
        reload_dirs=["app"],
        access_log=False,
    )


if __name__ == "__main__":
    main()
