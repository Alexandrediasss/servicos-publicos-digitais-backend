"""Configuração central da API.

Tudo que muda entre computadores (ou entre o computador e o Render) vem de variáveis de ambiente.
No computador, elas ficam no arquivo `.env` na raiz do projeto (veja `.env.example`).
No Render, ficam no painel do serviço (Environment).

Regra: nenhum outro arquivo lê `os.environ` diretamente. Variável nova -> adicione aqui E no
`.env.example`, com um comentário em português.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAG_DIR = PROJECT_ROOT / "rag"

# Endereço e modelo padrão de cada provedor de IA. Todos falam o formato da API da OpenAI
# (/chat/completions), então trocar de provedor é só mudar variáveis de ambiente.
LLM_DEFAULTS: dict[str, tuple[str, str]] = {
    "mock": ("", "demonstracao"),
    "ollama": ("http://localhost:11434/v1", "llama3.1:8b"),
    "custom": ("", ""),
}


class ConfigError(Exception):
    """Configuração inválida. A mensagem explica, em português, o que corrigir."""


@dataclass(frozen=True)
class LlmSettings:
    provider: str
    base_url: str
    model: str
    api_key: str
    temperature: float
    max_tokens: int
    timeout_seconds: float
    # Pausa entre as palavras no modo "mock", para imitar o streaming de uma IA de verdade.
    mock_delay_seconds: float = 0.015


@dataclass(frozen=True)
class Settings:
    port: int
    cors_origins: tuple[str, ...]
    trust_proxy: bool
    llm: LlmSettings
    documents_dir: Path
    index_file: Path
    top_k: int
    max_message_chars: int
    max_history_messages: int
    rate_limit_per_minute: int
    # Valores fixos do contrato da API (docs/CONTRATO-API.md). Não vêm do ambiente.
    chunk_size: int = 900
    chunk_overlap: int = 200
    max_messages: int = 40
    max_body_bytes: int = 32 * 1024


def _text(env: Mapping[str, str], name: str, default: str = "") -> str:
    value = env.get(name)
    if value is None or value.strip() == "":
        return default
    return value.strip()


def _number(env: Mapping[str, str], name: str, default: float, problems: list[str]) -> float:
    raw = _text(env, name)
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        problems.append(f'{name} precisa ser um número (está "{raw}").')
        return default


def _flag(env: Mapping[str, str], name: str) -> bool:
    return _text(env, name, "0").lower() in {"1", "true", "sim", "yes"}


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    """Lê a configuração. Sem `env`, usa o `.env` da raiz + as variáveis do sistema."""
    if env is None:
        load_dotenv(PROJECT_ROOT / ".env")
        env = os.environ

    problems: list[str] = []

    provider = _text(env, "LLM_PROVIDER", "mock").lower()
    if provider not in LLM_DEFAULTS:
        options = ", ".join(LLM_DEFAULTS)
        raise ConfigError(f'LLM_PROVIDER inválido: "{provider}". Use um destes: {options}.')
    default_url, default_model = LLM_DEFAULTS[provider]

    llm = LlmSettings(
        provider=provider,
        base_url=_text(env, "LLM_BASE_URL", default_url).rstrip("/"),
        model=_text(env, "LLM_MODEL", default_model),
        api_key=_text(env, "LLM_API_KEY"),
        temperature=_number(env, "LLM_TEMPERATURE", 0.2, problems),
        max_tokens=int(_number(env, "LLM_MAX_TOKENS", 700, problems)),
        timeout_seconds=_number(env, "LLM_TIMEOUT_MS", 120_000, problems) / 1000,
    )
    if provider != "mock":
        if not llm.base_url:
            problems.append("LLM_BASE_URL está vazio.")
        if not llm.model:
            problems.append("LLM_MODEL está vazio.")

    cors = tuple(
        origin.strip().rstrip("/")
        for origin in _text(env, "CORS_ORIGIN", "http://localhost:5173").split(",")
        if origin.strip()
    )

    settings = Settings(
        port=int(_number(env, "PORT", 3001, problems)),
        cors_origins=cors,
        trust_proxy=_flag(env, "TRUST_PROXY"),
        llm=llm,
        documents_dir=RAG_DIR / "documentos",
        index_file=RAG_DIR / "indice" / "indice.json",
        top_k=int(_number(env, "RAG_TOP_K", 4, problems)),
        max_message_chars=int(_number(env, "MAX_MESSAGE_CHARS", 1000, problems)),
        max_history_messages=int(_number(env, "MAX_HISTORY_MESSAGES", 8, problems)),
        rate_limit_per_minute=int(_number(env, "RATE_LIMIT_PER_MINUTE", 20, problems)),
    )

    if problems:
        lines = "\n".join(f"- {problem}" for problem in problems)
        raise ConfigError(f"Configuração incompleta ou inválida:\n{lines}\nVeja o arquivo .env.example.")
    return settings
