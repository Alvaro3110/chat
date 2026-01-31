#!/usr/bin/env python3
"""
teste.py - Arquivo de DEBUG para o pipeline multiagente.

Este arquivo é o instrumento oficial de diagnóstico.
Executa o orquestrador multiagente com um modelo Databricks
e imprime todas as informações de debug no terminal.

Uso:
    PYTHONPATH=. python teste.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("TESTE DE DEBUG - PIPELINE MULTIAGENTE")
print("=" * 60)

print("\n[DEBUG] Verificando variáveis de ambiente...")
databricks_host = os.getenv("DATABRICKS_HOST")
databricks_token = os.getenv("DATABRICKS_TOKEN")
openai_key = os.getenv("OPENAI_API_KEY")

print(f"[DEBUG] DATABRICKS_HOST: {'configurado' if databricks_host else 'NÃO CONFIGURADO'}")
print(f"[DEBUG] DATABRICKS_TOKEN: {'configurado' if databricks_token else 'NÃO CONFIGURADO'}")
print(f"[DEBUG] OPENAI_API_KEY: {'configurado' if openai_key else 'NÃO CONFIGURADO'}")

if not databricks_host or not databricks_token:
    print("\n[ERRO] Databricks não está configurado!")
    print("[ERRO] Configure DATABRICKS_HOST e DATABRICKS_TOKEN no arquivo .env")
    sys.exit(1)

print("\n[DEBUG] Importando módulos...")

try:
    from app.config.models import (
        DEFAULT_MODEL,
        ModelProvider,
        get_model_config,
        get_models_by_provider,
    )
    print("[DEBUG] Módulo models importado com sucesso")
except ImportError as e:
    print(f"[ERRO] Falha ao importar models: {e}")
    sys.exit(1)

try:
    from app.orchestration.graph import (
        create_deep_orchestrator_instance,
    )
    print("[DEBUG] Módulo graph importado com sucesso")
except ImportError as e:
    print(f"[ERRO] Falha ao importar graph: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("MODELOS DATABRICKS DISPONÍVEIS")
print("=" * 60)

databricks_models = get_models_by_provider(ModelProvider.DATABRICKS)
for model_id in databricks_models:
    config = get_model_config(model_id)
    if config:
        print(f"  - {model_id}")
        print(f"    Display: {config.display_name}")
        print(f"    Task: {config.task.value}")
        print(f"    Endpoint: {config.endpoint_name}")
        print()

print("=" * 60)
print("INICIANDO TESTE DO PIPELINE")
print("=" * 60)

model_id = DEFAULT_MODEL
print(f"\n[DEBUG] Modelo selecionado: {model_id}")

model_config = get_model_config(model_id)
if model_config:
    print(f"[DEBUG] Provider: {model_config.provider.value}")
    print(f"[DEBUG] Display name: {model_config.display_name}")
    print(f"[DEBUG] Endpoint: {model_config.endpoint_name}")
    print(f"[DEBUG] Task: {model_config.task.value}")
    print(f"[DEBUG] Supports tools: {model_config.supports_tools}")
else:
    print(f"[ERRO] Modelo {model_id} não encontrado no registry!")
    sys.exit(1)

print("\n[DEBUG] Criando orquestrador multiagente...")

try:
    orchestrator = create_deep_orchestrator_instance(
        session=None,
        user_id="teste_debug",
        model_id=model_id,
    )
    print("[DEBUG] Orquestrador criado com sucesso")
except Exception as e:
    print(f"[ERRO] Falha ao criar orquestrador: {e}")
    import traceback
    print(f"[DEBUG] Stack trace:\n{traceback.format_exc()}")
    sys.exit(1)

print("\n" + "=" * 60)
print("EXECUTANDO PERGUNTA DE TESTE")
print("=" * 60)

test_query = "testando pipeline"
print(f"\n[DEBUG] Pergunta: '{test_query}'")

print("\n[DEBUG] Processando pergunta via orquestrador multiagente...")
print("[DEBUG] Fluxo esperado:")
print("  1. Memory Recall")
print("  2. Ambiguity Resolver")
print("  3. Planner")
print("  4. Executor (Subagentes)")
print("  5. Visualization")
print("  6. Critic")
print("  7. Response")
print("  8. Memory Persist")

print("\n" + "-" * 60)

try:
    result = orchestrator.process_query(
        query=test_query,
        active_domains=["Cadastro", "Financeiro"],
        group_context={"codigo_grupo": "TESTE001", "nome_grupo": "Grupo de Teste"},
    )

    print("\n" + "-" * 60)
    print("\n[DEBUG] ========== RESULTADO DO PIPELINE ==========")

    print(f"\n[DEBUG] Tipo do resultado: {type(result).__name__}")
    print(f"[DEBUG] Chaves do resultado: {list(result.keys())}")

    response = result.get("response", "")
    print(f"\n[DEBUG] Tipo da resposta: {type(response).__name__}")
    print(f"[DEBUG] Tamanho da resposta: {len(response)} caracteres")

    print("\n[DEBUG] ========== RESPOSTA FINAL ==========")
    print(response)
    print("=" * 60)

    memory_status = result.get("memory_status", {})
    print("\n[DEBUG] ========== STATUS DO PIPELINE ==========")
    for key, value in memory_status.items():
        status = "✔" if value else "✗"
        print(f"  {status} {key}: {value}")

    normalized_query = result.get("normalized_query", "")
    print(f"\n[DEBUG] Pergunta normalizada: {normalized_query}")

    validation = result.get("validation", {})
    print(f"[DEBUG] Validação: {validation}")

    print("\n" + "=" * 60)
    print("TESTE CONCLUÍDO COM SUCESSO")
    print("=" * 60)

except Exception as e:
    print(f"\n[ERRO] Falha ao processar pergunta: {e}")
    import traceback
    print(f"[DEBUG] Stack trace:\n{traceback.format_exc()}")
    sys.exit(1)
