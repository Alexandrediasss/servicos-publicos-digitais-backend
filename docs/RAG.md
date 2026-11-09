# RAG: a base de conhecimento do assistente

RAG (Retrieval-Augmented Generation) = antes de responder, a API **busca trechos** nos nossos
documentos e manda para a IA junto com a pergunta. Assim a IA responde com base em informação
conferida, e não só no que "lembra". **A IA repete o que estiver escrito**: por isso todo documento
precisa de fonte oficial.

```
rag/documentos/*.md  ──(python -m scripts.ingest)──▶  rag/indice/indice.json  ──▶  API
```

## O que pesquisar para alimentar a base

Para cada serviço, abra a **fonte oficial** e confira:

1. **Para que serve**: o que o serviço resolve, em uma ou duas frases.
2. **Quem pode usar**: idade, situação, regras de renda.
3. **Onde acessar**: site oficial (termina em `.gov.br`, `.jus.br`, `.mil.br`...), aplicativo oficial e
   se precisa da conta gov.br (e de qual nível: bronze, prata ou ouro).
4. **O que dá para fazer**: as ações principais (consultar, emitir, pedir...).
5. **Cuidados**: o golpe ou erro mais comum. Lembrar que serviço público digital é gratuito.

Além disso:

- **Atendimento presencial em Manaus** (o documento que mais precisa de pesquisa): qual órgão
  cuida dos PACs e a página oficial com a lista de unidades e serviços; a página da Prefeitura com os
  CRAS e as UBS.
- **Perguntas reais dos alunos** (da palestra ou do formulário, **sem dados pessoais**): servem para
  testar se a busca acha o documento certo. Se não achar, acrescente no documento as palavras que os
  alunos usaram.

## Situação atual

Os 13 documentos da primeira carga existem, mas são **rascunhos** (`status: rascunho`). Lista e
fontes em [`rag/documentos/README.md`](../rag/documentos/README.md). Os pontos que mais precisam ser
conferidos estão marcados com `CONFERIR` nos comentários `<!-- -->` de cada arquivo.

## Como escrever um documento

1. Copie `rag/documentos/_MODELO.md` para um arquivo novo, sem o `_` (ex.: `enem.md`).
2. Preencha o cabeçalho:

   ```
   ---
   titulo: ENEM — inscrição, isenção e resultados
   fonte: https://www.gov.br/inep/pt-br/areas-de-atuacao/avaliacao-e-exames-educacionais/enem
   categoria: educacao
   atualizado_em: 2026-11-08
   status: rascunho
   ---
   ```

   | Campo | O que é |
   | --- | --- |
   | `titulo` | Aparece em "Fontes consultadas" embaixo da resposta |
   | `fonte` | Link oficial de onde a informação saiu (**obrigatório**) |
   | `categoria` | `educacao`, `trabalho`, `saude`, `cidadania`, `financas`, `seguranca` ou `geral` |
   | `atualizado_em` | Data em que alguém conferiu na fonte (AAAA-MM-DD) |
   | `status` | `rascunho` ou `revisado` |

3. Escreva com seções `##` (Para que serve, Quem pode usar, Onde acessar, O que dá para fazer,
   Cuidados).
4. Rode o ingest (com o ambiente virtual ativado):

   ```bash
   python -m scripts.ingest
   ```

5. Com a API ligada, o índice recarrega sozinho. Teste no site ou com `curl`.
6. Faça commit do documento **e** do `rag/indice/indice.json`.

## Regras para escrever

- **Toda informação com fonte oficial.** Sem fonte, não entra.
- **Linguagem simples**, frases curtas, "você". Termo técnico só explicado na mesma frase.
- **Use as palavras que os alunos usariam** ("vacina", "trabalho", "título de eleitor", "posto de
  saúde"), não só os nomes oficiais. A busca é por palavras: se o aluno escreve "vacina" e o documento
  só diz "imunização", a busca não acha.
- **Sem passo a passo de telas** (as telas do gov.br mudam muito): explique o que o serviço faz e mande
  para o link oficial.
- **Valores, prazos e datas** só com fonte e com o ano. Na dúvida, deixe de fora e mande conferir no
  site oficial. A IA está instruída a não inventar, mas repete o que o documento disser.
- **Nada de dados pessoais** nos documentos.
- **Um assunto por arquivo.** Arquivos pequenos e focados dão respostas mais precisas.
- Comentários `<!-- ... -->` **não vão para a IA**: use para anotar o que falta conferir.

## Como o ingest funciona

- Lê os `.md` e `.txt` de `rag/documentos/`, ignorando arquivos que começam com `_` e o `README.md`.
- Corta o texto em trechos de até ~900 caracteres, **respeitando as seções** `##`. Cada trecho guarda
  o título da seção. Se o último parágrafo de um trecho for curto (até 200 caracteres), ele se repete
  no começo do próximo, para não perder contexto.
- Avisa quando falta `titulo` ou `fonte`, quando a categoria não existe e quando o documento ainda é
  rascunho.
- Grava `rag/indice/indice.json` com os documentos, os trechos e a data de criação.

## Como a busca funciona (BM25)

- Normaliza o texto: minúsculas, sem acentos, sem palavras vazias ("de", "para", "quero", "preciso"...).
- "Stemming" simples: `inscrições → inscricao`, `mulheres → mulher`, `vacinas → vacina`.
- O título do documento conta duas vezes (ajuda a achar o documento certo).
- Pega os 4 trechos com maior nota (`RAG_TOP_K`). Se nenhum trecho tem palavra da pergunta, a IA
  recebe o aviso de que não há contexto e responde só com orientações gerais.

Para testar a busca sem a IA, rode na raiz do projeto:

```bash
python -c "from pathlib import Path; from app.rag.store import IndexStore; from app.rag.retriever import retrieve; r = retrieve(IndexStore(Path('rag/indice/indice.json')).load(), 'quero ver se tomei a vacina'); print([x.chunk['title'] for x in r.results])"
```
