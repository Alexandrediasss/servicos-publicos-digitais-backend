# AGENTS.md — instruções para assistentes de IA

Este arquivo é lido por assistentes de IA de programação (Claude Code, GitHub Copilot, Cursor, Codex,
Gemini e outros). Ele resume o que a IA precisa saber para mexer neste projeto **sem quebrar o
contrato com o site e sem violar as regras de privacidade**. Pessoas também podem ler.

Antes de qualquer tarefa, leia também o [`GUIA-DO-PROJETO.md`](GUIA-DO-PROJETO.md). Detalhes de cada
área ficam em `docs/` (lista no fim).

## O projeto em 5 linhas

- API em **Python 3.12 + FastAPI** que atende a aba "Qual serviço eu preciso?" do site **Guia do
  Cidadão Digital** (projeto de extensão universitária, Manaus-AM, público: alunos do Ensino Médio).
- O site (React) fica em outro repositório: https://github.com/MariaLuiza007-Teo/servicos-publicos-digitais
- A API recebe a conversa, **mascara dados pessoais**, busca trechos na base própria (**RAG com BM25**),
  manda tudo para um modelo de IA **open source** (`openai/gpt-oss-20b` na **Groq**, plano gratuito, em
  produção; Llama no **Ollama**, opcional, no computador) e devolve a resposta aos pedaços (**SSE**).
- **Sem banco de dados.** Nada de ninguém é guardado.
- O frontend **não pode precisar mudar**: a API segue o contrato em [`docs/CONTRATO-API.md`](docs/CONTRATO-API.md).

## Fale a mesma língua da apresentação

O site é material educativo de uma apresentação em cinco eixos (inclusão e letramento digital, governo
digital, proteção de dados, segurança, desinformação). Textos do assistente, do prompt e do RAG usam os
mesmos conceitos: **os quatro sinais de golpe** (urgência, pedido de dado ou código, pedido de dinheiro,
link fora do endereço oficial), **conta gov.br como identidade digital** (bronze, prata, ouro), **PAC e
CRAS** quando o digital não resolve, e as três mensagens-chave: *acesso digital é direito*, *seus dados
são seus*, *desconfie e confirme*. Resumo completo em [`docs/CONTEXTO.md`](docs/CONTEXTO.md).

## Como a equipe trabalha (respeite)

- **Fale em português do Brasil**, simples e direto.
- **Git é com a pessoa usuária.** Não crie branch, não faça commit, merge, rebase nem push. Edite os
  arquivos e diga o que mudou.
- **`.env`:** pode ser editado pela IA (a equipe autorizou), mas **nunca** mostre, copie ou repita o
  valor de `LLM_API_KEY` em respostas, logs, testes ou documentos. O `.env` está no `.gitignore`.
- **Custo zero.** Provedor de IA em produção: **Groq, plano gratuito**, modelo `openai/gpt-oss-20b` (os Llama não estão no plano gratuito). No computador:
  `mock`, `groq` ou `ollama`. Não sugira nada que exija pagamento ou cartão. O provedor `custom` é só
  saída de emergência. (Groq, com "q", é uma empresa de chips de IA; não é o Grok do X/Elon Musk.)
- Ao terminar uma etapa, atualize a seção "Situação atual" do `GUIA-DO-PROJETO.md`.

## Comandos

```bash
python -m app                 # API em http://localhost:3001 (recarrega ao salvar)
python -m pytest              # testes
python -m scripts.ingest      # (re)gera rag/indice/indice.json a partir de rag/documentos
```

Sempre com o ambiente virtual ativado (`source .venv/bin/activate` no Mac/Linux,
`.venv\Scripts\activate` no Windows). Sem `.env`, a API sobe em modo `mock` (sem IA).

## Mapa do código

