"""
Configuração de LLMs para a plataforma multiagente.
Usa a camada central de modelos (models.py) como fonte única de verdade.
Suporta OpenAI e Databricks Foundation Models.
"""

import os
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel

from app.config.models import (
    DEFAULT_MODEL,
    MODELS_REGISTRY,
    ModelProvider,
    check_provider_available,
)
from app.config.models import (
    get_model_config as get_model_config_from_registry,
)


def create_llm(
    model_id: str | None = None,
    temperature: float | None = None,
    **kwargs: Any,
) -> BaseChatModel:
    """
    Cria uma instância de LLM baseada no modelo especificado.
    Usa a configuração central de models.py.

    Args:
        model_id: ID do modelo (usa DEFAULT_MODEL se não especificado)
        temperature: Temperatura para geração (usa config padrão se não especificado)
        **kwargs: Argumentos adicionais para o LLM

    Returns:
        Instância de BaseChatModel configurada

    Raises:
        ValueError: Se o modelo não for encontrado ou API key não estiver configurada
    """
    print(f"[DEBUG] create_llm called with model_id: {model_id}")

    if model_id is None:
        model_id = DEFAULT_MODEL
        print(f"[DEBUG] Using DEFAULT_MODEL: {model_id}")

    config = get_model_config_from_registry(model_id)
    if not config:
        print(f"[DEBUG] ERROR: Model not found in MODELS_REGISTRY: {model_id}")
        print(f"[DEBUG] Available models: {list(MODELS_REGISTRY.keys())}")
        raise ValueError(f"Modelo não encontrado: {model_id}")

    print(f"[DEBUG] Model config found: {config.display_name}")
    print(f"[DEBUG] Provider: {config.provider.value}")
    print(f"[DEBUG] Endpoint: {config.endpoint_name or config.model_name}")

    if not check_provider_available(config.provider):
        env_key = "DATABRICKS_HOST/DATABRICKS_TOKEN" if config.provider == ModelProvider.DATABRICKS else "OPENAI_API_KEY"
        raise ValueError(
            f"API key não configurada para {config.provider.value}. "
            f"Configure a variável de ambiente {env_key}"
        )

    temp = temperature if temperature is not None else config.temperature

    if config.provider == ModelProvider.OPENAI:
        from langchain_openai import ChatOpenAI

        print(f"[DEBUG] Creating ChatOpenAI with model: {config.model_name}")
        return ChatOpenAI(
            model=config.model_name,
            temperature=temp,
            max_tokens=config.max_tokens,
            **kwargs,
        )

    elif config.provider == ModelProvider.DATABRICKS:
        print(f"[DEBUG] Creating ChatDatabricks with endpoint: {config.endpoint_name}")
        return _create_databricks_llm(config, temp, **kwargs)

    raise ValueError(f"Provedor não suportado: {config.provider}")


def _create_databricks_llm(
    config: Any,
    temperature: float,
    **kwargs: Any,
) -> BaseChatModel:
    """
    Cria uma instância de LLM Databricks usando databricks-sdk.

    Args:
        config: Configuração do modelo (ModelConfig de models.py)
        temperature: Temperatura para geração
        **kwargs: Argumentos adicionais

    Returns:
        Instância de ChatModel para Databricks
    """
    from app.config.databricks_llm import ChatDatabricks

    host = os.getenv("DATABRICKS_HOST", "")
    token = os.getenv("DATABRICKS_TOKEN", "")

    endpoint = config.endpoint_name or config.model_name

    print(f"[DEBUG] Databricks host: {host[:30]}..." if len(host) > 30 else f"[DEBUG] Databricks host: {host}")
    print(f"[DEBUG] Databricks endpoint: {endpoint}")

    return ChatDatabricks(
        host=host,
        token=token,
        endpoint=endpoint,
        temperature=temperature,
        max_tokens=config.max_tokens,
        **kwargs,
    )
