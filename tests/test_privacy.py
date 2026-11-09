"""Mascaramento: os mesmos casos de teste do frontend (frontend/src/lib/privacy.test.js)."""

from app.utils.privacy import mask_sensitive


def test_mascara_cpf_com_pontuacao():
    text, found = mask_sensitive("meu cpf é 123.456.789-09")
    assert text == "meu cpf é [CPF ocultado]"
    assert found == ["cpf"]


def test_mascara_cpf_sem_pontuacao():
    text, _ = mask_sensitive("cpf 12345678909 ok")
    assert text == "cpf [CPF ocultado] ok"


def test_mascara_cartao_e_email():
    text, found = mask_sensitive("cartão 4111 1111 1111 1111 e email ana@exemplo.com.br")
    assert "[número de cartão ocultado]" in text
    assert "[e-mail ocultado]" in text
    assert set(found) == {"cartao", "email"}


def test_nao_altera_texto_comum_anos_e_telefones_curtos():
    original = "Vou fazer o ENEM em 2026 e tenho 17 anos. Liguei para 3333-4444."
    text, found = mask_sensitive(original)
    assert text == original
    assert found == []


def test_cpf_com_espaco_inquebravel_do_whatsapp():
    text, found = mask_sensitive("cpf 123 456 789 09")
    assert text == "cpf [CPF ocultado]"
    assert found == ["cpf"]


def test_digitos_de_outros_alfabetos_nao_contam_como_cpf():
    # "١٢٣" são dígitos árabes: no JavaScript \d não pega, então aqui também não pode pegar.
    original = "código ١٢٣٤٥٦٧٨٩٠٩"
    text, found = mask_sensitive(original)
    assert text == original
    assert found == []


def test_tipos_nao_se_repetem():
    _, found = mask_sensitive("a@b.com e c@d.com")
    assert found == ["email"]
