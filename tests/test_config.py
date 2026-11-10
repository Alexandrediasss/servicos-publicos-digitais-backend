import pytest

from app.config import ConfigError, load_settings
from app.utils.rate_limit import RateLimiter


def test_sem_nada_configurado_usa_mock_e_os_padroes():
    settings = load_settings({})
    assert settings.llm.provider == "mock"
    assert settings.llm.model == "demonstracao"
    assert settings.cors_origins == ("http://localhost:5173",)
    assert settings.port == 3001
    assert settings.top_k == 4
    assert settings.max_message_chars == 1000
    assert settings.max_history_messages == 8
    assert settings.rate_limit_per_minute == 20
    assert settings.llm.temperature == 0.2
    assert settings.llm.max_tokens == 700
    assert settings.llm.timeout_seconds == 120
    assert settings.trust_proxy is False


def test_ollama_tem_endereco_e_modelo_padrao():
    llm = load_settings({"LLM_PROVIDER": "ollama"}).llm
    assert llm.base_url == "http://localhost:11434/v1"
    assert llm.model == "llama3.1:8b"


def test_groq_tem_endereco_e_modelo_padrao():
    llm = load_settings({"LLM_PROVIDER": "groq", "LLM_API_KEY": "chave-de-teste"}).llm
    assert llm.base_url == "https://api.groq.com/openai/v1"
    assert llm.model == "openai/gpt-oss-20b"
    assert llm.api_key == "chave-de-teste"


def test_groq_sem_chave_explica_o_que_falta():
    with pytest.raises(ConfigError, match="LLM_API_KEY é obrigatório para o provedor groq"):
        load_settings({"LLM_PROVIDER": "groq"})


def test_variaveis_trocam_os_padroes():
    settings = load_settings(
        {
            "LLM_PROVIDER": "Ollama",
            "LLM_MODEL": "llama3.2:3b",
            "LLM_BASE_URL": "http://outro:11434/v1/",
            "CORS_ORIGIN": "http://localhost:5173, https://guia.netlify.app/",
            "TRUST_PROXY": "1",
        }
    )
    assert settings.llm.model == "llama3.2:3b"
    assert settings.llm.base_url == "http://outro:11434/v1"
    assert settings.cors_origins == ("http://localhost:5173", "https://guia.netlify.app")
    assert settings.trust_proxy is True


def test_provedor_invalido_explica_as_opcoes():
    with pytest.raises(ConfigError, match="mock, ollama, groq, custom"):
        load_settings({"LLM_PROVIDER": "chatgpt"})


def test_custom_sem_endereco_e_modelo():
    with pytest.raises(ConfigError) as caught:
        load_settings({"LLM_PROVIDER": "custom"})
    assert "LLM_BASE_URL" in str(caught.value)
    assert "LLM_MODEL" in str(caught.value)


def test_numero_invalido():
    with pytest.raises(ConfigError, match="RAG_TOP_K precisa ser um número"):
        load_settings({"RAG_TOP_K": "quatro"})


def test_rate_limiter_janela_de_um_minuto():
    now = [0.0]
    limiter = RateLimiter(2, clock=lambda: now[0])
    assert limiter.hit("ip") and limiter.hit("ip")
    assert not limiter.hit("ip")
    assert limiter.hit("outro-ip")
    now[0] = 61
    assert limiter.hit("ip")


def test_rate_limiter_zero_desliga():
    limiter = RateLimiter(0)
    assert all(limiter.hit("ip") for _ in range(100))
