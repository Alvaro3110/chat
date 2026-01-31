#!/usr/bin/env python3
"""
test_debug.py - Arquivo de DEBUG para o pipeline multiagente.

Este arquivo é o instrumento oficial de diagnóstico.
Executa o orquestrador multiagente com um modelo Databricks
e imprime todas as informações de debug no terminal.

Uso:
    PYTHONPATH=. python test_debug.py
    PYTHONPATH=. python test_debug.py --model databricks-qwen3-next-80b-a3b-instruct
    PYTHONPATH=. python test_debug.py --list-models
"""

import argparse
import os
import sys

from dotenv import load_dotenv

load_dotenv()


def print_header(title: str) -> None:
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def print_section(title: str) -> None:
    print("\n" + "-" * 50)
    print(f" {title}")
    print("-" * 50)


def check_environment() -> bool:
    print_header("VERIFICAÇÃO DE AMBIENTE")

    databricks_host = os.getenv("DATABRICKS_HOST")
    databricks_token = os.getenv("DATABRICKS_TOKEN")
    openai_key = os.getenv("OPENAI_API_KEY")

    print(f"DATABRICKS_HOST: {'configurado' if databricks_host else 'NÃO CONFIGURADO'}")
    print(f"DATABRICKS_TOKEN: {'configurado' if databricks_token else 'NÃO CONFIGURADO'}")
    print(f"OPENAI_API_KEY: {'configurado' if openai_key else 'NÃO CONFIGURADO'}")

    if not databricks_host or not databricks_token:
        print("\n[ERRO] Databricks não está configurado!")
        print("[ERRO] Configure DATABRICKS_HOST e DATABRICKS_TOKEN no arquivo .env")
        return False

    return True


def list_available_models() -> None:
    print_header("MODELOS DISPONÍVEIS")

    try:
        from app.config.models import (
            ModelProvider,
            ModelTask,
            get_model_config,
            get_models_by_provider,
        )

        print("\n--- MODELOS DATABRICKS (CHAT) ---")
        databricks_models = get_models_by_provider(ModelProvider.DATABRICKS)
        for model_id in databricks_models:
            config = get_model_config(model_id)
            if config and config.task == ModelTask.CHAT:
                print(f"  {model_id}")
                print(f"    Display: {config.display_name}")
                print(f"    Endpoint: {config.endpoint_name}")
                print()

        print("\n--- MODELOS DATABRICKS (EMBEDDING) ---")
        for model_id in databricks_models:
            config = get_model_config(model_id)
            if config and config.task == ModelTask.EMBEDDING:
                print(f"  {model_id}")
                print(f"    Display: {config.display_name}")
                print(f"    Endpoint: {config.endpoint_name}")
                print()

        print("\n--- MODELOS OPENAI ---")
        openai_models = get_models_by_provider(ModelProvider.OPENAI)
        for model_id in openai_models:
            config = get_model_config(model_id)
            if config:
                print(f"  {model_id}")
                print(f"    Display: {config.display_name}")
                print(f"    Supports Tools: {config.supports_tools}")
                print()

    except ImportError as e:
        print(f"[ERRO] Falha ao importar módulos: {e}")
        sys.exit(1)


