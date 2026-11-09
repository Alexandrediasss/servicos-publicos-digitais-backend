import pytest

from app.utils.validation import (
    ERROR_FORMAT,
    ERROR_LAST_NOT_USER,
    ERROR_MISSING,
    ERROR_TOO_LONG,
    ValidationError,
    validate_messages,
)


def error_of(body) -> str:
    with pytest.raises(ValidationError) as caught:
        validate_messages(body)
    return caught.value.message


@pytest.mark.parametrize("body", [None, [], {}, {"messages": None}, {"messages": "oi"}, {"messages": []}])
def test_sem_messages(body):
    assert error_of(body) == ERROR_MISSING


def test_mensagens_exatas_do_contrato():
    assert ERROR_MISSING == 'Envie a conversa no campo "messages".'
    assert ERROR_TOO_LONG == "Conversa longa demais. Comece uma nova."
    assert ERROR_FORMAT == "Formato de mensagem inválido."
    assert ERROR_LAST_NOT_USER == "A última mensagem precisa ser da pessoa usuária."


def test_conversa_longa_demais():
    messages = [{"role": "user", "content": "oi"}] * 41
    assert error_of({"messages": messages}) == ERROR_TOO_LONG


@pytest.mark.parametrize(
    "message",
    [
        "oi",
        None,
        {"role": "system", "content": "oi"},
        {"role": "user", "content": 123},
        {"role": "user"},
    ],
)
def test_formato_invalido(message):
    assert error_of({"messages": [message]}) == ERROR_FORMAT


def test_ultima_precisa_ser_do_usuario():
    body = {"messages": [{"role": "user", "content": "oi"}, {"role": "assistant", "content": "olá"}]}
    assert error_of(body) == ERROR_LAST_NOT_USER


def test_mensagens_vazias_sao_descartadas_antes_de_conferir_a_ultima():
    body = {"messages": [{"role": "user", "content": "oi"}, {"role": "assistant", "content": "   "}]}
    assert validate_messages(body) == [{"role": "user", "content": "oi"}]
    assert error_of({"messages": [{"role": "user", "content": "  "}]}) == ERROR_LAST_NOT_USER


def test_limpa_corta_e_mantem_as_ultimas():
    messages = [{"role": "user" if i % 2 == 0 else "assistant", "content": f"  msg {i}  "} for i in range(11)]
    messages[-1]["content"] = "x" * 1500
    clean = validate_messages({"messages": messages}, max_history=8)
    assert len(clean) == 8
    assert clean[0]["content"] == "msg 3"
    assert clean[-1]["content"] == "x" * 1000
    assert clean[-1]["role"] == "user"


def test_ignora_campos_extras():
    clean = validate_messages({"messages": [{"role": "user", "content": "oi", "id": 7}]})
    assert clean == [{"role": "user", "content": "oi"}]
