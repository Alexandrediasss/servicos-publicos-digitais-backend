# Documentos da base de conhecimento (RAG)

Esta pasta guarda os textos que o assistente "Qual serviço eu preciso?" usa para responder.
O passo a passo completo está em [`docs/RAG.md`](../../docs/RAG.md).

## Resumo

1. Copie `_MODELO.md` para um arquivo novo, sem o `_` (ex.: `enem.md`).
2. Preencha o cabeçalho (`titulo`, `fonte`, `categoria`, `atualizado_em`, `status`).
3. Escreva em linguagem simples, com seções `##`.
4. Na raiz do projeto: `python -m scripts.ingest`.
5. Faça commit do documento **e** do `rag/indice/indice.json`.

## Situação dos documentos

Os 13 documentos abaixo são **rascunhos** (`status: rascunho`). Eles foram escritos em 2026-11-08 a
partir do catálogo do site (que já tinha os links conferidos) e de informações gerais dos serviços.
**Antes da apresentação, alguém da equipe precisa:**

1. Abrir o link do campo `fonte`.
2. Conferir cada frase, principalmente as marcadas com `CONFERIR` nos comentários `<!-- -->`.
3. Corrigir o que estiver diferente, apagar o comentário e trocar para `status: revisado`.
4. Rodar o ingest de novo.

O ingest mostra um aviso para cada documento que ainda é rascunho.

| Arquivo | Assunto | Fonte oficial |
| --- | --- | --- |
| `conta-gov-br.md` | Conta gov.br e níveis bronze, prata e ouro | https://www.gov.br/governodigital/pt-br/identidade/conta-gov-br |
| `enem.md` | Inscrição, isenção e resultados | https://www.gov.br/inep/pt-br/areas-de-atuacao/avaliacao-e-exames-educacionais/enem |
| `sisu-prouni-fies.md` | Como usar a nota do ENEM | https://acessounico.mec.gov.br/sisu |
| `pe-de-meia.md` | Quem recebe e onde consultar | https://www.gov.br/mec/pt-br/pe-de-meia |
| `carteira-de-trabalho-digital.md` | Contratos, vagas e primeiro emprego | https://www.gov.br/trabalho-e-emprego/pt-br/servicos/trabalhador/carteira-de-trabalho |
| `meu-sus-digital.md` | Vacinação e histórico de saúde | https://meususdigital.saude.gov.br |
| `e-titulo.md` | Título de eleitor digital e voto aos 16 | https://www.tse.jus.br/servicos-eleitorais/servicos/aplicativo-e-titulo |
| `cpf.md` | Consultar e regularizar o CPF | https://www.gov.br/receitafederal/pt-br/assuntos/meu-cpf |
| `alistamento-militar.md` | Quem precisa e quando | https://alistamento.eb.mil.br |
| `cadunico.md` | Cadastro Único e programas sociais | https://www.gov.br/mds/pt-br/acoes-e-programas/cadastro-unico |
| `registrato-e-valores-a-receber.md` | Contas no seu nome e dinheiro esquecido | https://www.bcb.gov.br/meubc/registrato |
| `golpes-digitais.md` | Golpes comuns e o que fazer se cair | https://cartilha.cert.br |
| `atendimento-presencial-manaus.md` | PAC, CRAS e UBS em Manaus | https://www.manaus.am.gov.br (**precisa de pesquisa**) |

## Regras

- **Toda informação precisa de fonte oficial.** Sem fonte, não entra. A IA repete o que está escrito.
- **Um arquivo por serviço ou tema.** Arquivos menores dão respostas mais precisas.
- **Nada de dados pessoais**, prints com CPF ou informações de alunos.
- **Sem passo a passo de telas** (as telas do gov.br mudam muito): explique o que o serviço faz e
  mande para o link oficial.
- **Valores, prazos e datas** só entram se estiverem na fonte e com o ano. Na dúvida, deixe de fora e
  mande a pessoa conferir no site oficial.
- Formatos aceitos: `.md` e `.txt`. Arquivos que começam com `_` e este README são ignorados.
