"""
Configuração de LLMs para a plataforma multiagente.
Suporta OpenAI, Google Gemini e Databricks Foundation Models.
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel


class LLMProvider(Enum):
    """Provedores de LLM suportados."""

    OPENAI = "openai"
    GOOGLE = "google"
    DATABRICKS = "databricks"


@dataclass
class LLMConfig:
    """Configuração de um modelo LLM."""

    provider: LLMProvider
    model_id: str
    display_name: str
    description: str
    env_key: str
    max_tokens: int = 4096
    temperature: float = 0.0


AVAILABLE_MODELS: dict[str, LLMConfig] = {
    "gpt-4o-mini": LLMConfig(
        provider=LLMProvider.OPENAI,
        model_id="gpt-4o-mini",
        display_name="GPT-4o Mini",
        description="Modelo rápido e econômico da OpenAI",
        env_key="OPENAI_API_KEY",
    ),
    "gpt-4o": LLMConfig(
        provider=LLMProvider.OPENAI,
        model_id="gpt-4o",
        display_name="GPT-4o",
        description="Modelo mais avançado da OpenAI",
        env_key="OPENAI_API_KEY",
    ),
    "gpt-4-turbo": LLMConfig(
        provider=LLMProvider.OPENAI,
        model_id="gpt-4-turbo",
        display_name="GPT-4 Turbo",
        description="Modelo GPT-4 otimizado para velocidade",
        env_key="OPENAI_API_KEY",
    ),
    "gemini-1.5-flash": LLMConfig(
        provider=LLMProvider.GOOGLE,
        model_id="gemini-1.5-flash",
        display_name="Gemini 1.5 Flash",
        description="Modelo rápido do Google",
        env_key="GOOGLE_API_KEY",
    ),
    "gemini-1.5-pro": LLMConfig(
        provider=LLMProvider.GOOGLE,
        model_id="gemini-1.5-pro",
        display_name="Gemini 1.5 Pro",
        description="Modelo avançado do Google",
        env_key="GOOGLE_API_KEY",
    ),
    "gemini-2.0-flash": LLMConfig(
        provider=LLMProvider.GOOGLE,
        model_id="gemini-2.0-flash-exp",
        display_name="Gemini 2.0 Flash",
        description="Modelo mais recente do Google",
        env_key="GOOGLE_API_KEY",
    ),
    "databricks-dbrx-instruct": LLMConfig(
        provider=LLMProvider.DATABRICKS,
        model_id="databricks-dbrx-instruct",
        display_name="DBRX Instruct",
        description="Modelo DBRX da Databricks",
        env_key="DATABRICKS_TOKEN",
    ),
    "databricks-llama-3-70b": LLMConfig(
        provider=LLMProvider.DATABRICKS,
        model_id="databricks-meta-llama-3-70b-instruct",
        display_name="Llama 3 70B",
        description="Meta Llama 3 70B via Databricks",
        env_key="DATABRICKS_TOKEN",
    ),
    "databricks-mixtral-8x7b": LLMConfig(
        provider=LLMProvider.DATABRICKS,
        model_id="databricks-mixtral-8x7b-instruct",
        display_name="Mixtral 8x7B",
        description="Mixtral 8x7B via Databricks",
        env_key="DATABRICKS_TOKEN",
    ),
}

DEFAULT_MODEL = "gpt-4o-mini"


def check_api_key_available(provider: LLMProvider) -> bool:
    """Verifica se a API key do provedor está disponível."""
    if provider == LLMProvider.OPENAI:
        return bool(os.getenv("OPENAI_API_KEY"))
    elif provider == LLMProvider.GOOGLE:
        return bool(os.getenv("GOOGLE_API_KEY"))
    elif provider == LLMProvider.DATABRICKS:
        return bool(os.getenv("DATABRICKS_TOKEN")) and bool(os.getenv("DATABRICKS_HOST"))
    return False


def get_available_models() -> list[str]:
    """Retorna lista de IDs de modelos disponíveis."""
    return list(AVAILABLE_MODELS.keys())


def get_available_models_with_keys() -> list[str]:
    """Retorna lista de modelos cujas API keys estão configuradas."""
    available = []
    for model_id, config in AVAILABLE_MODELS.items():
        if check_api_key_available(config.provider):
            available.append(model_id)
    return available


def get_model_config(model_id: str) -> LLMConfig | None:
    """Retorna configuração de um modelo específico."""
    return AVAILABLE_MODELS.get(model_id)


def get_model_display_info(model_id: str) -> dict[str, str]:
    """Retorna informações de exibição de um modelo."""
    config = AVAILABLE_MODELS.get(model_id)
    if config:
        return {
            "id": model_id,
            "name": config.display_name,
            "description": config.description,
            "provider": config.provider.value,
        }
    return {}


def get_models_by_provider(provider: LLMProvider) -> list[str]:
    """Retorna lista de modelos de um provedor específico."""
    return [
        model_id
        for model_id, config in AVAILABLE_MODELS.items()
        if config.provider == provider
    ]


def create_llm(
    model_id: str | None = None,
    temperature: float | None = None,
    **kwargs: Any,
) -> BaseChatModel:
    """
    Cria uma instância de LLM baseada no modelo especificado.

    Args:
        model_id: ID do modelo (usa DEFAULT_MODEL se não especificado)
        temperature: Temperatura para geração (usa config padrão se não especificado)
        **kwargs: Argumentos adicionais para o LLM

    Returns:
        Instância de BaseChatModel configurada

    Raises:
        ValueError: Se o modelo não for encontrado ou API key não estiver configurada
    """
    if model_id is None:
        model_id = DEFAULT_MODEL

    config = AVAILABLE_MODELS.get(model_id)
    if not config:
        raise ValueError(f"Modelo não encontrado: {model_id}")

    if not check_api_key_available(config.provider):
        raise ValueError(
            f"API key não configurada para {config.provider.value}. "
            f"Configure a variável de ambiente {config.env_key}"
        )

    temp = temperature if temperature is not None else config.temperature

    if config.provider == LLMProvider.OPENAI:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=config.model_id,
            temperature=temp,
            max_tokens=config.max_tokens,
            **kwargs,
        )

    elif config.provider == LLMProvider.GOOGLE:
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=config.model_id,
            temperature=temp,
            max_output_tokens=config.max_tokens,
            **kwargs,
        )

    elif config.provider == LLMProvider.DATABRICKS:
        return _create_databricks_llm(config, temp, **kwargs)

    raise ValueError(f"Provedor não suportado: {config.provider}")


def _create_databricks_llm(
    config: LLMConfig,
    temperature: float,
    **kwargs: Any,
) -> BaseChatModel:
    """
    Cria uma instância de LLM Databricks usando databricks-sdk.

    Args:
        config: Configuração do modelo
        temperature: Temperatura para geração
        **kwargs: Argumentos adicionais

    Returns:
        Instância de ChatModel para Databricks
    """
    from app.config.databricks_llm import ChatDatabricks

    host = os.getenv("DATABRICKS_HOST", "")
    token = os.getenv("DATABRICKS_TOKEN", "")

    endpoint = os.getenv("DATABRICKS_MODEL_ENDPOINT", config.model_id)

    return ChatDatabricks(
        host=host,
        token=token,
        endpoint=endpoint,
        temperature=temperature,
        max_tokens=config.max_tokens,
        **kwargs,
    )
