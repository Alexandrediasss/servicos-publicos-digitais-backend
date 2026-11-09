# Publicação

| Parte | Onde | Quem publica |
| --- | --- | --- |
| Site (frontend) | Netlify | A dona do repositório do site |
| Esta API | Render, plano gratuito (Web Service) | Quem cuida do backend |
| IA (Ollama + Llama) | **Computador da equipe** (ver abaixo) | Quem for apresentar |

## O problema: o Ollama não cabe no plano gratuito

O plano gratuito do Render tem pouca memória (cerca de 512 MB) e não tem placa de vídeo. O modelo
`llama3.1:8b` precisa de ~8 GB. Então **a API vai para o Render, mas o Ollama não**.

Opções para o Ollama em produção, todas gratuitas:

| Opção | Como funciona | Prós | Contras |
| --- | --- | --- | --- |
| **A. Ollama no notebook + túnel** (recomendada) | A API fica no Render. O Ollama roda no notebook da equipe e um túnel gratuito da Cloudflare dá um endereço público para ele | Grátis, sem cartão, usa o Llama, rápido se o notebook for bom | O assistente só funciona com o notebook ligado; o endereço do túnel muda a cada vez |
| B. Tudo no notebook + túnel | API e Ollama no notebook; o túnel expõe a API | Não precisa do Render | O endereço muda a cada vez → a Netlify precisa de novo deploy toda vez |
| C. Máquina virtual gratuita na nuvem | Ex.: o plano "Always Free" da Oracle Cloud tem máquinas com memória suficiente | Fica ligado sempre | Configuração mais difícil, pede cartão para cadastro, lento sem placa de vídeo |

Com a opção A, quando o notebook está desligado, a aba do assistente mostra "O assistente está
indisponível agora" (o resto do site funciona normalmente).

## 1. Publicar a API no Render

1. Entre em https://render.com com a conta do GitHub.
2. **New → Web Service** e escolha este repositório.
3. Preencha:

   | Campo | Valor |
   | --- | --- |
   | Language / Runtime | Python 3 |
   | Branch | `main` |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT --no-access-log` |
   | Instance Type | Free |
   | Health Check Path (em Advanced) | `/api/health` |

   A versão do Python vem do arquivo `.python-version` (3.12). Confira no log do build que ele usou
   Python 3.12; se não usou, crie a variável `PYTHON_VERSION` com a versão completa (ex.: `3.12.12`).

4. Variáveis de ambiente (**Environment**):

   | Variável | Valor |
   | --- | --- |
   | `LLM_PROVIDER` | `ollama` (ou `mock` enquanto o túnel não estiver pronto) |
   | `LLM_BASE_URL` | endereço do túnel + `/v1` (ver passo 2) |
   | `LLM_MODEL` | `llama3.1:8b` |
   | `CORS_ORIGIN` | endereço do site, sem `/` no final (ex.: `https://guia-cidadao-digital.netlify.app`) |
   | `TRUST_PROXY` | `1` |

   O Render define a `PORT` sozinho. **Não** coloque chaves de API no código: só aqui.

5. Clique em **Create Web Service**. Em alguns minutos, abra `https://SEU-SERVICO.onrender.com/api/health`.
   Deve aparecer `"ok": true`.

O Render publica de novo sozinho toda vez que algo entra na `main`.

## 2. Ligar o Ollama do notebook (opção A)

Faça isso no notebook de quem vai apresentar, um pouco antes de usar:

1. Abra o Ollama e confira se o modelo está baixado: `ollama list` (senão, `ollama pull llama3.1:8b`).
2. Instale o `cloudflared` (gratuito, sem conta):
   https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
   (no Mac: `brew install cloudflared`).
3. Abra o túnel:

   ```bash
   cloudflared tunnel --url http://localhost:11434 --http-host-header="localhost:11434"
   ```

   O `--http-host-header` é necessário porque o Ollama recusa pedidos que não pareçam vir do próprio
   computador. O terminal mostra um endereço como `https://palavras-aleatorias.trycloudflare.com`.
4. No Render, mude `LLM_BASE_URL` para esse endereço **+ `/v1`**
   (ex.: `https://palavras-aleatorias.trycloudflare.com/v1`) e salve. O Render reinicia a API.
5. Teste uma pergunta no site.

Deixe o terminal do túnel e o Ollama abertos enquanto o assistente estiver em uso.

> **Atenção:** enquanto o túnel está aberto, qualquer pessoa que descobrir o endereço consegue usar o
> Ollama do notebook. O endereço é aleatório e muda a cada vez, então o risco é pequeno, mas **feche o
> túnel (Ctrl+C) quando terminar**.

## 3. Ligar o site à API (Netlify)

1. Na Netlify: **Site configuration → Environment variables → Add a variable**:
   `VITE_API_URL` = endereço da API no Render, **sem `/` no final** (ex.: `https://guia-api.onrender.com`).
2. **Deploys → Trigger deploy → Deploy site**. A variável só vale depois de um novo deploy.
3. No Render, confira se `CORS_ORIGIN` tem o endereço do site.

O endereço do Render não muda, então isso é feito **uma vez só**, mesmo com o túnel mudando.

## Dia da apresentação

- [ ] Notebook ligado na tomada, Ollama aberto, `ollama list` mostra o modelo.
- [ ] Túnel aberto e `LLM_BASE_URL` atualizado no Render.
- [ ] O plano gratuito do Render "dorme" quando fica parado: a primeira chamada pode demorar ~1
      minuto. **Abra o assistente alguns minutos antes** e faça uma pergunta de teste.
- [ ] `https://SUA-API/api/health` mostra `"provider": "ollama"`.

## Problemas comuns

| Sintoma | O que fazer |
| --- | --- |
| Site mostra "Assistente fora do ar no momento" | A API caiu ou está acordando. Abra `/api/health` e espere. Confira `VITE_API_URL` (sem `/` no final, com novo deploy) e `CORS_ORIGIN` |
| Site mostra "O assistente está indisponível agora" | A API está no ar, mas não alcança o Ollama. Confira se o notebook, o Ollama e o túnel estão abertos e se `LLM_BASE_URL` termina em `/v1`. O log do Render mostra o detalhe |
| Log do Render mostra `403` | Faltou o `--http-host-header="localhost:11434"` no túnel |
| Build falha no Render | Confira o log: versão do Python (3.12) e se o `requirements.txt` está na raiz |
