"""
Agente Crítico (CriticAgent).
Avalia a consistência e completude das respostas dos subagentes.
"""

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.config.agents import CRITIC_AGENT_CONFIG
from app.governance.logging import SessionContext


class CriticAgent:
    """Agente responsável por validar respostas dos subagentes."""

    def __init__(
        self,
        session: SessionContext | None = None,
        model_name: str = "gpt-4o-mini",
    ):
        self.config = CRITIC_AGENT_CONFIG
        self.session = session
        self.model_name = model_name
        self._llm = None

    @property
    def llm(self) -> ChatOpenAI:
        """Retorna instância do LLM lazy-loaded."""
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=self.model_name,
                temperature=0,
            )
        return self._llm

    def validate_responses(
        self,
        query: str,
        responses: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Valida as respostas dos subagentes.

        Args:
            query: Pergunta original do usuário
            responses: Lista de respostas dos subagentes

        Returns:
            Dicionário com resultado da validação
        """
        if self.session:
            self.session.log_agent_call(self.config.name, f"Validando {len(responses)} respostas")

        responses_text = "\n\n".join([
            f"**{r.get('agent', 'Unknown')}**:\n{r.get('response', 'Sem resposta')}"
            for r in responses
        ])

        validation_prompt = f"""Avalie as seguintes respostas dos subagentes para a pergunta do usuário.

Pergunta original: {query}

Respostas dos subagentes:
{responses_text}

Analise:
1. As respostas respondem completamente à pergunta?
2. Há inconsistências ou contradições entre as respostas?
3. Os dados fazem sentido no contexto?
4. Há informações faltando?

Responda em formato JSON:
{{
    "is_valid": true/false,
    "completeness_score": 0-100,
    "issues": ["lista de problemas encontrados"],
    "suggestions": ["sugestões de melhoria"],
    "summary": "resumo da validação"
}}"""

        messages = [
            SystemMessage(content=self.config.system_prompt),
            HumanMessage(content=validation_prompt),
        ]

        response = self.llm.invoke(messages)
        content = response.content

        try:
            import json

            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                validation = json.loads(content[json_start:json_end])
            else:
                validation = {
                    "is_valid": True,
                    "completeness_score": 70,
                    "issues": [],
                    "suggestions": [],
                    "summary": content,
                }
        except json.JSONDecodeError:
            validation = {
                "is_valid": True,
                "completeness_score": 70,
                "issues": [],
                "suggestions": [],
                "summary": content,
            }

        if self.session:
            self.session.log_agent_call(
                self.config.name,
                f"Validação concluída: {validation.get('is_valid', True)}",
                validation.get("summary", ""),
            )

        return validation

    def invoke(
        self,
        query: str,
        responses: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Executa a validação completa.

        Args:
            query: Pergunta original
            responses: Respostas dos subagentes

        Returns:
            Resultado da validação
        """
        return self.validate_responses(query, responses)


def create_critic_agent(session: SessionContext | None = None) -> CriticAgent:
    """Factory function para criar CriticAgent."""
    return CriticAgent(session=session)
