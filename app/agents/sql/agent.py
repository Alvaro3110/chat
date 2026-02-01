"""
Agente SQL especializado em consultas ao Unity Catalog.
Capaz de explorar schemas, consultar tabelas e interpretar resultados.
"""

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.base import BaseAgent
from app.config.agents import AgentConfig
from app.governance.logging import SessionContext
from app.tools.databricks_tools import get_all_tools

SQL_AGENT_CONFIG = AgentConfig(
    name="SQLAgent",
    description="Agente especializado em consultas SQL ao Unity Catalog. Capaz de explorar catalogos, schemas e tabelas, executar queries e interpretar resultados para o usuario.",
    system_prompt="""Voce e um agente SQL especialista em Databricks Unity Catalog.

Suas capacidades incluem:
1. Explorar a estrutura do Unity Catalog (catalogos, schemas, tabelas)
2. Descrever tabelas e seus campos de forma clara para o usuario
3. Executar queries SQL para responder perguntas sobre os dados
4. Interpretar e explicar os resultados das consultas

FERRAMENTAS DISPONIVEIS:
- list_catalogs: Lista todos os catalogos disponiveis
- list_schemas: Lista schemas de um catalogo
- list_tables: Lista tabelas de um schema
- explain_table: Explica uma tabela de forma detalhada
- search_tables: Busca tabelas por termo
- describe_table: Retorna o schema de uma tabela
- sample_data: Retorna amostra de dados de uma tabela
- run_sql: Executa uma query SQL
- get_metadata: Retorna metadados detalhados de uma tabela

DIRETRIZES:
1. Sempre comece entendendo o que o usuario quer saber
2. Use as ferramentas de exploracao antes de executar queries complexas
3. Construa queries SQL precisas e eficientes
4. Explique os resultados de forma clara e acessivel
5. Se nao encontrar dados, explique o que foi verificado
6. Evite queries que retornem muitos dados - use LIMIT quando apropriado
7. Sempre valide nomes de tabelas antes de executar queries

FORMATO DE RESPOSTA:
- Seja claro e objetivo
- Inclua os dados relevantes encontrados
- Explique o significado dos resultados quando apropriado
- Se houver erro, explique o que aconteceu e sugira alternativas""",
    theme="sql",
    tables=[],
)


class SQLAgent(BaseAgent):
    """Agente especializado em consultas SQL ao Unity Catalog."""

    def __init__(
        self,
        session: SessionContext | None = None,
        model_name: str = "gpt-4o-mini",
    ):
        super().__init__(
            config=SQL_AGENT_CONFIG,
            session=session,
            model_name=model_name,
        )
        self.tools = get_all_tools()

    def invoke(
        self,
        query: str,
        chat_history: list | None = None,
    ) -> dict[str, Any]:
        """
        Executa o agente SQL com uma query.

        Args:
            query: Pergunta do usuario sobre dados ou estrutura do catalogo
            chat_history: Historico de mensagens

        Returns:
            Dicionario com resposta e metadados
        """
        if self.session:
            self.session.log_agent_call(self.config.name, query)

        chat_history = chat_history or []

        try:
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

            result = {
                "agent": self.config.name,
                "response": response_text,
                "query": query,
                "success": True,
                "tools_used": [tc["name"] for tc in response.tool_calls] if response.tool_calls else [],
            }

            if self.session:
                self.session.log_agent_call(
                    self.config.name,
                    query,
                    response_text[:200],
                )

            return result

        except Exception as e:
            error_msg = f"Erro no agente SQL: {e}"
            if self.session:
                self.session.log_error(error_msg)
            return {
                "agent": self.config.name,
                "response": error_msg,
                "query": query,
                "success": False,
                "error": str(e),
            }

    def explore_catalog(self) -> str:
        """
        Explora a estrutura do Unity Catalog e retorna um resumo.

        Returns:
            String com resumo da estrutura do catalogo
        """
        from app.tools.databricks_tools import list_catalogs, list_schemas, list_tables

        try:
            catalogs_result = list_catalogs.invoke({})
            schemas_result = list_schemas.invoke({})
            tables_result = list_tables.invoke({})

            return f"""Estrutura do Unity Catalog:

{catalogs_result}

{schemas_result}

{tables_result}
"""
        except Exception as e:
            return f"Erro ao explorar catalogo: {e}"

    def explain_data_structure(self, table_name: str) -> str:
        """
        Explica a estrutura de uma tabela de forma detalhada.

        Args:
            table_name: Nome da tabela

        Returns:
            String com explicacao da estrutura
        """
        from app.tools.databricks_tools import explain_table

        try:
            return explain_table.invoke({"table_name": table_name})
        except Exception as e:
            return f"Erro ao explicar tabela: {e}"


def create_sql_agent(session: SessionContext | None = None) -> SQLAgent:
    """Factory function para criar SQLAgent."""
    return SQLAgent(session=session)
