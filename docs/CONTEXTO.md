# Contexto do projeto de extensão

Resumo do documento **"Conteúdo Teórico — Inclusão Digital: Acesso aos Serviços Públicos Digitais"**
(material de estudo da equipe, versão de 2026-11-07). O assistente e a base do RAG devem **falar a
mesma língua da apresentação**: mesmos conceitos, mesmos exemplos e mesmas mensagens.

## O projeto

- **Título:** Inclusão Digital: Acesso aos Serviços Públicos Digitais
- **Curso:** Sistemas de Informação, 5º período, 2026.2 (Manaus-AM)
- **Público:** alunos do Ensino Médio (16 e 17 anos). Já têm celular, mas usam para redes sociais e
  jogos, não para acessar direitos e serviços. Têm medo de golpes.
- **Entregas:** apresentação expositiva (~75 min, cinco eixos), dinâmica "Golpe ou Real?", materiais
  educativos (o site é um deles) e resumo expandido.
- **Onde o projeto atua:** no 2º nível (habilidades e uso) e no 3º nível (resultados: emprego, renda,
  direitos) da exclusão digital. O 1º nível (ter aparelho e internet) os alunos já têm.
- **O mito do "nativo digital":** saber usar redes sociais e jogos não garante saber acessar serviços,
  proteger dados ou checar informações. É exatamente o perfil do público.

## Os cinco eixos da apresentação

| Eixo | Tempo | Ideia central | Onde aparece no site / na API |
| --- | --- | --- | --- |
| Abertura | 5 min | Apresentação do grupo e do projeto | — |
| 1. Inclusão e letramento digital | 10 min | Ter acesso não basta: é preciso saber usar | Tema 1 do Guia |
| 2. Governo digital e serviços públicos | 15 min | O Estado migrou para o digital; o acesso virou condição de cidadania | Catálogo de serviços + **este assistente** + documentos do RAG |
| 3. Cidadania digital e proteção de dados | 10 min | O cidadão tem direitos também no ambiente digital | Tema 3 do Guia; **mascaramento de dados na API** |
| 4. Segurança da informação + dinâmica | 20 min | Golpes exploram pessoas, não máquinas; conhecer os sinais protege | Tema 4, verificador de links, regra 6 do prompt, `golpes-digitais.md` |
| 5. Desinformação e bem-estar digital | 10 min | Checar antes de compartilhar e usar a tecnologia com equilíbrio | Tema 5 do Guia |
| Fechamento | 5 min | Três mensagens-chave | — |

A única interação com os alunos é a dinâmica **"Golpe ou Real?"** (10 min, dentro do Eixo 4): a
equipe mostra de 6 a 8 mensagens com dados fictícios, algumas legítimas (como um aviso de resultado do
ENEM); os alunos votam; a equipe revela a resposta e aponta o sinal de golpe e o gatilho de persuasão.

## Conceitos que o assistente e os documentos devem usar

**Serviços por área** (Eixo 2), os mesmos da base do RAG:

| Área | Serviços |
| --- | --- |
| Educação | ENEM, Sisu, ProUni, Fies e Pé-de-Meia |
| Trabalho | Carteira de Trabalho Digital e vagas do Sine |
| Saúde | Meu SUS Digital, com a carteira de vacinação |
| Cidadania | e-Título, situação do CPF, alistamento militar e Meu CadÚnico |
| Vida financeira | Registrato e Valores a Receber, do Banco Central |

- **Conta gov.br = identidade digital**, com níveis bronze, prata e ouro: quanto mais forte a
  comprovação, mais serviços liberados (o nível de proteção cresce com a sensibilidade do serviço).
- **O paradoxo da digitalização:** o digital reduz filas, mas pode excluir quem não tem acesso ou
  habilidade. Por isso o atendimento presencial (**PAC e CRAS**) continua necessário, e o assistente
  deve indicá-lo quando o digital não resolver (regra 3 do prompt).

**Proteção de dados** (Eixo 3):

- **LGPD (Lei 13.709/2018)** e **Marco Civil da Internet (Lei 12.965/2014)**. Dados de crianças e
  adolescentes devem ser tratados no seu melhor interesse (LGPD, art. 14).
- **Biometria facial** (usada para validar a conta gov.br) é **dado sensível**: só deve ser fornecida
  em aplicativos oficiais.
- **Cyberbullying** (intimidação sistemática virtual) é crime desde a Lei 14.811/2024. Canal de ajuda:
  SaferNet Brasil.
- É por isso que esta API mascara CPF, cartão e e-mail e não guarda nada: o próprio site dá o exemplo.

**Segurança** (Eixo 4):

- **Os quatro sinais de golpe:** urgência, pedido de dado ou código, pedido de dinheiro e link fora do
  endereço oficial.
- **Gatilhos de persuasão** (Cialdini): autoridade ("aqui é da Receita"), urgência e escassez ("último
  dia"), afeto ou confiança ("oi, é seu primo").
- **Tipos de golpe:** falsa autoridade, falso benefício, sequestro de conta, falsa identidade pessoal,
  falsa oportunidade.
- **Autenticação em dois fatores:** algo que você sabe (senha), tem (celular) ou é (biometria).
- **Caiu num golpe:** avisar o banco na hora e pedir o **MED** (Mecanismo Especial de Devolução) em caso
  de Pix, trocar as senhas e registrar boletim de ocorrência.

**Desinformação** (Eixo 5): leitura lateral (abrir outras fontes), conferir data, busca reversa de
imagem e agências de checagem (Aos Fatos, Lupa, Comprova, Fato ou Fake). Deepfakes já são usados em
golpes que imitam a voz de parentes.

## As três mensagens-chave (fechamento)

1. **Acesso digital é direito.** Os serviços públicos digitais são gratuitos e pensados para o cidadão
   usar sem intermediários.
2. **Seus dados são seus.** Senhas, códigos e biometria nunca devem ser entregues a terceiros.
3. **Desconfie e confirme.** Diante de urgência, pedido de dado, pedido de dinheiro ou link estranho,
   confirme por um canal oficial.

O assistente reforça as três: indica o canal oficial e gratuito, nunca pede dados (regra 5 do prompt)
e alerta golpes (regra 6).

## Marco legal citado

| Norma | O que estabelece |
| --- | --- |
| Decreto 8.936/2016 | Plataforma de Cidadania Digital |
| Decreto 9.319/2018 | Estratégia Brasileira para a Transformação Digital (E-Digital) |
| Lei 12.965/2014 | Marco Civil da Internet |
| Lei 13.709/2018 | LGPD |
| Lei 14.129/2021 | Lei do Governo Digital |
| Lei 14.811/2024 | Proteção de crianças e adolescentes; cyberbullying como crime |

> O próprio documento avisa que as referências foram organizadas sem consulta às obras: confira
> edição, páginas e links antes de citar no resumo expandido.
