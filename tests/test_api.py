"""Testes de ponta a ponta das rotas, seguindo docs/CONTRATO-API.md."""

import dataclasses
import json

import httpx
from fastapi.testclient import TestClient

from app.server import create_app
from tests.conftest import make_settings, parse_sse

ASK_ENEM = {"messages": [{"role": "user", "content": "Quero fazer a inscrição no ENEM"}]}


# ---------- GET /api/health ----------


def test_health_no_formato_do_contrato(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "llm": {"provider": "mock", "model": "demonstracao"},
        "rag": {
            "ready": True,
            "documents": 2,
            "chunks": 3,
            "createdAt": "2026-11-08T12:00:00Z",
            "retriever": "palavras-chave",
        },
    }


def test_health_sem_indice(tmp_path):
    client = TestClient(create_app(make_settings(tmp_path, index_file=tmp_path / "nada.json")))
    rag = client.get("/api/health").json()["rag"]
    assert rag == {"ready": False, "documents": 0, "chunks": 0, "createdAt": None, "retriever": "palavras-chave"}


# ---------- POST /api/chat: resposta normal ----------


def test_chat_responde_em_sse(client):
    response = client.post("/api/chat", json=ASK_ENEM)
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    assert response.headers["cache-control"] == "no-cache, no-transform"
    assert response.headers["x-accel-buffering"] == "no"

    events = parse_sse(response.text)
    names = [name for name, _ in events]
    assert names[0] == "meta"
    assert names[-1] == "done"
    assert set(names[1:-1]) == {"token"}
    assert events[-1][1] == {}

    meta = events[0][1]
    assert meta == {
        "sources": [{"title": "ENEM", "url": "https://www.gov.br/inep/enem", "category": "educacao"}],
        "retrieval": "palavras-chave",
        "ragReady": True,
        "masked": [],
    }
    text = "".join(data["text"] for name, data in events if name == "token")
    assert "Modo de demonstração" in text


def test_cada_evento_tem_exatamente_duas_linhas(client):
    raw = client.post("/api/chat", json=ASK_ENEM).text
    for block in raw.split("\n\n")[:-1]:
        lines = block.split("\n")
        assert len(lines) == 2
        assert lines[0].startswith("event: ")
        assert lines[1].startswith("data: ")
    assert raw.endswith("\n\n")


def test_chat_sem_base(tmp_path):
    client = TestClient(create_app(make_settings(tmp_path, index_file=tmp_path / "nada.json")))
    meta = parse_sse(client.post("/api/chat", json=ASK_ENEM).text)[0][1]
    assert meta == {"sources": [], "retrieval": "sem-base", "ragReady": False, "masked": []}


def test_mascara_antes_de_enviar_para_a_ia(tmp_path, index_file):
    sent = {}

    def handler(request):
        sent["body"] = json.loads(request.content)
        return httpx.Response(200, text='data: {"choices":[{"delta":{"content":"ok"}}]}\n\ndata: [DONE]\n\n')

    settings = make_settings(tmp_path)
    settings = dataclasses.replace(settings, llm=dataclasses.replace(settings.llm, provider="ollama", base_url="http://ia"))
    client = TestClient(create_app(settings, llm_transport=httpx.MockTransport(handler)))

    body = {
        "messages": [
            {"role": "user", "content": "meu email é ana@exemplo.com"},
            {"role": "assistant", "content": "Não compartilhe seu e-mail."},
            {"role": "user", "content": "meu cpf é 123.456.789-09, e o ENEM?"},
        ]
    }
    events = parse_sse(client.post("/api/chat", json=body).text)
    assert events[0][1]["masked"] == ["email", "cpf"]
    assert [name for name, _ in events] == ["meta", "token", "done"]

    sent_text = json.dumps(sent["body"], ensure_ascii=False)
    assert "123.456.789-09" not in sent_text
    assert "ana@exemplo.com" not in sent_text
    assert "[CPF ocultado]" in sent_text
    assert sent["body"]["messages"][0]["role"] == "system"
    assert "CONTEXTO:\n[1] ENEM" in sent["body"]["messages"][0]["content"]


