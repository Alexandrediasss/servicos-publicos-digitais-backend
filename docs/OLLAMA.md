# Ollama: a IA do assistente

O [Ollama](https://ollama.com) é um programa gratuito que roda modelos de IA open source, como o
**Llama** (da Meta), no próprio computador. A API conversa com ele pelo endereço
`http://localhost:11434/v1`, no mesmo formato da API da OpenAI.

## Instalar

1. Baixe e instale: https://ollama.com/download (Windows, Mac ou Linux).
2. Baixe o modelo do projeto (cerca de 5 GB, só na primeira vez):

   ```bash
   ollama pull llama3.1:8b
   ```

3. No `.env` da API: `LLM_PROVIDER=ollama`.
4. Rode a API (`python -m app`). O terminal mostra `IA: ollama (llama3.1:8b)`.

O Ollama precisa estar aberto (no Windows, o ícone fica perto do relógio; no Mac, na barra de cima).
Para conferir se ele está funcionando:

```bash
ollama list
```

## Qual modelo usar

| Modelo | Tamanho | Memória livre | Quando usar |
| --- | --- | --- | --- |
| `llama3.1:8b` (padrão) | ~5 GB | ~8 GB | Melhor qualidade em português entre os Llama que rodam em notebook |
| `llama3.2:3b` | ~2 GB | ~4 GB | Computador mais fraco. Responde mais rápido, mas erra mais |

Para trocar, baixe o modelo (`ollama pull llama3.2:3b`) e coloque no `.env`:
`LLM_MODEL=llama3.2:3b`.

Velocidade: com placa de vídeo (ou Mac com chip M), a resposta sai em poucos segundos. Só com o
processador, pode levar de 10 a 60 segundos. Por isso a resposta aparece aos pedaços no site.

## Problemas comuns

| Sintoma no site | Causa provável | O que fazer |
| --- | --- | --- |
| "O assistente está indisponível agora" | O Ollama está fechado | Abra o Ollama e confira com `ollama list` |
| "O assistente está indisponível agora" e o log da API diz `404` / `model not found` | O modelo não foi baixado | `ollama pull llama3.1:8b` (ou o modelo do `LLM_MODEL`) |
| Resposta muito lenta | Modelo grande rodando só no processador | Use `llama3.2:3b` |
| "Assistente fora do ar no momento" | A API não está rodando | Rode `python -m app` e abra http://localhost:3001/api/health |

O detalhe técnico de cada erro aparece no terminal da API (nunca no site).

## Ollama em outra máquina

A API não precisa estar no mesmo computador que o Ollama. Basta apontar `LLM_BASE_URL` para o
endereço do Ollama terminado em `/v1` (ex.: `LLM_BASE_URL=https://endereco-do-tunel/v1`). É assim
que a API publicada no Render usa o Ollama do computador da equipe: veja [DEPLOY.md](DEPLOY.md).

## E o "Ollama Cloud"?

O Ollama também vende modelos na nuvem (https://ollama.com/pricing). Conferido em 2026-11-08: é pago
por uso (não há uso gratuito incluído) e a lista de modelos na nuvem não tem Llama. Por isso **não
usamos**. Se um dia mudar, basta `LLM_BASE_URL=https://ollama.com/v1`, `LLM_API_KEY` e `LLM_MODEL`
com um modelo da lista.