| Arquivo | O que faz |
| --- | --- |
| `app/config.py` | **Única** leitura de variáveis de ambiente. Variável nova → aqui **e** no `.env.example` |
| `app/server.py` | `create_app(settings)`: CORS, rotas, erros 404/500 em JSON `{"error": ...}` |
| `app/main.py` | `app` para o Uvicorn (Render). `app/__main__.py`: `python -m app` no computador |
| `app/routes/health.py` | `GET /api/health` |
| `app/routes/chat.py` | `POST /api/chat`: limite de uso → tamanho → validação → máscara → RAG → prompt → IA → SSE |
| `app/utils/privacy.py` | Mascara CPF, cartão e e-mail (igual ao frontend, com `re.ASCII`) |
| `app/utils/validation.py` | Valida a conversa; mensagens de erro do contrato |
| `app/utils/rate_limit.py` | 20 pedidos/min por IP, em memória; IP real via `X-Forwarded-For` com `TRUST_PROXY=1` |
| `app/utils/sse.py` | Formato `event: X\ndata: JSON\n\n` e cabeçalhos do streaming |
| `app/llm/client.py` | `/chat/completions` com `stream=true` (httpx); `reasoning_effort`; aviso se `finish_reason="length"`; modo `mock`; `LlmError` |
| `app/prompts/system.py` | Prompt de sistema + montagem do CONTEXTO com os trechos |
| `app/rag/` | `frontmatter`, `chunker` (~900 caracteres por seção), `keyword` (BM25), `store` (índice com recarga), `retriever` (citados pelo nome primeiro, máx. 2 por documento, corte em 40% da melhor nota) |
| `scripts/ingest.py` | Lê `rag/documentos/*.md` e grava `rag/indice/indice.json` |
| `tests/` | pytest. `conftest.py` tem `make_settings()` e `parse_sse()`. `test_rag_base.py` testa a busca na base real |

## Regras que NÃO podem ser quebradas

1. **Privacidade:** nunca registre no log o conteúdo das mensagens (nem em erro). Nada de banco de
   dados. O log de acesso do Uvicorn fica desligado (`--no-access-log`): só erros vão para o log.
2. **Mascarar** CPF, cartão e e-mail no servidor antes de mandar à IA, mesmo que o frontend já mande
   mascarado. As regex ficam iguais às do frontend (`frontend/src/lib/privacy.js`).
3. **Chave de API só em variável de ambiente.** Nunca no código, nos testes, nos documentos ou no Git.
   O `.env` está no `.gitignore`.
4. **Prompt:** as regras 3 a 7 de `app/prompts/system.py` são de segurança (não inventar, só links
   oficiais, não pedir dados, alertar golpes, não se passar pelo governo). Não remova nem enfraqueça.
5. **Contrato da API:** status, JSON, textos de erro, nomes e ordem dos eventos SSE são consumidos pelo
   `frontend/src/lib/chatApi.js`. Mudou o contrato → o frontend precisa mudar junto → avise a equipe.
6. **Mensagens para o aluno** em português simples, sem detalhe técnico. Detalhe técnico só no log.
7. **Código em inglês** (nomes de variáveis, funções, arquivos); **comentários, mensagens e textos em
   português**.
8. **RAG:** toda informação dos documentos precisa de fonte oficial no campo `fonte`. Não invente
   valores, prazos ou endereços. Documentos novos começam com `status: rascunho`.

## Antes de dizer que terminou

- `python -m pytest` passando. Lógica nova → teste novo (os testes são a documentação viva do contrato).
- Mudou algo que a equipe precisa saber? Atualize o `GUIA-DO-PROJETO.md` e o doc da área em `docs/`.
- Mudou variável de ambiente? Atualize `app/config.py`, `.env.example` e `docs/DEPLOY.md`.

## Documentação

- [`GUIA-DO-PROJETO.md`](GUIA-DO-PROJETO.md): resumo, decisões, situação atual (comece aqui)
- [`docs/CONTEXTO.md`](docs/CONTEXTO.md): o projeto de extensão, os cinco eixos e os conceitos da apresentação
- [`docs/CONTRATO-API.md`](docs/CONTRATO-API.md): o que o frontend espera, campo a campo
- [`docs/ARQUITETURA.md`](docs/ARQUITETURA.md): fluxo de uma pergunta e por que cada escolha
- [`docs/RAG.md`](docs/RAG.md): como escrever documentos e rodar a ingestão
- [`docs/IA.md`](docs/IA.md): provedores de IA (Groq e Ollama) e escolha do modelo
- [`docs/DEPLOY.md`](docs/DEPLOY.md): publicar e ligar ao site
