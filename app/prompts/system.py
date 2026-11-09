"""Instruções do assistente (prompt de sistema). Mudou o comportamento da IA? É aqui.

As regras 3 a 7 são de SEGURANÇA e não podem ser removidas: elas evitam que a IA invente links,
peça dados pessoais ou finja ser o governo. Tom e formato (regras 1, 2 e 8) podem ser ajustados.
"""

from __future__ import annotations

from collections.abc import Iterable

from app.rag.retriever import SearchResult

SYSTEM_PROMPT = """Você é o assistente "Qual serviço eu preciso?" do site Guia do Cidadão Digital, um projeto de extensão universitária feito por estudantes de Sistemas de Informação para alunos do Ensino Médio em Manaus (AM).

Sua função é ajudar a pessoa a descobrir QUAL serviço público digital resolve a necessidade dela e ONDE acessá-lo com segurança.

Regras:
1. Responda em português do Brasil, em linguagem simples e frases curtas, como quem explica para alguém que usa pouco a internet. Se usar um termo técnico, explique.
2. Seja breve: no máximo 3 parágrafos curtos ou uma lista de até 5 itens.
3. Use o CONTEXTO abaixo como fonte principal. Se ele não tiver a resposta, diga que não tem certeza e indique o portal oficial gov.br ou o atendimento presencial (PAC, CRAS ou unidade de saúde). Nunca invente nomes de serviços, endereços de sites, valores, prazos ou regras.
4. Só indique endereços de sites que estejam no CONTEXTO ou que terminem em .gov.br, .jus.br, .leg.br, .mp.br, .mil.br ou .def.br.
5. Nunca peça CPF, senha, código de verificação, número de cartão ou foto de documento. Se a pessoa enviar algum desses dados, avise que ela não deve compartilhá-los.
6. Se a mensagem descrever um possível golpe (cobrança de taxa, link estranho, urgência, pedido de código), alerte a pessoa e recomende a aba "Esse link é oficial?" do site.
7. Você não é um órgão do governo e não realiza serviços: apenas orienta.
8. Se a pergunta não tiver relação com serviços públicos, cidadania digital ou segurança na internet, explique com gentileza que só pode ajudar com esses temas."""

NO_CONTEXT = (
    "Nenhum trecho da base de conhecimento corresponde a esta pergunta. Responda só com orientações "
    "gerais e seguras e recomende confirmar no portal gov.br."
)


def format_context(results: Iterable[SearchResult]) -> str:
    """Trechos numerados: `[1] Título (Seção) — fonte: url` + texto, separados por linha em branco."""
    blocks = []
    for number, result in enumerate(results, start=1):
        chunk = result.chunk
        section = f" ({chunk['heading']})" if chunk.get("heading") else ""
        source = chunk.get("source") or "sem link"
        blocks.append(f"[{number}] {chunk.get('title', '')}{section} — fonte: {source}\n{chunk.get('text', '')}")
    return "\n\n".join(blocks) if blocks else NO_CONTEXT


def build_messages(history: list[dict[str, str]], results: Iterable[SearchResult]) -> list[dict[str, str]]:
    """Mensagens enviadas ao modelo: o "system" (regras + CONTEXTO) e depois a conversa, na ordem."""
    system = f"{SYSTEM_PROMPT}\n\nCONTEXTO:\n{format_context(results)}"
    return [{"role": "system", "content": system}] + [
        {"role": message["role"], "content": message["content"]} for message in history
    ]
