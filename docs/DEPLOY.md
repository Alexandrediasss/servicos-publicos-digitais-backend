# Publicação

Tudo gratuito e sempre no ar, sem depender de computador ligado:

| Parte | Onde | Quem publica |
| --- | --- | --- |
| Site (frontend) | Netlify | A dona do repositório do site |
| Esta API | Render, plano gratuito (Web Service) | Quem cuida do backend |
| IA (`openai/gpt-oss-20b`, open source) | Groq, plano gratuito | Quem cuida do backend (só cria a chave) |

```
Aluno ──▶ Site (Netlify) ──▶ API (Render) ──▶ IA open source (Groq)
```

## 1. Criar a chave da Groq

Siga a seção "Groq" de [IA.md](IA.md). Guarde a chave: ela vai só no painel do Render.

## 2. Publicar a API no Render

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
   | `LLM_PROVIDER` | `groq` |
   | `LLM_API_KEY` | a chave da Groq (**só aqui**, nunca no código) |
   | `CORS_ORIGIN` | endereço do site, sem `/` no final (ex.: `https://guia-cidadao-digital.netlify.app`) |
   | `TRUST_PROXY` | `1` |
   | `LLM_MODEL` | opcional: deixe vazio (usa `openai/gpt-oss-20b`) ou `openai/gpt-oss-120b` |
   | `LLM_MAX_TOKENS` / `LLM_REASONING_EFFORT` | opcional: deixe vazio (padrões `1500` / `low`, ver [IA.md](IA.md)) |

   O Render define a `PORT` sozinho.

5. Clique em **Create Web Service**. Em alguns minutos, abra `https://SEU-SERVICO.onrender.com/api/health`.
   Deve aparecer `"ok": true` e `"provider": "groq"`.

O Render publica de novo sozinho toda vez que algo entra na `main`. Se faltar a chave, a API não
liga e o log do Render mostra "LLM_API_KEY é obrigatório para o provedor groq".

## 3. Ligar o site à API (Netlify)

1. Na Netlify: **Site configuration → Environment variables → Add a variable**:
   `VITE_API_URL` = endereço da API no Render, **sem `/` no final** (ex.: `https://guia-api.onrender.com`).
2. **Deploys → Trigger deploy → Deploy site**. A variável só vale depois de um novo deploy.
3. No Render, confira se `CORS_ORIGIN` tem o endereço exato do site.

Isso é feito uma vez só. O site não precisa de nenhuma outra mudança.

## O Render "dorme"

No plano gratuito, a API desliga sozinha depois de uns 15 minutos sem uso. A próxima chamada a acorda,
mas pode demorar cerca de 1 minuto; nesse meio-tempo, a aba pode mostrar "Assistente fora do ar no
momento" e o botão de tentar de novo resolve. **No dia da apresentação, abra o assistente alguns
minutos antes** e faça uma pergunta de teste.

## Limite da Groq no dia da palestra

O plano gratuito aguenta cerca de **6 perguntas por minuto para o site todo** (8.000 tokens por minuto;
com `reasoning_effort=low` cada pergunta gasta menos, então na prática sobra um pouco mais). Se a turma
inteira perguntar ao mesmo tempo, parte dos alunos vai ver "Muita gente perguntando agora. Espere um
minuto e tente de novo.". Recomendação:

- Testar o assistente **em grupos pequenos** (ex.: uma pergunta por dupla, uma dupla de cada vez).
- Abrir o assistente alguns minutos antes (o Render "dorme").
- Ter perguntas de exemplo prontas, que já foram testadas.

## Checklist

- [ ] `https://SUA-API/api/health` responde `"ok": true` e `"provider": "groq"`.
- [ ] No site publicado, uma pergunta é respondida aos poucos e mostra "Fontes consultadas".
- [ ] Nenhuma chave aparece em arquivo do repositório.

## Problemas comuns

| Sintoma | O que fazer |
| --- | --- |
| Site mostra "Assistente fora do ar no momento" | A API está acordando ou caiu. Abra `/api/health` e espere. Confira `VITE_API_URL` (sem `/` no final, com novo deploy) e `CORS_ORIGIN` |
| Site mostra "O assistente está indisponível agora" | A API está no ar, mas a Groq recusou. Veja os **Logs** no Render: `401` = chave errada; `429` = limite gratuito; `404` = modelo errado. Detalhes em [IA.md](IA.md) |
| Build falha no Render | Confira o log: versão do Python (3.12) e se o `requirements.txt` está na raiz |
| Deploy falha com "LLM_API_KEY é obrigatório" | Falta a variável `LLM_API_KEY` no Render |
