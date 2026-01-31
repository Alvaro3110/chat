"""
Módulo de conexão com Databricks.
Gerencia conexões com SQL Warehouse e Unity Catalog.
"""

import os
from typing import Any

from databricks import sql
from databricks.sdk import WorkspaceClient


class DatabricksConnection:
    """Gerencia conexões com Databricks SQL Warehouse."""

    def __init__(self):
        self.host = os.getenv("DATABRICKS_HOST")
        self.token = os.getenv("DATABRICKS_TOKEN")
        self.warehouse_id = os.getenv("DATABRICKS_WAREHOUSE_ID")
        self.catalog = os.getenv("DATABRICKS_CATALOG", "main")
        self.schema = os.getenv("DATABRICKS_SCHEMA", "default")
        self._connection = None
        self._workspace_client = None

    @property
    def connection(self):
        """Retorna conexão SQL lazy-loaded."""
        if self._connection is None:
            self._connection = sql.connect(
                server_hostname=self.host,
                http_path=f"/sql/1.0/warehouses/{self.warehouse_id}",
                access_token=self.token,
            )
        return self._connection

    @property
    def workspace_client(self) -> WorkspaceClient:
        """Retorna cliente do Workspace lazy-loaded."""
        if self._workspace_client is None:
            self._workspace_client = WorkspaceClient(
                host=self.host,
                token=self.token,
            )
        return self._workspace_client

    def execute_query(self, query: str) -> list[dict[str, Any]]:
        """
        Executa uma query SQL e retorna os resultados.

        Args:
            query: Query SQL a ser executada

        Returns:
            Lista de dicionários com os resultados
        """
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            return results
        finally:
            cursor.close()

    def get_table_schema(self, table_name: str) -> list[dict[str, str]]:
        """
        Retorna o schema de uma tabela.

        Args:
            table_name: Nome da tabela (pode incluir catalog.schema.table)

        Returns:
            Lista com informações das colunas
        """
        query = f"DESCRIBE TABLE {table_name}"
        return self.execute_query(query)

    def get_sample_data(self, table_name: str, limit: int = 5) -> list[dict[str, Any]]:
        """
        Retorna amostra de dados de uma tabela.

        Args:
            table_name: Nome da tabela
            limit: Número de linhas a retornar

        Returns:
            Lista com dados de amostra
        """
        query = f"SELECT * FROM {table_name} LIMIT {limit}"
        return self.execute_query(query)

    def close(self):
        """Fecha a conexão."""
        if self._connection:
            self._connection.close()
            self._connection = None


# Singleton para conexão global
_db_connection: DatabricksConnection | None = None


def get_db_connection() -> DatabricksConnection:
    """Retorna instância singleton da conexão."""
    global _db_connection
    if _db_connection is None:
        _db_connection = DatabricksConnection()
    return _db_connection
