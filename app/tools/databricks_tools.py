"""
Ferramentas de integração com Databricks para os agentes.
Implementa describe_table, sample_data, run_sql e get_metadata.
"""

from typing import Any

from langchain_core.tools import tool

from app.databricks.connection import get_db_connection


@tool
def describe_table(table_name: str) -> str:
    """
    Retorna o schema de uma tabela do Databricks.

    Args:
        table_name: Nome da tabela (pode incluir catalog.schema.table)

    Returns:
        String formatada com informações das colunas
    """
    try:
        db = get_db_connection()
        schema = db.get_table_schema(table_name)
        if not schema:
            return f"Tabela '{table_name}' não encontrada ou sem colunas."

        result = f"Schema da tabela '{table_name}':\n"
        result += "-" * 50 + "\n"
        for col in schema:
            col_name = col.get("col_name", "")
            data_type = col.get("data_type", "")
            comment = col.get("comment", "")
            result += f"  - {col_name}: {data_type}"
            if comment:
                result += f" ({comment})"
            result += "\n"
        return result
    except Exception as e:
        return f"Erro ao descrever tabela '{table_name}': {e}"


@tool
def sample_data(table_name: str, limit: int = 5) -> str:
    """
    Retorna uma amostra de dados de uma tabela.

    Args:
        table_name: Nome da tabela
        limit: Número de linhas a retornar (padrão: 5)

    Returns:
        String formatada com dados de amostra
    """
    try:
        db = get_db_connection()
        data = db.get_sample_data(table_name, limit)
        if not data:
            return f"Tabela '{table_name}' está vazia ou não encontrada."

        result = f"Amostra de dados da tabela '{table_name}' ({len(data)} linhas):\n"
        result += "-" * 50 + "\n"
        for i, row in enumerate(data, 1):
            result += f"Linha {i}:\n"
            for key, value in row.items():
                result += f"  {key}: {value}\n"
            result += "\n"
        return result
    except Exception as e:
        return f"Erro ao obter amostra de '{table_name}': {e}"


@tool
def run_sql(query: str) -> str:
    """
    Executa uma query SQL no Databricks e retorna os resultados.

    Args:
        query: Query SQL a ser executada

    Returns:
        String formatada com os resultados da query
    """
    try:
        db = get_db_connection()
        results = db.execute_query(query)
        if not results:
            return "Query executada com sucesso. Nenhum resultado retornado."

        result = f"Resultados da query ({len(results)} linhas):\n"
        result += "-" * 50 + "\n"
        for i, row in enumerate(results, 1):
            result += f"Linha {i}:\n"
            for key, value in row.items():
                result += f"  {key}: {value}\n"
            result += "\n"
        return result
    except Exception as e:
        return f"Erro ao executar query: {e}"


@tool
def get_metadata(table_name: str) -> str:
    """
    Retorna metadados detalhados de uma tabela do Unity Catalog.

    Args:
        table_name: Nome da tabela (catalog.schema.table)

    Returns:
        String formatada com metadados da tabela
    """
    try:
        db = get_db_connection()
        query = f"DESCRIBE EXTENDED {table_name}"
        metadata = db.execute_query(query)
        if not metadata:
            return f"Metadados não encontrados para '{table_name}'."

        result = f"Metadados da tabela '{table_name}':\n"
        result += "-" * 50 + "\n"
        for item in metadata:
            col_name = item.get("col_name", "")
            data_type = item.get("data_type", "")
            if col_name and data_type:
                result += f"  {col_name}: {data_type}\n"
            elif col_name:
                result += f"  {col_name}\n"
        return result
    except Exception as e:
        return f"Erro ao obter metadados de '{table_name}': {e}"


def get_tools_for_theme(theme: str) -> list:
    """
    Retorna lista de ferramentas disponíveis para um tema específico.

    Args:
        theme: Nome do tema (cadastro, financeiro, rentabilidade)

    Returns:
        Lista de ferramentas LangChain
    """
    return [describe_table, sample_data, run_sql, get_metadata]


def get_all_tools() -> list:
    """Retorna todas as ferramentas disponíveis."""
    return [describe_table, sample_data, run_sql, get_metadata]


def format_tool_results(results: list[dict[str, Any]]) -> str:
    """
    Formata resultados de ferramentas para exibição.

    Args:
        results: Lista de dicionários com resultados

    Returns:
        String formatada
    """
    if not results:
        return "Nenhum resultado."

    output = []
    for i, row in enumerate(results, 1):
        output.append(f"Registro {i}:")
        for key, value in row.items():
            output.append(f"  {key}: {value}")
    return "\n".join(output)
