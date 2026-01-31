"""
check_databricks_access.py

Objetivo:
Validar acesso ao Databricks:
1. Autenticação
2. Workspace
3. Unity Catalog
4. Model Serving Endpoints

Pré-requisitos:
- pip install databricks-sdk python-dotenv
- .env com DATABRICKS_HOST e DATABRICKS_TOKEN
"""

from databricks.sdk import WorkspaceClient
from dotenv import load_dotenv
import os
import sys


def fail(msg: str):
    print(f"❌ FALHA: {msg}")
    sys.exit(1)


def success(msg: str):
    print(f"✅ OK: {msg}")


def main():
    load_dotenv()

    host = os.getenv("DATABRICKS_HOST")
    token = os.getenv("DATABRICKS_TOKEN")

    if not host:
        fail("Variável DATABRICKS_HOST não encontrada no .env")
    if not token:
        fail("Variável DATABRICKS_TOKEN não encontrada no .env")

    if not host.startswith("https://"):
        fail("DATABRICKS_HOST deve começar com https://")

    print("🔐 Conectando ao Databricks...")

    try:
        client = WorkspaceClient(host=host, token=token)
        success("Autenticação realizada")
    except Exception as e:
        fail(f"Erro de autenticação: {e}")

    # 1️⃣ Workspace
    try:
        me = client.current_user.me()
        success(f"Usuário autenticado: {me.user_name}")
    except Exception as e:
        fail(f"Erro ao acessar usuário atual: {e}")

    # 2️⃣ Unity Catalog – listar catálogos
    print("\n📚 Testando Unity Catalog...")
    try:
        catalogs = list(client.catalogs.list())
        if not catalogs:
            fail("Nenhum catálogo encontrado (permissão insuficiente?)")

        success(f"{len(catalogs)} catálogos encontrados")
        for c in catalogs[:5]:
            print(f"   - {c.name}")
    except Exception as e:
        fail(f"Erro ao acessar Unity Catalog: {e}")

    # 3️⃣ Schemas (opcional, apenas 1 catálogo)
    try:
        catalog_name = catalogs[0].name
        schemas = list(client.schemas.list(catalog_name=catalog_name))
        success(f"{len(schemas)} schemas no catálogo '{catalog_name}'")
    except Exception as e:
        fail(f"Erro ao listar schemas: {e}")

    # 4️⃣ Model Serving Endpoints
    print("\n🤖 Testando Model Serving...")
    try:
        endpoints = list(client.serving_endpoints.list())
        if not endpoints:
            print("⚠️ Nenhum Model Serving Endpoint encontrado")
        else:
            success(f"{len(endpoints)} endpoints encontrados")
            for ep in endpoints:
                print(f"   - {ep.name}")
    except Exception as e:
        fail(f"Erro ao listar Model Serving Endpoints: {e}")

    print("\n🎉 CONCLUSÃO")
    print("Você tem acesso funcional ao Databricks:")
    print("- Workspace")
    print("- Unity Catalog")
    print("- Model Serving (se houver endpoints listados)")


if __name__ == "__main__":
    main()
