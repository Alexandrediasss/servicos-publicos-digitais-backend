"""Frontmatter, chunker, BM25, índice e ingestão."""

import json
import os
from datetime import datetime, timezone

from app.rag.chunker import chunk_markdown
from app.rag.frontmatter import parse_frontmatter
from app.rag.keyword import build_keyword_index, normalize, search_keyword, stem, tokenize
from app.rag.retriever import collect_sources, retrieve
from app.rag.store import IndexStore
from scripts.ingest import build_index


# ---------- frontmatter ----------


def test_le_o_frontmatter_e_separa_o_corpo():
    meta, body = parse_frontmatter(
        '---\ntitulo: ENEM\nfonte: "https://www.gov.br/inep"\ncategoria: educacao\n---\n# ENEM\n\nTexto.'
    )
    assert meta["titulo"] == "ENEM"
    assert meta["fonte"] == "https://www.gov.br/inep"
    assert body == "# ENEM\n\nTexto."


def test_documento_sem_frontmatter_vira_so_corpo():
    assert parse_frontmatter("Só texto.") == ({}, "Só texto.")


def test_frontmatter_com_bom_e_quebra_de_linha_do_windows():
    meta, body = parse_frontmatter("﻿---\r\ntitulo: CPF\r\n---\r\nTexto.")
    assert meta == {"titulo": "CPF"}
    assert body == "Texto."


def test_valor_com_dois_pontos_continua_inteiro():
    meta, _ = parse_frontmatter("---\nfonte: https://www.gov.br/x\n---\n")
    assert meta["fonte"] == "https://www.gov.br/x"


# ---------- chunker ----------


def test_divide_por_secao_e_respeita_o_tamanho_maximo():
    paragraph = ("Frase de teste sobre serviços públicos digitais. " * 8).strip()
    md = f"# Título\n\n## Seção A\n\n{paragraph}\n\n{paragraph}\n\n## Seção B\nTexto curto da seção B."
    chunks = chunk_markdown(md, size=500, overlap=100)
    assert len(chunks) >= 3
    assert chunks[0].heading == "Seção A"
    assert chunks[-1].heading == "Seção B"
    assert chunks[-1].text == "Texto curto da seção B."
    assert all(len(chunk.text) <= 500 + 100 for chunk in chunks)


def test_paragrafo_curto_no_fim_se_repete_no_proximo_trecho():
    long_text = "a" * 300
    short = "Parágrafo curto."
    md = f"## Seção\n\n{long_text}\n\n{short}\n\n{long_text}"
    chunks = chunk_markdown(md, size=400, overlap=200)
    assert chunks[0].text.endswith(short)
    assert chunks[1].text.startswith(short)


def test_paragrafo_gigante_e_cortado_por_frases():
    sentence = "Uma frase com várias palavras para teste."
    md = " ".join([sentence] * 50)
    chunks = chunk_markdown(md, size=200, overlap=0)
    assert len(chunks) > 1
    assert all(len(chunk.text) <= 200 for chunk in chunks)


def test_titulo_sem_texto_nao_gera_trecho_vazio():
    chunks = chunk_markdown("# ENEM\n\n## Para que serve\n\nTexto.")
    assert [(c.heading, c.text) for c in chunks] == [("Para que serve", "Texto.")]


# ---------- BM25 ----------


def test_normalize_tira_acentos_e_maiusculas():
    assert normalize("Inscrição Ação ÚNICO") == "inscricao acao unico"


def test_stemming_simples():
    assert stem("inscricoes") == "inscricao"
    assert stem("mulheres") == "mulher"
    assert stem("vacinas") == "vacina"
    assert stem("gas") == "gas"


def test_tokenize_ignora_acentos_maiusculas_e_palavras_vazias():
    assert tokenize("Quero fazer a INSCRIÇÃO no ENEM") == ["inscricao", "enem"]


def test_bm25_encontra_o_trecho_certo():
    chunks = [
        {"title": "ENEM", "text": "Inscrição no Exame Nacional do Ensino Médio pela Página do Participante."},
        {"title": "Carteira de Trabalho Digital", "text": "Contratos, salários e vagas de emprego."},
        {"title": "Meu SUS Digital", "text": "Carteira de vacinação e histórico de saúde."},
    ]
    index = build_keyword_index(chunks)
    first = search_keyword(index, "onde vejo minha vacinação?", 2)[0]
    assert first[0] == 2
    assert search_keyword(index, "xyzabc", 2) == []


def test_titulo_conta_mais_que_o_texto():
    chunks = [
        {"title": "Outro assunto", "text": "fala de enem uma vez"},
        {"title": "ENEM", "text": "outro texto qualquer"},
    ]
    index = build_keyword_index(chunks)
    assert search_keyword(index, "enem")[0][0] == 1


