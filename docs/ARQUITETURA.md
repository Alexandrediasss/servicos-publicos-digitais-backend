# Arquitetura

## Visão geral

```
 Celular do aluno               Esta API (FastAPI)                       Groq (ou Ollama)
┌──────────────────┐ /api/chat ┌───────────────────────────────────┐   ┌────────────────┐
│ Site (React)     │ ────────▶ │ 1. limite de uso (20/min por IP)  │   │ IA open source │
│ aba "Qual serviço│           │ 2. tamanho (32 KB) e validação    │   │ gpt-oss-20b    │
│ eu preciso?"     │           │ 3. mascara CPF, cartão, e-mail    │──▶│                │
│                  │ ◀──────── │ 4. RAG: busca 4 trechos (BM25)    │◀──│ /v1/chat/      │
│ chatApi.js       │  SSE:     │ 5. monta o prompt                 │   │ completions    │
└──────────────────┘  meta,    │ 6. repassa a resposta aos pedaços │   └────────────────┘
                      token...,└───────────────────────────────────┘
                      done/error          ▲
                                          │ lê (recarrega se mudar)
                                 rag/indice/indice.json ◀── python -m scripts.ingest ◀── rag/documentos/*.md
```

## Fluxo de uma pergunta (`app/routes/chat.py`)

1. `RateLimiter.hit(client_ip(...))`: passou de 20 pedidos no minuto → `429`.
2. `read_body_limited`: corpo maior que 32 KB → `413` (para de ler assim que passa do limite).
3. `validate_messages`: confere o formato, limpa, corta em 1000 caracteres, fica com as 8 últimas → `400` se inválido.
4. `mask_sensitive` em cada mensagem: troca CPF, cartão e e-mail por marcadores.
5. `IndexStore.load()` + `retrieve()`: os 4 trechos com maior nota BM25 para a **última** pergunta.
6. `build_messages`: mensagem `system` (regras + CONTEXTO com os trechos) + histórico.
7. `StreamingResponse(event_stream(...))`:
   - `meta` com as fontes (sem repetir documento);
   - `stream_chat()` chama `{LLM_BASE_URL}/chat/completions` com `stream=true` e repassa cada pedaço
     como `token`;
   - `done` no fim, ou `error` se a IA falhar.
8. Se a conexão cai ("Parar" ou página fechada), o Uvicorn cancela o gerador; o `async with` do httpx
   fecha o pedido à IA, que para de gerar. Testado com o Ollama: ele registra "cancel task" na hora.

## Por que essas escolhas

- **Formato OpenAI** (`/chat/completions`): a Groq e o Ollama (em `/v1`) aceitam, e quase todo provedor também.
  Trocar de modelo ou de máquina é só mudar `LLM_MODEL` e `LLM_BASE_URL`.
- **Server-Sent Events:** um modelo rodando em computador comum pode levar de 10 a 60 segundos.
  Mostrar o texto aos poucos evita a impressão de que travou.
- **BM25 e índice em JSON:** a base tem dezenas de documentos. Banco vetorial seria exagero. A busca
  ignora acentos, maiúsculas, plural e palavras vazias ("de", "para", "quero"...), e o título do
  documento vale em dobro.
- **`create_app(settings)`:** a aplicação recebe a configuração pronta. Os testes criam APIs com
  configurações diferentes (limite menor, índice de teste, provedor simulado) sem mexer no `.env`.
- **Sem banco de dados e sem log de acesso:** nada a proteger = nada a vazar. O público é menor de idade.

## Privacidade, ponto a ponto

| Onde | O que acontece |
| --- | --- |
| Site | Mascara CPF, cartão e e-mail antes de enviar |
| API (entrada) | Mascara de novo (`app/utils/privacy.py`) |
| API (log) | Só erros técnicos (status, tipo do erro). Nunca o conteúdo. Log de acesso desligado |
| API (memória) | O IP fica no máximo 1 minuto, só para o limite de uso |
| Groq | Recebe a conversa já mascarada (é um serviço de terceiros). Com o Ollama no computador, nada sai da máquina |

## Pontos de extensão

- **Embeddings** (busca por significado): implementar em `app/rag/retriever.py`, com `retrieval =
  "embeddings"` no evento `meta` e voltando para BM25 se o servidor de embeddings falhar.
- **Outro provedor**: `LLM_PROVIDER=custom` + `LLM_BASE_URL` + `LLM_MODEL` (+ `LLM_API_KEY`).
  Nenhum código muda.
