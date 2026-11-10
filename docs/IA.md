# A IA do assistente: Groq e Ollama

A API fala com qualquer serviço de IA no formato da API da OpenAI (`/chat/completions`). Trocar de
provedor ou de modelo é só mudar variáveis de ambiente; o código não muda.

| `LLM_PROVIDER` | Onde a IA roda | Custo | Quando usar |
| --- | --- | --- | --- |
| `mock` | Em lugar nenhum (texto de demonstração) | Grátis | Testar o site sem IA |
| `groq` | Nos servidores da Groq | **Plano gratuito, sem cartão** | **Site publicado** e testes no computador |
| `ollama` | No seu computador | Grátis | Testar sem internet ou sem mandar nada para terceiros |
| `custom` | Qualquer API compatível com a OpenAI | Depende | Saída de emergência |

> **Groq ≠ Grok.** A **Groq** (com "q", https://groq.com) é uma empresa que faz chips para rodar IA e
> oferece modelos open source pela internet. O **Grok** (com "k") é o chatbot da xAI,
> de Elon Musk, que aparece no X. São coisas diferentes.

## Groq (produção)

1. Crie uma conta em https://console.groq.com (pode entrar com o Google ou o GitHub; não pede cartão).
2. Em https://console.groq.com/keys, clique em **Create API Key** e copie a chave.
3. No `.env` (computador) ou nas variáveis do Render (produção):

   ```
   LLM_PROVIDER=groq
   LLM_API_KEY=cole_a_chave_aqui
   ```

4. Rode a API. O terminal mostra `IA: groq (openai/gpt-oss-20b)`.

**A chave é um segredo.** Nunca coloque no código, no frontend, em print ou no Git. Se vazar, apague
no painel da Groq e crie outra. Quem tiver a chave consegue gastar o limite gratuito da equipe.

### Qual modelo usar na Groq

**Os modelos Llama não estão no plano gratuito da Groq.** Testado em 2026-11-09 com a chave da equipe:
`llama-3.3-70b-versatile` e `llama-3.1-8b-instant` respondem "model not found". Por isso o padrão é o
**`openai/gpt-oss-20b`**: um modelo **open source** (licença Apache 2.0) lançado pela OpenAI, que
qualquer pessoa pode baixar e rodar. Não é o ChatGPT.

| Modelo (plano gratuito) | Resultado no teste ("SMS dizendo que o CPF vai ser cancelado") |
| --- | --- |
| `openai/gpt-oss-20b` (padrão) | Identificou o golpe, mandou para o site oficial da Receita e para a aba "Esse link é oficial?". ~1 s |
| `openai/gpt-oss-120b` | Também bom, mais longo, mas sugeriu Procon e "avisar a Receita" (fora do contexto). ~1,3 s |
| `qwen/qwen3.8-27b` | Bom e curto, mas é um modelo em "preview" na Groq (pode sair do ar). Não usar em produção |

Para ver os modelos que a sua chave libera:

```bash
curl -s https://api.groq.com/openai/v1/models -H "Authorization: Bearer SUA_CHAVE"
```

Para trocar: `LLM_MODEL=openai/gpt-oss-120b`.

**Limites do plano gratuito** (medidos em 2026-11-09 nos cabeçalhos da resposta, iguais para os dois
gpt-oss): **1.000 pedidos por dia** e **8.000 tokens por minuto** (token ≈ pedaço de palavra). Cada
pergunta do site gasta uns **1.300 tokens** (regras + trechos do RAG + resposta), então o site todo
aguenta umas **6 perguntas por minuto**. Os números podem mudar: confira em
https://console.groq.com/settings/limits. Quando o limite estoura, a Groq responde `429` e o site
mostra "O assistente está indisponível agora. Tente de novo em alguns minutos.".

Na apresentação, se muitos alunos perguntarem ao mesmo tempo, o limite de tokens por minuto é o que
estoura primeiro: algumas respostas vão falhar até o minuto virar.

**Privacidade.** Com a Groq, a pergunta (já sem CPF, cartão e e-mail) é processada por uma empresa de
fora. Por isso a API mascara tudo antes de enviar e nunca grava as perguntas.

## Ollama (opcional, no computador)

O [Ollama](https://ollama.com) roda o Llama no próprio computador, sem internet e sem chave.

1. Instale: https://ollama.com/download
2. Baixe o modelo (cerca de 5 GB, só na primeira vez):

   ```bash
   ollama pull llama3.1:8b
   ```

   Computador mais fraco? `ollama pull llama3.2:3b` e `LLM_MODEL=llama3.2:3b` no `.env`.
3. No `.env`: `LLM_PROVIDER=ollama`.

O Ollama precisa estar aberto (`ollama list` confere). Sem placa de vídeo, cada resposta pode levar de
10 a 60 segundos.

**Por que o Ollama não vai para o site publicado:** o plano gratuito do Render tem cerca de 512 MB de
memória e o `llama3.1:8b` precisa de uns 8 GB. Até modelos bem pequenos não cabem ou ficam lentos
demais, e escrevem mal em português. Rodar no computador da equipe exigiria deixá-lo ligado o tempo
todo.

## Problemas comuns

| Sintoma no site | Causa provável | O que fazer |
| --- | --- | --- |
| "Assistente fora do ar no momento" | A API não está rodando (ou está acordando no Render) | Abra `/api/health` e espere |
| "O assistente está indisponível agora" + log `401` | Chave da Groq errada ou apagada | Confira `LLM_API_KEY` |
| "O assistente está indisponível agora" + log `429` | Limite do plano gratuito da Groq | Espere o minuto virar (ou o dia, se passou de 1.000 pedidos) |
| "O assistente está indisponível agora" + log `404` / `model not found` | Nome do modelo errado (ou modelo saiu do ar na Groq) | Confira a lista em https://console.groq.com/docs/models |
| "O assistente está indisponível agora" com Ollama | Ollama fechado ou modelo não baixado | Abra o Ollama; `ollama pull llama3.1:8b` |
| A API nem liga: "LLM_API_KEY é obrigatório para o provedor groq" | Falta a chave | Coloque `LLM_API_KEY` no `.env` ou no Render |

O detalhe técnico de cada erro aparece no terminal da API (ou nos Logs do Render), nunca no site.