def test_falha_da_ia_vira_evento_de_erro_em_portugues(tmp_path, index_file, caplog):
    settings = make_settings(tmp_path)
    settings = dataclasses.replace(settings, llm=dataclasses.replace(settings.llm, provider="ollama", base_url="http://ia"))

    def handler(request):
        raise httpx.ConnectError("Connection refused")

    client = TestClient(create_app(settings, llm_transport=httpx.MockTransport(handler)))
    secret_question = "pergunta secreta sobre o ENEM"
    with caplog.at_level("INFO", logger="guia"):
        events = parse_sse(client.post("/api/chat", json={"messages": [{"role": "user", "content": secret_question}]}).text)

    assert events[0][0] == "meta"
    assert events[-1] == ("error", {"message": "O assistente está indisponível agora. Tente de novo em alguns minutos."})
    assert "ConnectError" in caplog.text  # detalhe técnico vai para o log...
    assert secret_question not in caplog.text  # ...mas a pergunta nunca


def test_erro_inesperado_vira_mensagem_generica(tmp_path, index_file, monkeypatch):
    async def broken(*args, **kwargs):
        raise RuntimeError("bug com texto da pergunta")
        yield  # pragma: no cover

    monkeypatch.setattr("app.routes.chat.stream_chat", broken)
    client = TestClient(create_app(make_settings(tmp_path)))
    events = parse_sse(client.post("/api/chat", json=ASK_ENEM).text)
    assert events[-1] == ("error", {"message": "Algo deu errado ao gerar a resposta."})


# ---------- POST /api/chat: erros antes de responder ----------


def test_pedido_invalido_responde_400_em_json(client):
    cases = [
        ({}, 'Envie a conversa no campo "messages".'),
        ({"messages": [{"role": "robo", "content": "oi"}]}, "Formato de mensagem inválido."),
        ({"messages": [{"role": "user", "content": "oi"}] * 41}, "Conversa longa demais. Comece uma nova."),
        ({"messages": [{"role": "assistant", "content": "oi"}]}, "A última mensagem precisa ser da pessoa usuária."),
    ]
    for body, message in cases:
        response = client.post("/api/chat", json=body)
        assert response.status_code == 400
        assert response.json() == {"error": message}


def test_json_quebrado_responde_400(client):
    response = client.post("/api/chat", content=b"{nao e json", headers={"Content-Type": "application/json"})
    assert response.status_code == 400
    assert "error" in response.json()


def test_corpo_maior_que_32kb_responde_413(client):
    body = {"messages": [{"role": "user", "content": "a" * 40_000}]}
    response = client.post("/api/chat", json=body)
    assert response.status_code == 413
    assert response.json() == {"error": "Sua mensagem ficou grande demais. Tente resumir."}


def test_limite_de_uso_responde_429(tmp_path, index_file):
    client = TestClient(create_app(make_settings(tmp_path, rate_limit_per_minute=2)))
    assert client.post("/api/chat", json=ASK_ENEM).status_code == 200
    assert client.post("/api/chat", json={}).status_code == 400  # pedido inválido também conta
    response = client.post("/api/chat", json=ASK_ENEM)
    assert response.status_code == 429
    assert response.json() == {"error": "Muitas perguntas em pouco tempo. Espere um minuto e tente de novo."}


def test_limite_usa_o_ip_do_x_forwarded_for_atras_do_proxy(tmp_path, index_file):
    client = TestClient(create_app(make_settings(tmp_path, rate_limit_per_minute=1, trust_proxy=True)))
    ask = lambda ip: client.post("/api/chat", json=ASK_ENEM, headers={"X-Forwarded-For": f"{ip}, 10.0.0.1"})
    assert ask("200.1.1.1").status_code == 200
    assert ask("200.2.2.2").status_code == 200  # outra pessoa
    assert ask("200.1.1.1").status_code == 429


def test_rota_desconhecida_responde_404_em_portugues(client):
    response = client.get("/api/nada")
    assert response.status_code == 404
    assert response.json() == {"error": "Rota não encontrada."}


# ---------- CORS ----------


def test_cors_libera_o_site_configurado(client):
    response = client.options(
        "/api/chat",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST",
                 "Access-Control-Request-Headers": "content-type"},
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_bloqueia_outros_sites(client):
    response = client.get("/api/health", headers={"Origin": "https://site-estranho.com"})
    assert "access-control-allow-origin" not in response.headers


def test_cors_com_varias_origens(tmp_path, index_file):
    origins = ("http://localhost:5173", "https://guia-cidadao-digital.netlify.app")
    client = TestClient(create_app(make_settings(tmp_path, cors_origins=origins)))
    response = client.get("/api/health", headers={"Origin": origins[1]})
    assert response.headers["access-control-allow-origin"] == origins[1]
