# Contrato da API

O site chama esta API por `frontend/src/lib/chatApi.js` (no repositório do site), usando o endereço em
`VITE_API_URL`. **O site não pode precisar mudar**: esta API segue o contrato exatamente.

> Mudou alguma coisa aqui (status, campo, texto de erro, nome ou ordem de evento)? O `chatApi.js`
> precisa mudar junto. Combine com quem cuida do site **antes**.

Os testes em `tests/test_api.py` conferem cada item deste documento.

## `GET /api/health`

Resposta `200`, JSON:

```json
{
  "ok": true,
  "llm": { "provider": "groq", "model": "openai/gpt-oss-20b" },
  "rag": {
    "ready": true,
    "documents": 13,
    "chunks": 75,
    "createdAt": "2026-11-08T12:00:00Z",
    "retriever": "palavras-chave"
  }
}
```

| Campo | Como o site usa |
| --- | --- |
| `llm.provider` | `"mock"` → mostra "Modo de demonstração (sem IA conectada)" |
| `llm.model` | Senão → mostra "Assistente conectado · <modelo>" |
| `rag.ready` | `false` → acrescenta "base de conhecimento em construção" |
| (falha ou resposta sem JSON) | Mostra "Assistente fora do ar no momento" e um botão de tentar de novo |

Sem índice, `rag` fica `{"ready": false, "documents": 0, "chunks": 0, "createdAt": null, "retriever": "palavras-chave"}`.

## `POST /api/chat`

### Pedido

`Content-Type: application/json`, corpo de até 32 KB:

```json
{ "messages": [
  { "role": "user", "content": "Vou fazer o ENEM. O que eu preciso?" },
  { "role": "assistant", "content": "..." },
  { "role": "user", "content": "..." }
] }
```

O site já manda o texto mascarado, mas a API **mascara de novo** (não confia no site).

### Erros antes de responder

Sempre JSON `{"error": "..."}`. O site mostra o `error` **direto para o aluno**.

| Situação | Status | `error` |
| --- | --- | --- |
| `messages` ausente, não é lista, vazia (ou JSON quebrado) | 400 | `Envie a conversa no campo "messages".` |
| Mais de 40 mensagens | 400 | `Conversa longa demais. Comece uma nova.` |
| `role` diferente de `user`/`assistant` ou `content` que não é texto | 400 | `Formato de mensagem inválido.` |
| Depois de limpar, a última mensagem não é do usuário | 400 | `A última mensagem precisa ser da pessoa usuária.` |
| Corpo maior que 32 KB | 413 | `Sua mensagem ficou grande demais. Tente resumir.` |
| Mais de 20 pedidos por minuto do mesmo IP | 429 | `Muitas perguntas em pouco tempo. Espere um minuto e tente de novo.` |
| Rota que não existe | 404 | `Rota não encontrada.` |

Limpeza: cada `content` passa por trim e é cortado em 1000 caracteres; mensagens vazias são
descartadas; só as **8 últimas** seguem para a IA.

O limite de uso conta todos os pedidos ao `/api/chat`, inclusive os inválidos. No Render, o IP real
vem do cabeçalho `X-Forwarded-For` (com `TRUST_PROXY=1`).

### Resposta normal: Server-Sent Events

Status `200` com os cabeçalhos:

```
Content-Type: text/event-stream; charset=utf-8
Cache-Control: no-cache, no-transform
Connection: keep-alive
X-Accel-Buffering: no
```

Cada evento é exatamente `event: NOME\ndata: JSON-EM-UMA-LINHA\n\n`, nesta ordem:

1. **`meta`** (uma vez, antes de qualquer texto):

   ```json
   {
     "sources": [{ "title": "ENEM — inscrição, isenção e resultados", "url": "https://www.gov.br/inep/...", "category": "educacao" }],
     "retrieval": "palavras-chave",
     "ragReady": true,
     "masked": ["cpf"]
   }
   ```

   - `sources`: documentos de onde vieram os trechos usados, **sem repetir documento**. Viram a lista
     "Fontes consultadas" embaixo da resposta. `url` e `category` podem ser `null`.
   - `retrieval`: `"palavras-chave"` | `"embeddings"` (ainda não existe) | `"sem-base"` (índice vazio).
   - `ragReady`: `false` quando a base está vazia.
   - `masked`: tipos mascarados na conversa: `"cpf"`, `"cartao"`, `"email"`.

2. **`token`** (várias vezes, conforme o modelo escreve; texto em Markdown): `{"text": "pedaço"}`

3. Fim:
   - **`done`**: `{}`, fim normal; **ou**
   - **`error`**: fim com erro no meio do caminho:
     - `{"message": "O assistente está indisponível agora. Tente de novo em alguns minutos."}` quando
       o provedor de IA falha, demora demais ou recusa;
     - `{"message": "Muita gente perguntando agora. Espere um minuto e tente de novo."}` quando o
       provedor de IA responde que passou do limite de uso (HTTP 429 do provedor);
     - `{"message": "Algo deu errado ao gerar a resposta."}` para qualquer outro erro.

Exemplo real:

```
event: meta
data: {"sources":[],"retrieval":"sem-base","ragReady":false,"masked":[]}

event: token
data: {"text":"Para o ENEM, "}

event: token
data: {"text":"você precisa..."}

event: done
data: {}
```

Se o provedor cortar a resposta por tamanho, o último `token` antes do `done` é o aviso
`"\n\n_(A resposta ficou longa demais e foi cortada. Tente perguntar sobre um assunto de cada vez.)_"`.
É texto comum em Markdown: o site não precisa tratar.

### Outras regras do `/api/chat`

- Se o aluno fecha a página ou clica em "Parar", a conexão cai e a API **para de chamar a IA** (o
  pedido à IA é cancelado).
- Detalhes técnicos de erro vão só para o log do servidor, nunca para o aluno.
- **Nunca** registrar no log o conteúdo das perguntas.

## CORS

Libera as origens da variável `CORS_ORIGIN` (lista separada por vírgula, sem `/` no final).
Padrão: `http://localhost:5173`. Em produção: o endereço do site na Netlify
(ex.: `https://guia-cidadao-digital.netlify.app`). Métodos `GET` e `POST`, cabeçalho `Content-Type`.

## Testar com o site no computador

No repositório do site, o Vite encaminha `/api` para `http://localhost:3001`. Então:

1. Rode esta API: `python -m app` (porta 3001).
2. No site, rode **só o site**: `npm run dev:web` (não use `npm run dev`, que sobe também a API antiga
   em Node na mesma porta).
3. Abra http://localhost:5173/assistente e confira:
   - [ ] A barra de status mostra "Assistente conectado · <modelo>" (ou "Modo de demonstração" no mock).
   - [ ] A resposta aparece aos poucos.
   - [ ] "Fontes consultadas" aparece embaixo da resposta.
   - [ ] "Parar" interrompe a resposta.
   - [ ] Com a IA fora do ar (ex.: chave errada ou Ollama fechado), aparece "O assistente está indisponível agora..." em português.
