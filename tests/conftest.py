"""Peças compartilhadas pelos testes."""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, load_settings
from app.server import create_app

SAMPLE_INDEX = {
    "version": 1,
    "created_at": "2026-11-08T12:00:00Z",
    "documents": [
        {"id": "enem", "title": "ENEM", "source": "https://www.gov.br/inep/enem", "category": "educacao"},
        {"id": "meu-sus", "title": "Meu SUS Digital", "source": "https://meususdigital.saude.gov.br", "category": "saude"},
    ],
    "chunks": [
        {
            "id": "enem#1",
            "doc_id": "enem",
            "title": "ENEM",
            "heading": "Para que serve",
            "source": "https://www.gov.br/inep/enem",
            "category": "educacao",
            "text": "O ENEM é a prova usada para entrar na faculdade. A inscrição é pela Página do Participante.",
        },
        {
            "id": "enem#2",
            "doc_id": "enem",
            "title": "ENEM",
            "heading": "Isenção",
            "source": "https://www.gov.br/inep/enem",
            "category": "educacao",
            "text": "Quem estuda em escola pública no último ano tem isenção da taxa de inscrição do ENEM.",
        },
        {
            "id": "meu-sus#1",
            "doc_id": "meu-sus",
            "title": "Meu SUS Digital",
            "heading": "Para que serve",
            "source": "https://meususdigital.saude.gov.br",
            "category": "saude",
            "text": "Mostra a carteira de vacinação e o histórico de saúde.",
        },
    ],
}


def make_settings(tmp_path: Path, **changes) -> Settings:
    """Configuração de teste: modo mock, sem atraso e com o índice numa pasta temporária."""
    base = load_settings({"LLM_PROVIDER": "mock"})
    llm = dataclasses.replace(base.llm, mock_delay_seconds=0)
    settings = dataclasses.replace(
        base,
        llm=llm,
        documents_dir=tmp_path / "documentos",
        index_file=tmp_path / "indice.json",
    )
    return dataclasses.replace(settings, **changes)


@pytest.fixture
def index_file(tmp_path: Path) -> Path:
    path = tmp_path / "indice.json"
    path.write_text(json.dumps(SAMPLE_INDEX), encoding="utf-8")
    return path


@pytest.fixture
def client(tmp_path: Path, index_file: Path) -> TestClient:
    return TestClient(create_app(make_settings(tmp_path)))


def parse_sse(text: str) -> list[tuple[str, dict]]:
    """Lê a resposta do /api/chat do mesmo jeito que o frontend (chatApi.js)."""
    events = []
    for raw in text.split("\n\n"):
        if not raw.strip():
            continue
        name, data = "message", []
        for line in raw.split("\n"):
            if line.startswith("event:"):
                name = line[6:].strip()
            elif line.startswith("data:"):
                data.append(line[5:].lstrip())
        events.append((name, json.loads("\n".join(data))))
    return events
