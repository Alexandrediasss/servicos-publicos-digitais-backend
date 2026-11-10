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
- **Como:** modelo de IA **open source** (`openai/gpt-oss-20b`) rodando na **Groq** (plano gratuito) + **RAG** (antes de responder, busca
  trechos numa base de documentos escritos pela equipe, sempre com fonte oficial).

As outras duas abas do site (o Guia e o verificador de links) **não usam esta API**.

O site é um dos materiais educativos de uma **apresentação expositiva de ~75 minutos em cinco eixos**
(inclusão e letramento digital; governo digital e serviços públicos; cidadania digital e proteção de
dados; segurança da informação, com a dinâmica "Golpe ou Real?"; desinformação e bem-estar digital).
O assistente atende sobretudo o **Eixo 2** (qual serviço usar e onde) e reforça os Eixos 3 e 4 (não
pedir dados, alertar golpes). Conceitos e vocabulário em [`docs/CONTEXTO.md`](docs/CONTEXTO.md).

- Site (frontend, React, outro repositório): https://github.com/MariaLuiza007-Teo/servicos-publicos-digitais
- Este repositório: só o backend, em Python. Ele substitui a API antiga em Node.js (`backend/` do
  repositório do site), que fica só como referência.

## Stack

| Parte | Escolha |
| --- | --- |
| Linguagem | Python 3.12 |
| Framework | FastAPI + Uvicorn |
| Chamada à IA | httpx (assíncrono), formato OpenAI `/chat/completions` com `stream=true` |
| IA | Groq (plano gratuito) com `openai/gpt-oss-20b` em produção (Llama só no Ollama, local). No computador: `mock`, `groq` ou `ollama` |
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
│   ├── llm/client.py             # streaming no formato OpenAI (Groq/Ollama) + modo mock
│   ├── prompts/system.py         # instruções da IA
│   ├── rag/                      # frontmatter, chunker, keyword (BM25), store, retriever
│   └── utils/                    # privacy, validation, rate_limit, sse
├── scripts/ingest.py             # gera o índice do RAG
├── rag/
│   ├── documentos/               # base de conhecimento (.md)
│   └── indice/indice.json        # gerado pelo ingest (vai para o Git)
├── tests/                        # pytest
└── docs/                         # contrato, arquitetura, RAG, IA, deploy
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
| Groq (plano gratuito) como provedor de IA em produção | Gratuito, sem cartão e sempre no ar. O Ollama não cabe no plano gratuito do Render e exigiria um computador ligado o tempo todo. Decidido pela equipe em 2026-11-09 (Groq, com "q", não é o Grok do X) |
| Modelo `openai/gpt-oss-20b` em vez de Llama (2026-11-09) | Testado com a chave da equipe: os Llama dão "model not found" no plano gratuito. O gpt-oss é open source (licença Apache 2.0), responde bem em português em ~1 s. Limites gratuitos medidos: 1.000 pedidos/dia e 8.000 tokens/min (cada pergunta gasta ~1.300 tokens, então ~6 perguntas por minuto no site todo) |
| Provedores `mock`, `groq`, `ollama`, `custom` | `mock` para testar sem IA; `ollama` para rodar tudo no computador; `custom` como saída de emergência (qualquer API compatível com OpenAI) |
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
      conexão cai e o pedido à IA é cancelado).
- [x] Funciona com `LLM_PROVIDER=mock` e com `ollama` (testado no computador com um modelo local).
- [x] Provedor `groq` configurado (testado só com provedor simulado; falta testar com uma chave de verdade).
- [x] Testes com pytest passando (mascaramento, validação, chunker, BM25, prompt, cliente da IA, rotas).
- [x] 13 documentos do RAG escritos como **rascunho** e índice gerado.
- [x] Arquivos de contexto: `AGENTS.md`, `CLAUDE.md`, este guia, `README.md`, `docs/`.
- [x] Testado junto com o site no computador (2026-11-08, com o modelo `qwen3:8b` que já estava
      instalado): resposta aos poucos, "Fontes consultadas", "Parar" e erro com o Ollama fora do ar.
- [ ] (Opcional) Testar com o Ollama local e `llama3.1:8b`.
- [ ] **Revisar os 13 documentos do RAG na fonte oficial** (marcados com `CONFERIR`) e trocar para
      `status: revisado`. O `atendimento-presencial-manaus.md` precisa de pesquisa.
- [x] Conta da Groq criada (2026-11-09) e `.env` local preparado com `LLM_PROVIDER=groq`.
- [x] Contexto alinhado ao documento "Conteúdo Teórico" da equipe (`docs/CONTEXTO.md`).
- [x] Chave da Groq no `.env` e testada no computador (2026-11-09) com `openai/gpt-oss-20b`.
- [ ] Apagar a primeira chave da Groq (apareceu numa conversa) e colar uma nova no `.env` local.
- [x] Publicado no Render (2026-11-09): https://servicos-publicos-digitais-backend.onrender.com
      (`/api/health` ok, chat com streaming, CPF mascarado, erro 400 e CORS de `localhost:5173`
      conferidos; testado também com o site local apontando para o Render).
- [ ] Na Netlify, `VITE_API_URL` aponta para a API (sem `/` no final) + novo deploy; no Render,
      `CORS_ORIGIN` tem o endereço do site.

## Próximos passos (opcionais, depois do essencial)

- Busca por significado (embeddings `bge-m3` via Ollama), voltando para BM25 se falhar. O lugar de
  encaixar é `app/rag/retriever.py`.
- Testar perguntas reais dos alunos (sem dados pessoais) e ajustar os documentos.
