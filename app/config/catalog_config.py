"""
Configuracao do Unity Catalog para a plataforma multiagente.
Define estrutura de metadados de tabelas e configuracao de acesso ao catalogo.
Extensivel para multiplos catalogos, schemas e fontes de dados.
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DataDomain(Enum):
    """Dominios de dados disponiveis no Unity Catalog."""
    CADASTRO = "cadastro"
    FINANCEIRO = "financeiro"
    RENTABILIDADE = "rentabilidade"
    GERAL = "geral"


@dataclass
class ColumnMetadata:
    """Metadados de uma coluna de tabela."""
    name: str
    data_type: str
    description: str = ""
    is_nullable: bool = True
    is_primary_key: bool = False
    is_foreign_key: bool = False
    foreign_key_reference: str | None = None


@dataclass
class TableMetadata:
    """Metadados de uma tabela do Unity Catalog."""
    name: str
    catalog: str
    schema: str
    description: str
    domain: DataDomain
    columns: list[ColumnMetadata] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    owner: str = ""
    is_view: bool = False
    row_count_estimate: int | None = None

    @property
    def full_name(self) -> str:
        """Retorna o nome completo da tabela (catalog.schema.table)."""
        return f"{self.catalog}.{self.schema}.{self.name}"

    def get_column_names(self) -> list[str]:
        """Retorna lista de nomes das colunas."""
        return [col.name for col in self.columns]

    def get_column_by_name(self, name: str) -> ColumnMetadata | None:
        """Retorna metadados de uma coluna pelo nome."""
        for col in self.columns:
            if col.name.lower() == name.lower():
                return col
        return None


@dataclass
class CatalogConfig:
    """Configuracao de um catalogo do Unity Catalog."""
    name: str
    description: str = ""
    schemas: list[str] = field(default_factory=list)
    is_default: bool = False


class UnityCatalogRegistry:
    """
    Registro central de metadados do Unity Catalog.
    Gerencia catalogos, schemas e tabelas de forma extensivel.
    """

    def __init__(self):
        self._catalogs: dict[str, CatalogConfig] = {}
        self._tables: dict[str, TableMetadata] = {}
        self._domain_tables: dict[DataDomain, list[str]] = {
            domain: [] for domain in DataDomain
        }
        self._initialize_from_env()

    def _initialize_from_env(self):
        """Inicializa configuracao a partir de variaveis de ambiente."""
        default_catalog = os.getenv("DATABRICKS_CATALOG", "main")
        default_schema = os.getenv("DATABRICKS_SCHEMA", "default")

        self._default_catalog = default_catalog
        self._default_schema = default_schema

        self.register_catalog(CatalogConfig(
            name=default_catalog,
            description="Catalogo padrao configurado via ambiente",
            schemas=[default_schema],
            is_default=True,
        ))

    @property
    def default_catalog(self) -> str:
        """Retorna o catalogo padrao."""
        return self._default_catalog

    @property
    def default_schema(self) -> str:
        """Retorna o schema padrao."""
        return self._default_schema

    def register_catalog(self, catalog: CatalogConfig) -> None:
        """Registra um catalogo no registry."""
        self._catalogs[catalog.name] = catalog

    def register_table(self, table: TableMetadata) -> None:
        """Registra uma tabela no registry."""
        self._tables[table.full_name] = table
        self._domain_tables[table.domain].append(table.full_name)

    def get_catalog(self, name: str) -> CatalogConfig | None:
        """Retorna configuracao de um catalogo."""
        return self._catalogs.get(name)

    def get_table(self, full_name: str) -> TableMetadata | None:
        """Retorna metadados de uma tabela pelo nome completo."""
        return self._tables.get(full_name)

    def get_table_by_short_name(self, name: str) -> TableMetadata | None:
        """Retorna metadados de uma tabela pelo nome curto (sem catalog.schema)."""
        for _full_name, table in self._tables.items():
            if table.name.lower() == name.lower():
                return table
        return None

    def get_tables_by_domain(self, domain: DataDomain) -> list[TableMetadata]:
        """Retorna lista de tabelas de um dominio especifico."""
        return [
            self._tables[full_name]
            for full_name in self._domain_tables.get(domain, [])
            if full_name in self._tables
        ]

    def get_all_tables(self) -> list[TableMetadata]:
        """Retorna lista de todas as tabelas registradas."""
        return list(self._tables.values())

    def get_all_catalogs(self) -> list[CatalogConfig]:
        """Retorna lista de todos os catalogos registrados."""
        return list(self._catalogs.values())

    def search_tables(self, query: str) -> list[TableMetadata]:
        """Busca tabelas por nome ou descricao."""
        query_lower = query.lower()
        results = []
        for table in self._tables.values():
            if (query_lower in table.name.lower() or
                query_lower in table.description.lower() or
                any(query_lower in tag.lower() for tag in table.tags)):
                results.append(table)
        return results

    def get_domain_summary(self) -> dict[str, int]:
        """Retorna resumo de tabelas por dominio."""
        return {
            domain.value: len(tables)
            for domain, tables in self._domain_tables.items()
        }

    def format_table_info(self, table: TableMetadata) -> str:
        """Formata informacoes de uma tabela para exibicao."""
        info = [
            f"Tabela: {table.full_name}",
            f"Descricao: {table.description}",
            f"Dominio: {table.domain.value}",
            f"Colunas ({len(table.columns)}):",
        ]
        for col in table.columns:
            col_info = f"  - {col.name} ({col.data_type})"
            if col.description:
                col_info += f": {col.description}"
            if col.is_primary_key:
                col_info += " [PK]"
            if col.is_foreign_key:
                col_info += f" [FK -> {col.foreign_key_reference}]"
            info.append(col_info)
        return "\n".join(info)

    def get_schema_for_agent(self, domain: DataDomain) -> str:
        """
        Retorna descricao do schema para uso por agentes.
        Otimizado para contexto de LLM.
        """
        tables = self.get_tables_by_domain(domain)
        if not tables:
            return f"Nenhuma tabela registrada para o dominio {domain.value}."

        schema_parts = [f"Schema do dominio {domain.value}:"]
        for table in tables:
            schema_parts.append(f"\n{table.full_name}:")
            schema_parts.append(f"  Descricao: {table.description}")
            schema_parts.append("  Colunas:")
            for col in table.columns[:10]:
                schema_parts.append(f"    - {col.name}: {col.data_type}")
            if len(table.columns) > 10:
                schema_parts.append(f"    ... e mais {len(table.columns) - 10} colunas")
        return "\n".join(schema_parts)


_catalog_registry: UnityCatalogRegistry | None = None


def get_catalog_registry() -> UnityCatalogRegistry:
    """Retorna instancia singleton do registry de catalogos."""
    global _catalog_registry
    if _catalog_registry is None:
        _catalog_registry = UnityCatalogRegistry()
    return _catalog_registry


def register_table_metadata(
    name: str,
    description: str,
    domain: DataDomain,
    columns: list[dict[str, Any]] | None = None,
    catalog: str | None = None,
    schema: str | None = None,
    tags: list[str] | None = None,
) -> TableMetadata:
    """
    Funcao utilitaria para registrar metadados de uma tabela.

    Args:
        name: Nome da tabela
        description: Descricao da tabela
        domain: Dominio de dados
        columns: Lista de dicionarios com metadados das colunas
        catalog: Nome do catalogo (usa padrao se nao especificado)
        schema: Nome do schema (usa padrao se nao especificado)
        tags: Tags para busca

    Returns:
        TableMetadata registrado
    """
    registry = get_catalog_registry()

    table = TableMetadata(
        name=name,
        catalog=catalog or registry.default_catalog,
        schema=schema or registry.default_schema,
        description=description,
        domain=domain,
        columns=[
            ColumnMetadata(**col) for col in (columns or [])
        ],
        tags=tags or [],
    )

    registry.register_table(table)
    return table


def get_table_context_for_query(query: str) -> str:
    """
    Retorna contexto de tabelas relevantes para uma query.
    Usado pelos agentes para entender o schema disponivel.
    """
    registry = get_catalog_registry()
    relevant_tables = registry.search_tables(query)

    if not relevant_tables:
        all_tables = registry.get_all_tables()
        if all_tables:
            relevant_tables = all_tables[:5]

    if not relevant_tables:
        return "Nenhuma tabela registrada no catalogo."

    context_parts = ["Tabelas disponiveis:"]
    for table in relevant_tables[:5]:
        context_parts.append(registry.format_table_info(table))
        context_parts.append("")

    return "\n".join(context_parts)


def get_domain_tables_context(domain: DataDomain) -> str:
    """Retorna contexto de tabelas de um dominio especifico."""
    registry = get_catalog_registry()
    return registry.get_schema_for_agent(domain)