def test_bm25_com_base_vazia():
    assert search_keyword(build_keyword_index([]), "enem") == []


# ---------- índice e busca ----------


def test_store_le_e_recarrega_quando_o_arquivo_muda(tmp_path, index_file):
    store = IndexStore(index_file)
    first = store.load()
    assert first.summary() == {
        "ready": True,
        "documents": 2,
        "chunks": 3,
        "createdAt": "2026-11-08T12:00:00Z",
        "retriever": "palavras-chave",
    }
    assert store.load() is first  # sem mudança, não relê

    data = json.loads(index_file.read_text(encoding="utf-8"))
    data["chunks"] = data["chunks"][:1]
    index_file.write_text(json.dumps(data), encoding="utf-8")
    stat = index_file.stat()
    os.utime(index_file, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000))
    assert store.load().summary()["chunks"] == 1


def test_store_sem_arquivo_ou_com_arquivo_quebrado(tmp_path):
    missing = IndexStore(tmp_path / "nao-existe.json").load()
    assert missing.summary()["ready"] is False
    assert missing.summary()["createdAt"] is None

    broken = tmp_path / "quebrado.json"
    broken.write_text("{ isto não é json", encoding="utf-8")
    assert IndexStore(broken).load().ready is False


def test_retrieve_sem_base(tmp_path):
    retrieval = retrieve(IndexStore(tmp_path / "x.json").load(), "enem")
    assert retrieval.mode == "sem-base"
    assert retrieval.rag_ready is False
    assert retrieval.results == ()


def test_retrieve_e_fontes_sem_repetir_documento(index_file):
    retrieval = retrieve(IndexStore(index_file).load(), "inscrição e isenção do ENEM", top_k=4)
    assert retrieval.mode == "palavras-chave"
    assert retrieval.rag_ready is True
    assert [r.chunk["doc_id"] for r in retrieval.results][:2] == ["enem", "enem"]
    sources = collect_sources(retrieval.results)
    assert sources == [{"title": "ENEM", "url": "https://www.gov.br/inep/enem", "category": "educacao"}]


def test_fonte_sem_link_vira_null():
    from app.rag.retriever import SearchResult

    sources = collect_sources((SearchResult({"doc_id": "x", "title": "X", "source": ""}, 1.0),))
    assert sources == [{"title": "X", "url": None, "category": None}]


# ---------- ingestão ----------


def test_ingest_monta_o_indice(tmp_path):
    docs = tmp_path / "documentos"
    docs.mkdir()
    (docs / "enem.md").write_text(
        "---\ntitulo: ENEM\nfonte: https://www.gov.br/inep\ncategoria: educacao\natualizado_em: 2026-11-08\n---\n"
        "<!-- comentário que não entra -->\n# ENEM\n\n## Para que serve\n\nProva para a faculdade.",
        encoding="utf-8",
    )
    (docs / "sem-fonte.md").write_text("---\ntitulo: Sem fonte\nstatus: rascunho\n---\nTexto.", encoding="utf-8")
    (docs / "_MODELO.md").write_text("ignorado", encoding="utf-8")
    (docs / "README.md").write_text("ignorado", encoding="utf-8")
    (docs / "vazio.md").write_text("---\ntitulo: Vazio\nfonte: https://x.gov.br\n---\n", encoding="utf-8")

    now = datetime(2026, 11, 8, 12, 0, 0, 123, tzinfo=timezone.utc)
    index, warnings = build_index(docs, now=now)

    assert index["created_at"] == "2026-11-08T12:00:00Z"
    assert [doc["id"] for doc in index["documents"]] == ["enem", "sem-fonte"]
    enem_chunk = index["chunks"][0]
    assert enem_chunk == {
        "id": "enem#1",
        "doc_id": "enem",
        "title": "ENEM",
        "heading": "Para que serve",
        "source": "https://www.gov.br/inep",
        "category": "educacao",
        "text": "Prova para a faculdade.",
    }
    assert "comentário" not in json.dumps(index, ensure_ascii=False)
    assert any("sem-fonte.md" in w and "fonte" in w for w in warnings)
    assert any("vazio.md" in w for w in warnings)
    assert any("sem-fonte.md" in w and "rascunho" in w for w in warnings)
    assert not any("enem.md" in w for w in warnings)


def test_ingest_sem_pasta_gera_indice_vazio(tmp_path):
    index, _ = build_index(tmp_path / "nao-existe")
    assert index["documents"] == [] and index["chunks"] == []
