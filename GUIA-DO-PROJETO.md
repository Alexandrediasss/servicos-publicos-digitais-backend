# Guia do projeto — API do Guia do Cidadão Digital

Contexto para qualquer pessoa (ou IA) que for mexer neste repositório. Leia antes de começar.
As instruções específicas para assistentes de IA estão no [`AGENTS.md`](AGENTS.md).

## O que é

API do assistente **"Qual serviço eu preciso?"**, uma das três abas do site **Guia do Cidadão
Digital**, do projeto de extensão universitária **"Inclusão Digital: Acesso aos Serviços Públicos
Digitais"** (Sistemas de Informação, 5º período, 2026.2, Manaus-AM).

- **Público do site:** alunos do Ensino Médio (16 e 17 anos), que usam bem o celular para redes
  sociais e jogos, mas conhecem pouco os serviços públicos digitais e têm medo de cair em golpes.
  Muitos só têm celular, às vezes simples e com internet limitada.
- **O que o assistente faz:** a pessoa descreve a necessidade ("vou fazer o ENEM", "quero ver minhas
  vacinas") e ele indica **qual serviço público** resolve e **onde acessar** com segurança.
- **Como:** modelo **Llama** (open source) rodando no **Ollama** + **RAG** (antes de responder, busca
  trechos numa base de documentos escritos pela equipe, sempre com fonte oficial).

As outras duas abas do site (o Guia e o verificador de links) **não usam esta API**.

- Site (frontend, React, outro repositório): https://github.com/MariaLuiza007-Teo/servicos-publicos-digitais
- Este repositório: só o backend, em Python. Ele substitui a API antiga em Node.js (`backend/` do
  repositório do site), que fica só como referência.

## Stack

| Parte | Escolha |
| --- | --- |
| Linguagem | Python 3.12 |
| Framework | FastAPI + Uvicorn |
| Chamada à IA | httpx (assíncrono), formato OpenAI `/chat/completions` com `stream=true` |
| IA | Ollama com `llama3.1:8b` (padrão). `mock` para testar sem IA |
| RAG | Markdown em `rag/documentos/` → `scripts/ingest.py` → `rag/indice/indice.json`; busca BM25 |
| Configuração | Variáveis de ambiente (`.env` no computador, painel do Render em produção) |
| Testes | pytest |
| Banco de dados | **Nenhum** (o site não guarda nada de ninguém) |
| Hospedagem | Render (plano gratuito) para a API — ver `docs/DEPLOY.md` |

## Comandos (na raiz do projeto, com o ambiente virtual ativado)

```bash
python -m app                 # API em http://localhost:3001 (recarrega ao salvar)
python -m pytest              # roda os testes
python -m scripts.ingest      # (re)gera o índice do RAG
```

Primeira vez no computador: veja o [`README.md`](README.md).

## Estrutura

```
servicos-publicos-digitais-backend/
├── AGENTS.md, CLAUDE.md          # contexto para assistentes de IA
├── GUIA-DO-PROJETO.md, README.md
├── .env.example                  # todas as variáveis, comentadas
├── requirements.txt              # dependências da API (Render)
├── requirements-dev.txt          # + pytest
├── app/
│   ├── config.py                 # ÚNICO lugar que lê variáveis de ambiente
│   ├── server.py                 # create_app(): CORS, rotas, erros
│   ├── main.py, __main__.py      # Uvicorn (Render) / python -m app (computador)
│   ├── routes/                   # health.py, chat.py
│   ├── llm/client.py             # streaming do Ollama/OpenAI + modo mock
│   ├── prompts/system.py         # instruções da IA
│   ├── rag/                      # frontmatter, chunker, keyword (BM25), store, retriever
│   └── utils/                    # privacy, validation, rate_limit, sse
├── scripts/ingest.py             # gera o índice do RAG
├── rag/
│   ├── documentos/               # base de conhecimento (.md)
│   └── indice/indice.json        # gerado pelo ingest (vai para o Git)
├── tests/                        # pytest
└── docs/                         # contrato, arquitetura, RAG, Ollama, deploy
```

## Regras do projeto (não negociáveis)

1. **Nenhum dado pessoal é guardado:** sem banco de dados, sem log do conteúdo das perguntas. O log
   de acesso fica desligado; só erros vão para o log.
2. **Mascarar CPF, cartão e e-mail no servidor** antes de enviar à IA, mesmo que o site já mascare.
3. **Chave de API só em variável de ambiente.** Nunca no código nem no Git (o repositório pode ser público).
4. **Manter as regras de segurança do prompt** (itens 3 a 7 de `app/prompts/system.py`).
5. **O assistente orienta, não executa serviços.**
6. **Mensagens de erro para o aluno em português simples**, sem detalhes técnicos.
7. **Código em inglês; comentários, mensagens e textos em português.**
8. **O contrato da API não muda sem combinar com quem cuida do site** (`docs/CONTRATO-API.md`).

## Decisões tomadas (e por quê)

| Decisão | Motivo |
| --- | --- |
| Backend novo em Python, em repositório separado | Escolha da equipe. O Node antigo fica como referência |
| FastAPI | Suporta streaming (SSE) e chamadas assíncronas de forma simples |
| Ollama como provedor de IA (sem Groq) | Gratuito e open source. Decidido pela equipe em 2026-11-08 |
| Provedores `mock`, `ollama`, `custom` | `mock` para testar sem IA; `custom` como saída de emergência (qualquer API compatível com OpenAI) |
| BM25 em vez de banco vetorial | A base é pequena (dezenas de documentos); funciona sem modelo extra |
| Índice em JSON, versionado no Git | O Render não roda o ingest; a API recarrega o índice quando o arquivo muda |
| Limite de uso em memória | Sem banco de dados; uma instância só no plano gratuito |
| Erro 413 com "Sua mensagem ficou grande demais. Tente resumir." | O contrato não definia o texto; aprovado pela equipe |
| Log de acesso desligado | O log de acesso grava o IP de quem acessa; só erros são registrados |
| Documentos do RAG começam como `status: rascunho` | Toda informação precisa ser conferida na fonte oficial antes de valer |
| Sem página `/docs` automática do FastAPI | A API só serve o site |

## Situação atual

Atualizado em 2026-11-08.

- [x] Projeto criado (FastAPI, configuração, `.env.example`, testes).
- [x] `GET /api/health` no formato do contrato.
- [x] `POST /api/chat`: validação, limite de uso, mascaramento, RAG, streaming SSE e "Parar" (a
      conexão cai e o pedido ao Ollama é cancelado).
- [x] Funciona com `LLM_PROVIDER=mock` e com `ollama` (testado no computador com um modelo local).
- [x] Testes com pytest passando (mascaramento, validação, chunker, BM25, prompt, cliente da IA, rotas).
- [x] 13 documentos do RAG escritos como **rascunho** e índice gerado.
- [x] Arquivos de contexto: `AGENTS.md`, `CLAUDE.md`, este guia, `README.md`, `docs/`.
- [x] Testado junto com o site no computador (2026-11-08, com o modelo `qwen3:8b` que já estava
      instalado): resposta aos poucos, "Fontes consultadas", "Parar" e erro com o Ollama fora do ar.
- [ ] Repetir o teste com o modelo oficial `llama3.1:8b`.
- [ ] **Revisar os 13 documentos do RAG na fonte oficial** (marcados com `CONFERIR`) e trocar para
      `status: revisado`. O `atendimento-presencial-manaus.md` precisa de pesquisa.
- [ ] Baixar o modelo oficial do projeto no computador de quem for apresentar: `ollama pull llama3.1:8b`.
- [ ] **Decidir onde o Ollama roda em produção** (o plano gratuito do Render não aguenta o Ollama;
      opções em `docs/DEPLOY.md`).
- [ ] Publicado no Render; `https://SUA-API/api/health` responde `"ok": true`.
- [ ] Na Netlify, `VITE_API_URL` aponta para a API (sem `/` no final) + novo deploy; no Render,
      `CORS_ORIGIN` tem o endereço do site.

## Próximos passos (opcionais, depois do essencial)

- Busca por significado (embeddings `bge-m3` via Ollama), voltando para BM25 se falhar. O lugar de
  encaixar é `app/rag/retriever.py`.
- Testar perguntas reais dos alunos (sem dados pessoais) e ajustar os documentos.
