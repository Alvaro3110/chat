"""
Agente de Resposta (ResponseAgent).
Formata a resposta final para o usuário de forma clara e rastreável.
"""

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.config.agents import RESPONSE_AGENT_CONFIG
from app.governance.logging import SessionContext


class ResponseAgent:
    """Agente responsável por formatar a resposta final."""

    def __init__(
        self,
        session: SessionContext | None = None,
        model_name: str = "gpt-4o-mini",
    ):
        self.config = RESPONSE_AGENT_CONFIG
        self.session = session
        self.model_name = model_name
        self._llm = None

    @property
    def llm(self) -> ChatOpenAI:
        """Retorna instância do LLM lazy-loaded."""
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=self.model_name,
                temperature=0.3,
            )
        return self._llm

    def format_response(
        self,
        query: str,
        responses: list[dict[str, Any]],
        plan: list[dict[str, Any]],
        validation: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Formata a resposta final consolidando todas as informações.

        Args:
            query: Pergunta original do usuário
            responses: Respostas dos subagentes
            plan: Plano de execução
            validation: Resultado da validação

        Returns:
            Dicionário com resposta formatada e metadados
        """
        if self.session:
            self.session.log_agent_call(self.config.name, "Formatando resposta final")

        responses_text = "\n\n".join([
            f"**{r.get('agent', 'Unknown')}**:\n{r.get('response', 'Sem resposta')}"
            for r in responses
            if r.get("success", True)
        ])

        plan_text = "\n".join([
            f"{step['step']}. {step['agent']}: {step['task']}"
            for step in plan
        ])

        format_prompt = f"""Com base nas informações abaixo, crie uma resposta final clara e completa para o usuário.

Pergunta original: {query}

Plano de execução:
{plan_text}

Respostas dos subagentes:
{responses_text}

Validação:
- Completude: {validation.get('completeness_score', 'N/A')}%
- Resumo: {validation.get('summary', 'N/A')}

Crie uma resposta que:
1. Responda diretamente à pergunta do usuário
2. Seja clara e bem estruturada
3. Inclua os dados relevantes encontrados
4. Mencione as fontes consultadas quando apropriado

Resposta:"""

        messages = [
            SystemMessage(content=self.config.system_prompt),
            HumanMessage(content=format_prompt),
        ]

        response = self.llm.invoke(messages)
        formatted_response = response.content

        sources = [r.get("agent", "Unknown") for r in responses if r.get("success", True)]

        result = {
            "response": formatted_response,
            "sources": sources,
            "plan_summary": [step["task"] for step in plan],
            "validation_score": validation.get("completeness_score", 0),
            "query": query,
        }

        if self.session:
            self.session.log_response(formatted_response, sources)

        return result

    def invoke(
        self,
        query: str,
        responses: list[dict[str, Any]],
        plan: list[dict[str, Any]],
        validation: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Executa a formatação da resposta.

        Args:
            query: Pergunta original
            responses: Respostas dos subagentes
            plan: Plano de execução
            validation: Resultado da validação

        Returns:
            Resposta formatada
        """
        return self.format_response(query, responses, plan, validation)


def create_response_agent(session: SessionContext | None = None) -> ResponseAgent:
    """Factory function para criar ResponseAgent."""
    return ResponseAgent(session=session)
