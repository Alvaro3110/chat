"""
Ferramentas de integracao com Databricks para os agentes.
Implementa ferramentas para consulta de dados e exploracao do Unity Catalog.
"""

import os
from typing import Any

from langchain_core.tools import tool

from app.db_connection.connection import get_db_connection


@tool
def list_catalogs() -> str:
    """
    Lista todos os catalogos disponiveis no Unity Catalog.

    Returns:
        String formatada com lista de catalogos
    """
    try:
        db = get_db_connection()
        query = "SHOW CATALOGS"
        results = db.execute_query(query)
        if not results:
            return "Nenhum catalogo encontrado."

        result = "Catalogos disponiveis no Unity Catalog:\n"
        result += "-" * 50 + "\n"
        for row in results:
            catalog_name = row.get("catalog", row.get("catalog_name", str(row)))
            result += f"  - {catalog_name}\n"
        return result
    except Exception as e:
        return f"Erro ao listar catalogos: {e}"


@tool
def list_schemas(catalog_name: str | None = None) -> str:
    """
    Lista todos os schemas de um catalogo.

    Args:
        catalog_name: Nome do catalogo (usa o padrao se nao especificado)

    Returns:
        String formatada com lista de schemas
    """
    try:
        db = get_db_connection()
        catalog = catalog_name or os.getenv("DATABRICKS_CATALOG", "main")
        query = f"SHOW SCHEMAS IN {catalog}"
        results = db.execute_query(query)
        if not results:
            return f"Nenhum schema encontrado no catalogo '{catalog}'."

        result = f"Schemas no catalogo '{catalog}':\n"
        result += "-" * 50 + "\n"
        for row in results:
            schema_name = row.get("databaseName", row.get("schema_name", str(row)))
            result += f"  - {schema_name}\n"
        return result
    except Exception as e:
        return f"Erro ao listar schemas: {e}"


@tool
def list_tables(catalog_name: str | None = None, schema_name: str | None = None) -> str:
    """
    Lista todas as tabelas de um schema.

    Args:
        catalog_name: Nome do catalogo (usa o padrao se nao especificado)
        schema_name: Nome do schema (usa o padrao se nao especificado)

    Returns:
        String formatada com lista de tabelas
    """
    try:
        db = get_db_connection()
        catalog = catalog_name or os.getenv("DATABRICKS_CATALOG", "main")
        schema = schema_name or os.getenv("DATABRICKS_SCHEMA", "default")
        query = f"SHOW TABLES IN {catalog}.{schema}"
        results = db.execute_query(query)
        if not results:
            return f"Nenhuma tabela encontrada em '{catalog}.{schema}'."

        result = f"Tabelas em '{catalog}.{schema}':\n"
        result += "-" * 50 + "\n"
        for row in results:
            table_name = row.get("tableName", row.get("table_name", str(row)))
            is_temp = row.get("isTemporary", False)
            table_type = " (temporaria)" if is_temp else ""
            result += f"  - {table_name}{table_type}\n"
        return result
    except Exception as e:
        return f"Erro ao listar tabelas: {e}"


