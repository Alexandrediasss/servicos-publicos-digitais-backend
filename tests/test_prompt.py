from app.prompts.system import NO_CONTEXT, SYSTEM_PROMPT, build_messages
from app.rag.retriever import SearchResult


def test_regras_de_seguranca_estao_no_prompt():
    for rule in (
        "3. Use o CONTEXTO abaixo como fonte principal.",
        "Nunca invente nomes de serviços, endereços de sites, valores, prazos ou regras.",
        "4. Só indique endereços de sites que estejam no CONTEXTO ou que terminem em .gov.br, .jus.br, "
        ".leg.br, .mp.br, .mil.br ou .def.br.",
        "5. Nunca peça CPF, senha, código de verificação, número de cartão ou foto de documento.",
        '6. Se a mensagem descrever um possível golpe',
        'recomende a aba "Esse link é oficial?" do site.',
        "7. Você não é um órgão do governo e não realiza serviços: apenas orienta.",
    ):
        assert rule in SYSTEM_PROMPT


def test_monta_system_com_trechos_e_depois_o_historico():
    results = (
        SearchResult({"title": "ENEM", "heading": "Isenção", "source": "https://www.gov.br/inep", "text": "Texto A."}, 2.0),
        SearchResult({"title": "Golpes", "heading": "", "source": "", "text": "Texto B."}, 1.0),
    )
    history = [
        {"role": "user", "content": "oi"},
        {"role": "assistant", "content": "olá"},
        {"role": "user", "content": "ENEM?"},
    ]
    messages = build_messages(history, results)

    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == (
        f"{SYSTEM_PROMPT}\n\nCONTEXTO:\n"
        "[1] ENEM (Isenção) — fonte: https://www.gov.br/inep\nTexto A.\n\n"
        "[2] Golpes — fonte: sem link\nTexto B."
    )
    assert messages[1:] == history


def test_sem_trechos_usa_o_aviso_de_contexto_vazio():
    messages = build_messages([{"role": "user", "content": "oi"}], ())
    assert messages[0]["content"].endswith(f"CONTEXTO:\n{NO_CONTEXT}")
    assert "Nenhum trecho da base de conhecimento corresponde a esta pergunta." in NO_CONTEXT