def run_pipeline_test(model_id: str, query: str) -> None:
    print_header("TESTE DO PIPELINE MULTIAGENTE")

    try:
        from app.config.models import DEFAULT_MODEL, get_model_config
        from app.orchestration.graph import create_deep_orchestrator_instance

        if not model_id:
            model_id = DEFAULT_MODEL

        print(f"\nModelo selecionado: {model_id}")

        model_config = get_model_config(model_id)
        if not model_config:
            print(f"[ERRO] Modelo {model_id} não encontrado no registry!")
            sys.exit(1)

        print(f"Provider: {model_config.provider.value}")
        print(f"Display name: {model_config.display_name}")
        print(f"Endpoint: {model_config.endpoint_name or model_config.model_name}")
        print(f"Task: {model_config.task.value}")
        print(f"Supports tools: {model_config.supports_tools}")

        print_section("CRIANDO ORQUESTRADOR")

        orchestrator = create_deep_orchestrator_instance(
            session=None,
            user_id="test_debug_user",
            model_id=model_id,
            debug_mode=True,
        )
        print("Orquestrador criado com sucesso")

        print_section("EXECUTANDO PERGUNTA DE TESTE")

        print(f"\nPergunta: '{query}'")
        print("\nFluxo esperado:")
        print("  1. Memory Recall")
        print("  2. Ambiguity Resolver")
        print("  3. Planner")
        print("  4. Executor (Subagentes + ReportAgent)")
        print("  5. Visualization (condicional)")
        print("  6. Critic")
        print("  7. Response")
        print("  8. Memory Persist")

        print("\n" + "=" * 70)
        print(" INICIANDO EXECUÇÃO DO PIPELINE")
        print("=" * 70)

        result = orchestrator.process_query(
            query=query,
            active_domains=["Cadastro", "Financeiro", "Rentabilidade"],
            group_context={
                "codigo_grupo": "TESTE001",
                "nome_grupo": "Grupo de Teste",
                "cnpj": "12.345.678/0001-90",
                "razao_social": "Empresa Teste LTDA",
            },
        )

        print_header("RESULTADO DO PIPELINE")

        print(f"\nTipo do resultado: {type(result).__name__}")
        print(f"Chaves do resultado: {list(result.keys())}")

        print_section("RELATÓRIO CONSOLIDADO (final_report)")
        final_report = result.get("final_report", "")
        print(f"Tamanho: {len(final_report)} caracteres")
        if final_report:
            print(f"\nConteúdo:\n{final_report[:1000]}...")
        else:
            print("[AVISO] Relatório consolidado vazio!")

        print_section("VALIDAÇÃO DO CRITIC")
        validation = result.get("validation", {})
        print(f"is_valid: {validation.get('is_valid', 'N/A')}")
        print(f"completeness_score: {validation.get('completeness_score', 'N/A')}")
        print(f"summary: {validation.get('summary', 'N/A')}")
        issues = validation.get("issues", [])
        if issues:
            print(f"issues: {issues}")

        print_section("RESPOSTA FINAL")
        response = result.get("response", "")
        print(f"Tamanho: {len(response)} caracteres")
        if response:
            print(f"\nConteúdo:\n{response}")
        else:
            print("[AVISO] Resposta final vazia!")

        print_section("STATUS DA MEMÓRIA")
        memory_status = result.get("memory_status", {})
        for key, value in memory_status.items():
            status = "OK" if value else "X"
            print(f"  [{status}] {key}: {value}")

        print_section("FONTES CONSULTADAS")
        sources = result.get("sources", [])
        if sources:
            for source in sources:
                print(f"  - {source}")
        else:
            print("  Nenhuma fonte registrada")

        print_section("VISUALIZAÇÃO")
        viz_suggestion = result.get("visualization_suggestion")
        viz_data = result.get("visualization_data")
        print(f"Sugestão: {viz_suggestion}")
        print(f"Dados: {viz_data}")

        print_header("ANÁLISE DE QUALIDADE")

        issues_found = []

        if not final_report or len(final_report) < 50:
            issues_found.append("Relatório consolidado vazio ou muito curto")

        if not response or len(response) < 50:
            issues_found.append("Resposta final vazia ou muito curta")

        generic_phrases = [
            "forneça mais contexto",
            "preciso de mais informações",
            "não tenho dados suficientes",
            "por favor, especifique",
        ]
        response_lower = response.lower() if response else ""
        for phrase in generic_phrases:
            if phrase in response_lower:
                issues_found.append(f"Resposta contém frase genérica: '{phrase}'")

        if not validation.get("is_valid", True):
            issues_found.append(f"Critic marcou como inválido: {validation.get('summary', '')}")

        if issues_found:
            print("\n[PROBLEMAS ENCONTRADOS]")
            for issue in issues_found:
                print(f"  - {issue}")
        else:
            print("\n[OK] Nenhum problema crítico encontrado")

        print_header("TESTE CONCLUÍDO")

    except Exception as e:
        print(f"\n[ERRO] Falha durante execução: {e}")
        import traceback
        print(f"\nStack trace:\n{traceback.format_exc()}")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Debug do pipeline multiagente",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  PYTHONPATH=. python test_debug.py
  PYTHONPATH=. python test_debug.py --model databricks-qwen3-next-80b-a3b-instruct
  PYTHONPATH=. python test_debug.py --query "qual a rentabilidade do cliente?"
  PYTHONPATH=. python test_debug.py --list-models
        """,
    )

    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="ID do modelo a usar (default: databricks-meta-llama-3-3-70b-instruct)",
    )

    parser.add_argument(
        "--query",
        type=str,
        default="Qual a situação financeira e rentabilidade do cliente?",
        help="Pergunta de teste",
    )

    parser.add_argument(
        "--list-models",
        action="store_true",
        help="Lista todos os modelos disponíveis e sai",
    )

    args = parser.parse_args()

    print_header("TEST_DEBUG.PY - DIAGNÓSTICO DO PIPELINE MULTIAGENTE")

    if not check_environment():
        sys.exit(1)

    if args.list_models:
        list_available_models()
        sys.exit(0)

    run_pipeline_test(args.model, args.query)


if __name__ == "__main__":
    main()
