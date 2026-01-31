"""
Agente Crítico (CriticAgent).
Avalia a consistência e completude das respostas dos subagentes.

Versão ENTERPRISE-SAFE:
- Suporta OpenAI / Databricks / outros providers
- Protege contra response.content como list, None ou dict
- Parsing JSON defensivo
- Nunca quebra o pipeline
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

    # ------------------------------------------------------------------
    # LLM
    # ------------------------------------------------------------------
    @property
    def llm(self) -> ChatOpenAI:
        """Retorna instância do LLM lazy-loaded."""
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=self.model_name,
                temperature=0,
            )
        return self._llm

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------
    @staticmethod
    def _normalize_llm_content(content: Any) -> str:
        """
        Normaliza QUALQUER retorno do LLM para string.

        Pode receber:
        - str
        - list
        - dict
        - None
        """
        if content is None:
            return ""

        if isinstance(content, str):
            return content

        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, dict):
                    # padrão comum em mensagens estruturadas
                    if "text" in item:
                        parts.append(str(item["text"]))
                    elif "content" in item:
                        parts.append(str(item["content"]))
                    else:
                        parts.append(str(item))
                else:
                    parts.append(str(item))
            return "\n".join(parts)

        if isinstance(content, dict):
            # fallback seguro
            return str(content)

        return str(content)

    @staticmethod
    def _safe_parse_json_from_text(text: str) -> dict[str, Any]:
        """
        Extrai JSON de texto livre de forma defensiva.
        Nunca lança exceção.
        """
        import json

        fallback: dict[str, Any] = {
            "is_valid": True,
            "completeness_score": 70,
            "issues": [],
            "suggestions": [],
            "summary": text,
        }

        if not text:
            fallback["summary"] = "Resposta vazia do modelo."
            return fallback

        try:
            start = text.find("{")
            end = text.rfind("}") + 1

            if start == -1 or end <= start:
                return fallback

            parsed = json.loads(text[start:end])

            if isinstance(parsed, dict):
                fallback.update(parsed)

            return fallback

        except Exception as e:
            fallback["summary"] = (
                "Erro ao interpretar resposta do modelo.\n"
                f"Motivo: {str(e)}\n\n"
                f"Conteúdo bruto:\n{text}"
            )
            return fallback

    # ------------------------------------------------------------------
    # Core
    # ------------------------------------------------------------------
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
            Resultado da validação
        """
        if self.session:
            self.session.log_agent_call(
                self.config.name,
                f"Validando {len(responses)} respostas",
            )

        # Proteção contra responses malformadas
        safe_responses = responses or []

        responses_text = "\n\n".join(
            f"**{r.get('agent', 'Unknown')}**:\n{r.get('response', 'Sem resposta')}"
            for r in safe_responses
            if isinstance(r, dict)
        )

        validation_prompt = f"""
Avalie as seguintes respostas dos subagentes para a pergunta do usuário.

Pergunta original:
{query}

Respostas dos subagentes:
{responses_text}

Analise:
1. As respostas respondem completamente à pergunta?
2. Há inconsistências ou contradições entre as respostas?
3. Os dados fazem sentido no contexto?
4. Há informações faltando?

Responda SOMENTE com um JSON válido no formato:

{{
  "is_valid": true/false,
  "completeness_score": 0-100,
  "issues": ["lista de problemas encontrados"],
  "suggestions": ["sugestões de melhoria"],
  "summary": "resumo da validação"
}}
""".strip()

        messages = [
            SystemMessage(content=self.config.system_prompt),
            HumanMessage(content=validation_prompt),
        ]

        # ------------------------------
        # Invocação segura do LLM
        # ------------------------------
        response = self.llm.invoke(messages)

        content = self._normalize_llm_content(
            getattr(response, "content", response)
        )

        validation = self._safe_parse_json_from_text(content)

        if self.session:
            self.session.log_agent_call(
                self.config.name,
                f"Validação concluída: {validation.get('is_valid', True)}",
                validation.get("summary", ""),
            )

        return validation

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def invoke(
        self,
        query: str,
        responses: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Executa a validação completa."""
        return self.validate_responses(query, responses)


def create_critic_agent(session: SessionContext | None = None) -> CriticAgent:
    """Factory function para criar CriticAgent."""
    return CriticAgent(session=session)
