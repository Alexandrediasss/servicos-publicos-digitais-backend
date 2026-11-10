"""Perguntas de referência contra a BASE REAL (rag/indice/indice.json).

Se um destes testes falhar depois de mudar um documento do RAG, a busca passou a trazer fontes
erradas para uma pergunta comum. Veja docs/RAG.md ("Testar a busca") antes de mudar o teste.
"""

from pathlib import Path

import pytest

from app.config import INDEX_FILE
from app.rag.retriever import collect_sources, retrieve
from app.rag.store import IndexStore

pytestmark = pytest.mark.skipif(not Path(INDEX_FILE).exists(), reason="índice do RAG ainda não foi gerado")


def docs_for(question: str) -> set[str]:
    found = retrieve(IndexStore(INDEX_FILE).load(), question, top_k=4)
    return {result.chunk["doc_id"] for result in found.results}


def test_pergunta_com_tres_servicos_traz_os_tres():
    docs = docs_for("Compare pra mim o Pé-de-Meia, o ENEM e o título de eleitor: para que serve cada um e onde acesso")
    assert {"pe-de-meia", "enem", "e-titulo"} <= docs


def test_cpf_cancelado_so_traz_cpf_e_golpes():
    assert docs_for("Recebi uma mensagem dizendo que meu CPF vai ser cancelado.") == {"cpf", "golpes-digitais"}


def test_enem_sem_fontes_estranhas():
    assert docs_for("Vou fazer o ENEM. O que eu preciso?") <= {"enem", "sisu-prouni-fies"}
    assert "enem" in docs_for("Vou fazer o ENEM. O que eu preciso?")


def test_vacina_traz_meu_sus_digital():
    found = retrieve(IndexStore(INDEX_FILE).load(), "Quero ver se tomei todas as vacinas", top_k=4)
    assert collect_sources(found.results)[0]["title"].startswith("Meu SUS Digital")
