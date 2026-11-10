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
DOCUMENTS_DIR = RAG_DIR / "documentos"
INDEX_FILE = RAG_DIR / "indice" / "indice.json"
# Tamanho dos trechos do RAG (em caracteres) e da repetição entre trechos (docs/RAG.md).
CHUNK_SIZE = 900
CHUNK_OVERLAP = 200

# Endereço e modelo padrão de cada provedor de IA. Todos falam o formato da API da OpenAI
# (/chat/completions), então trocar de provedor é só mudar variáveis de ambiente.
LLM_DEFAULTS: dict[str, tuple[str, str]] = {
    "mock": ("", "demonstracao"),
    "ollama": ("http://localhost:11434/v1", "llama3.1:8b"),
    "groq": ("https://api.groq.com/openai/v1", "openai/gpt-oss-20b"),
    "custom": ("", ""),
}

# Provedores que só funcionam com chave (LLM_API_KEY).
PROVIDERS_NEEDING_KEY = {"groq"}

# "Esforço de raciocínio" dos modelos que pensam antes de responder (como o gpt-oss). O raciocínio
# gasta tokens do LLM_MAX_TOKENS; com "low" sobra espaço para a resposta e cada pergunta gasta menos.
REASONING_EFFORTS = ("low", "medium", "high")
REASONING_MODEL_PREFIXES = ("openai/gpt-oss",)
DEFAULT_REASONING_EFFORT = "low"


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
    # Vazio = o campo "reasoning_effort" não é enviado (provedores como o Ollama podem não aceitar).
    reasoning_effort: str = ""
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
    chunk_size: int = CHUNK_SIZE
    chunk_overlap: int = CHUNK_OVERLAP
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


def _reasoning_effort(env: Mapping[str, str], model: str, problems: list[str]) -> str:
    """LLM_REASONING_EFFORT: low | medium | high | none. Vazio = "low" nos modelos que raciocinam."""
    raw = _text(env, "LLM_REASONING_EFFORT").lower()
    if not raw:
        return DEFAULT_REASONING_EFFORT if model.startswith(REASONING_MODEL_PREFIXES) else ""
    if raw == "none":
        return ""
    if raw not in REASONING_EFFORTS:
        problems.append(f'LLM_REASONING_EFFORT inválido: "{raw}". Use low, medium, high ou none.')
        return ""
    return raw


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
        max_tokens=int(_number(env, "LLM_MAX_TOKENS", 1500, problems)),
        timeout_seconds=_number(env, "LLM_TIMEOUT_MS", 120_000, problems) / 1000,
        reasoning_effort=_reasoning_effort(env, _text(env, "LLM_MODEL", default_model), problems),
    )
    if provider != "mock":
        if not llm.base_url:
            problems.append("LLM_BASE_URL está vazio.")
        if not llm.model:
            problems.append("LLM_MODEL está vazio.")
    if provider in PROVIDERS_NEEDING_KEY and not llm.api_key:
        problems.append(f"LLM_API_KEY é obrigatório para o provedor {provider} (crie a chave no site do provedor).")

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
        documents_dir=DOCUMENTS_DIR,
        index_file=INDEX_FILE,
        top_k=int(_number(env, "RAG_TOP_K", 4, problems)),
        max_message_chars=int(_number(env, "MAX_MESSAGE_CHARS", 1000, problems)),
        max_history_messages=int(_number(env, "MAX_HISTORY_MESSAGES", 8, problems)),
        rate_limit_per_minute=int(_number(env, "RATE_LIMIT_PER_MINUTE", 20, problems)),
    )

    if problems:
        lines = "\n".join(f"- {problem}" for problem in problems)
        raise ConfigError(f"Configuração incompleta ou inválida:\n{lines}\nVeja o arquivo .env.example.")
    return settings