@tool
def explain_table(table_name: str) -> str:
    """
    Explica uma tabela do Unity Catalog de forma detalhada para o usuario.
    Inclui schema, descricao das colunas e exemplos de dados.

    Args:
        table_name: Nome da tabela (pode incluir catalog.schema.table)

    Returns:
        String formatada com explicacao completa da tabela
    """
    try:
        db = get_db_connection()

        schema = db.get_table_schema(table_name)
        if not schema:
            return f"Tabela '{table_name}' nao encontrada."

        result = f"Explicacao da tabela '{table_name}':\n"
        result += "=" * 60 + "\n\n"

        result += "ESTRUTURA DA TABELA:\n"
        result += "-" * 40 + "\n"
        for col in schema:
            col_name = col.get("col_name", "")
            data_type = col.get("data_type", "")
            comment = col.get("comment", "")
            if col_name and not col_name.startswith("#"):
                result += f"  {col_name}:\n"
                result += f"    Tipo: {data_type}\n"
                if comment:
                    result += f"    Descricao: {comment}\n"
                result += "\n"

        result += "\nEXEMPLO DE DADOS (3 primeiras linhas):\n"
        result += "-" * 40 + "\n"
        try:
            sample = db.get_sample_data(table_name, 3)
            if sample:
                for i, row in enumerate(sample, 1):
                    result += f"  Registro {i}:\n"
                    for key, value in list(row.items())[:5]:
                        result += f"    {key}: {value}\n"
                    if len(row) > 5:
                        result += f"    ... e mais {len(row) - 5} campos\n"
                    result += "\n"
            else:
                result += "  (tabela vazia ou sem permissao de leitura)\n"
        except Exception:
            result += "  (nao foi possivel obter amostra de dados)\n"

        return result
    except Exception as e:
        return f"Erro ao explicar tabela '{table_name}': {e}"


@tool
def search_tables(search_term: str) -> str:
    """
    Busca tabelas no Unity Catalog que contenham o termo especificado.

    Args:
        search_term: Termo de busca para encontrar tabelas

    Returns:
        String formatada com tabelas encontradas
    """
    try:
        db = get_db_connection()
        catalog = os.getenv("DATABRICKS_CATALOG", "main")
        schema = os.getenv("DATABRICKS_SCHEMA", "default")

        query = f"""
        SELECT table_name, table_type, comment
        FROM {catalog}.information_schema.tables
        WHERE table_schema = '{schema}'
        AND (
            LOWER(table_name) LIKE LOWER('%{search_term}%')
            OR LOWER(comment) LIKE LOWER('%{search_term}%')
        )
        LIMIT 20
        """
        results = db.execute_query(query)

        if not results:
            query_fallback = f"SHOW TABLES IN {catalog}.{schema}"
            all_tables = db.execute_query(query_fallback)
            search_lower = search_term.lower()
            results = [
                t for t in all_tables
                if search_lower in str(t.get("tableName", "")).lower()
            ]

        if not results:
            return f"Nenhuma tabela encontrada com o termo '{search_term}'."

        result = f"Tabelas encontradas para '{search_term}':\n"
        result += "-" * 50 + "\n"
        for row in results:
            table_name = row.get("table_name", row.get("tableName", str(row)))
            comment = row.get("comment", "")
            result += f"  - {table_name}"
            if comment:
                result += f": {comment}"
            result += "\n"
        return result
    except Exception as e:
        return f"Erro ao buscar tabelas: {e}"


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


CATALOG_EXPLORATION_TOOLS = [
    list_catalogs,
    list_schemas,
    list_tables,
    explain_table,
    search_tables,
]

DATA_QUERY_TOOLS = [
    describe_table,
    sample_data,
    run_sql,
    get_metadata,
]


def get_tools_for_theme(theme: str) -> list:
    """
    Retorna lista de ferramentas disponiveis para um tema especifico.

    Args:
        theme: Nome do tema (cadastro, financeiro, rentabilidade, sql)

    Returns:
        Lista de ferramentas LangChain
    """
    if theme and theme.lower() == "sql":
        return CATALOG_EXPLORATION_TOOLS + DATA_QUERY_TOOLS
    return DATA_QUERY_TOOLS


def get_catalog_tools() -> list:
    """Retorna ferramentas de exploracao do Unity Catalog."""
    return CATALOG_EXPLORATION_TOOLS


def get_sql_tools() -> list:
    """Retorna ferramentas para consultas SQL."""
    return DATA_QUERY_TOOLS


def get_all_tools() -> list:
    """Retorna todas as ferramentas disponiveis."""
    return CATALOG_EXPLORATION_TOOLS + DATA_QUERY_TOOLS


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
