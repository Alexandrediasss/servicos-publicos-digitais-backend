# API do Guia do Cidadão Digital

API do assistente **"Qual serviço eu preciso?"** do site Guia do Cidadão Digital, do projeto de
extensão **Inclusão Digital: Acesso aos Serviços Públicos Digitais** (Sistemas de Informação, 2026.2).

Ela recebe a pergunta do aluno, esconde dados pessoais, busca trechos na base de conhecimento (RAG)
e pede a resposta a um modelo **Llama** rodando no **Ollama**. A resposta volta aos pedaços para o site.

- Site (frontend): https://github.com/MariaLuiza007-Teo/servicos-publicos-digitais
- Contexto do projeto: [GUIA-DO-PROJETO.md](GUIA-DO-PROJETO.md)

## Como rodar no seu computador

### 1. Instale o que precisa (só na primeira vez)

- **Python 3.12**
  - Windows: baixe em https://www.python.org/downloads/ e, na instalação, marque **"Add python.exe to PATH"**.
  - Mac: `brew install python@3.12` (com o [Homebrew](https://brew.sh)) ou o instalador de python.org.
- **Git:** https://git-scm.com
- **Ollama** (para a IA de verdade): https://ollama.com/download. Detalhes em [docs/OLLAMA.md](docs/OLLAMA.md).

### 2. Baixe o projeto e crie o ambiente virtual

O ambiente virtual (`.venv`) é uma pasta com as bibliotecas só deste projeto.

**Mac / Linux:**

```bash
cd servicos-publicos-digitais-backend
```

```bash
python3.12 -m venv .venv
```

```bash
source .venv/bin/activate
```

```bash
pip install -r requirements-dev.txt
```

**Windows (PowerShell):**

```powershell
cd servicos-publicos-digitais-backend
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
```

> Se o PowerShell disser que "a execução de scripts foi desabilitada", rode uma vez
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` e tente ativar de novo.

Toda vez que abrir um terminal novo para trabalhar no projeto, **ative o ambiente virtual** de novo
(`source .venv/bin/activate` ou `.venv\Scripts\activate`). O terminal mostra `(.venv)` no começo da linha.

### 3. Configure

Copie o `.env.example` para `.env` (no Windows, copie pelo Explorer e renomeie).

```bash
cp .env.example .env
```

O `.env.example` já vem com `LLM_PROVIDER=ollama`. Se ainda não instalou o Ollama, troque para
`LLM_PROVIDER=mock`: a API responde um texto de demonstração, sem IA.

### 4. Rode

```bash
python -m app
```

Abra http://localhost:3001/api/health. Deve aparecer `"ok": true`.

## Testes

```bash
python -m pytest
```

## Base de conhecimento (RAG)

Depois de criar ou mudar um documento em `rag/documentos/`:

```bash
python -m scripts.ingest
```

Com a API ligada, o índice recarrega sozinho. Passo a passo em [docs/RAG.md](docs/RAG.md).

## Testar junto com o site

1. Rode esta API (`python -m app`), que fica na porta 3001.
2. No repositório do site, rode **só o site** (o `npm run dev` sobe também a API antiga em Node na
   mesma porta):

   ```bash
   npm run dev:web
   ```

3. Abra http://localhost:5173/assistente.

## Publicar

Veja [docs/DEPLOY.md](docs/DEPLOY.md).

## Documentação

- [GUIA-DO-PROJETO.md](GUIA-DO-PROJETO.md): resumo, regras, decisões e situação atual (comece por aqui)
- [AGENTS.md](AGENTS.md): instruções para assistentes de IA (Claude, Copilot, Cursor...)
- [docs/CONTRATO-API.md](docs/CONTRATO-API.md): o que o site espera da API
- [docs/ARQUITETURA.md](docs/ARQUITETURA.md): como as partes se conectam
- [docs/RAG.md](docs/RAG.md): como escrever os documentos da base
- [docs/OLLAMA.md](docs/OLLAMA.md): instalar o Ollama e escolher o modelo
- [docs/DEPLOY.md](docs/DEPLOY.md): publicar no Render e ligar ao site

> Este não é um serviço do governo. O assistente apenas orienta e indica os canais oficiais.
