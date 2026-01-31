"""
Classe base para subagentes temáticos.
Define a interface comum e funcionalidades compartilhadas.
"""

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from app.config.agents import AgentConfig
from app.governance.logging import SessionContext
from app.tools.databricks_tools import get_tools_for_theme


class BaseAgent:
    """Classe base para todos os subagentes."""

    def __init__(
        self,
        config: AgentConfig,
        session: SessionContext | None = None,
        model_name: str = "gpt-4o-mini",
    ):
        self.config = config
        self.session = session
        self.model_name = model_name
        self.tools = get_tools_for_theme(config.theme) if config.theme else []
        self._llm = None
        self._agent = None

    @property
    def llm(self) -> ChatOpenAI:
        """Retorna instância do LLM lazy-loaded."""
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=self.model_name,
                temperature=0,
            )
        return self._llm

    def get_prompt(self) -> ChatPromptTemplate:
        """Retorna o prompt template do agente."""
        return ChatPromptTemplate.from_messages([
            SystemMessage(content=self.config.system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessage(content="{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

    def invoke(
        self,
        query: str,
        chat_history: list | None = None,
    ) -> dict[str, Any]:
        """
        Executa o agente com uma query.

        Args:
            query: Pergunta do usuário
            chat_history: Histórico de mensagens

        Returns:
            Dicionário com resposta e metadados
        """
        if self.session:
            self.session.log_agent_call(self.config.name, query)

        chat_history = chat_history or []

        try:
            if self.tools:
                llm_with_tools = self.llm.bind_tools(self.tools)
                messages = [
                    SystemMessage(content=self.config.system_prompt),
                    *chat_history,
                    HumanMessage(content=query),
                ]

                response = llm_with_tools.invoke(messages)

                if response.tool_calls:
                    tool_results = self._execute_tools(response.tool_calls)
                    messages.append(response)
                    for tool_result in tool_results:
                        messages.append(tool_result)

                    final_response = self.llm.invoke(messages)
                    response_text = final_response.content
                else:
                    response_text = response.content
            else:
                messages = [
                    SystemMessage(content=self.config.system_prompt),
                    *chat_history,
                    HumanMessage(content=query),
                ]
                response = self.llm.invoke(messages)
                response_text = response.content

            result = {
                "agent": self.config.name,
                "response": response_text,
                "query": query,
                "success": True,
            }

            if self.session:
                self.session.log_agent_call(
                    self.config.name,
                    query,
                    response_text[:200],
                )

            return result

        except Exception as e:
            error_msg = f"Erro no agente {self.config.name}: {e}"
            if self.session:
                self.session.log_error(error_msg)
            return {
                "agent": self.config.name,
                "response": error_msg,
                "query": query,
                "success": False,
                "error": str(e),
            }

    def _execute_tools(self, tool_calls: list) -> list:
        """
        Executa chamadas de ferramentas.

        Args:
            tool_calls: Lista de chamadas de ferramentas

        Returns:
            Lista de mensagens com resultados
        """
        from langchain_core.messages import ToolMessage

        results = []
        tool_map = {tool.name: tool for tool in self.tools}

        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            if self.session:
                self.session.log_tool_execution(tool_name, tool_args)

            if tool_name in tool_map:
                try:
                    tool_result = tool_map[tool_name].invoke(tool_args)
                    if self.session:
                        self.session.log_tool_execution(
                            tool_name,
                            tool_args,
                            str(tool_result)[:200],
                        )
                except Exception as e:
                    tool_result = f"Erro ao executar {tool_name}: {e}"
            else:
                tool_result = f"Ferramenta {tool_name} não encontrada"

            results.append(
                ToolMessage(
                    content=str(tool_result),
                    tool_call_id=tool_call["id"],
                )
            )

        return results

    def get_description(self) -> str:
        """Retorna descrição do agente."""
        return self.config.description

    def get_name(self) -> str:
        """Retorna nome do agente."""
        return self.config.name
