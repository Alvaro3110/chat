"""
Configuração de provedores de LLM.
Suporta OpenAI (ChatGPT) e Google (Gemini).
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Any

from langchain_core.language_models import BaseChatModel


class LLMProvider(str, Enum):
    """Provedores de LLM suportados."""

    OPENAI = "openai"
    GEMINI = "gemini"


@dataclass
class LLMConfig:
    """Configuração de um provedor de LLM."""

    provider: LLMProvider
    model_name: str
    display_name: str
    description: str
    requires_api_key: str


AVAILABLE_MODELS: dict[str, LLMConfig] = {
    "gpt-4o-mini": LLMConfig(
        provider=LLMProvider.OPENAI,
        model_name="gpt-4o-mini",
        display_name="GPT-4o Mini (OpenAI)",
        description="Modelo rápido e econômico da OpenAI",
        requires_api_key="OPENAI_API_KEY",
    ),
    "gpt-4o": LLMConfig(
        provider=LLMProvider.OPENAI,
        model_name="gpt-4o",
        display_name="GPT-4o (OpenAI)",
        description="Modelo mais avançado da OpenAI",
        requires_api_key="OPENAI_API_KEY",
    ),
    "gpt-4-turbo": LLMConfig(
        provider=LLMProvider.OPENAI,
        model_name="gpt-4-turbo",
        display_name="GPT-4 Turbo (OpenAI)",
        description="Modelo GPT-4 otimizado para velocidade",
        requires_api_key="OPENAI_API_KEY",
    ),
    "gemini-1.5-flash": LLMConfig(
        provider=LLMProvider.GEMINI,
        model_name="gemini-1.5-flash",
        display_name="Gemini 1.5 Flash (Google)",
        description="Modelo rápido e eficiente do Google",
        requires_api_key="GOOGLE_API_KEY",
    ),
    "gemini-1.5-pro": LLMConfig(
        provider=LLMProvider.GEMINI,
        model_name="gemini-1.5-pro",
        display_name="Gemini 1.5 Pro (Google)",
        description="Modelo mais avançado do Google",
        requires_api_key="GOOGLE_API_KEY",
    ),
    "gemini-2.0-flash": LLMConfig(
        provider=LLMProvider.GEMINI,
        model_name="gemini-2.0-flash-exp",
        display_name="Gemini 2.0 Flash (Google)",
        description="Modelo experimental mais recente do Google",
        requires_api_key="GOOGLE_API_KEY",
    ),
}

DEFAULT_MODEL = "gpt-4o-mini"


def get_available_models() -> list[str]:
    """Retorna lista de modelos disponíveis."""
    return list(AVAILABLE_MODELS.keys())


def get_model_config(model_id: str) -> LLMConfig | None:
    """Retorna configuração de um modelo específico."""
    return AVAILABLE_MODELS.get(model_id)


def get_models_by_provider(provider: LLMProvider) -> list[str]:
    """Retorna modelos de um provedor específico."""
    return [
        model_id
        for model_id, config in AVAILABLE_MODELS.items()
        if config.provider == provider
    ]


def check_api_key_available(model_id: str) -> bool:
    """Verifica se a API key necessária está disponível."""
    config = get_model_config(model_id)
    if not config:
        return False
    return bool(os.getenv(config.requires_api_key))


def get_available_models_with_keys() -> list[str]:
    """Retorna apenas modelos cujas API keys estão configuradas."""
    return [
        model_id
        for model_id in AVAILABLE_MODELS
        if check_api_key_available(model_id)
    ]


def create_llm(
    model_id: str | None = None,
    temperature: float = 0,
    **kwargs: Any,
) -> BaseChatModel:
    """
    Cria uma instância do LLM baseado no modelo selecionado.

    Args:
        model_id: ID do modelo (usa DEFAULT_MODEL se não especificado)
        temperature: Temperatura para geração
        **kwargs: Argumentos adicionais para o modelo

    Returns:
        Instância do LLM configurado

    Raises:
        ValueError: Se o modelo não for suportado ou API key não estiver disponível
    """
    if model_id is None:
        model_id = DEFAULT_MODEL

    config = get_model_config(model_id)
    if not config:
        raise ValueError(f"Modelo não suportado: {model_id}")

    api_key = os.getenv(config.requires_api_key)
    if not api_key:
        raise ValueError(
            f"API key não encontrada. Configure {config.requires_api_key} no ambiente."
        )

    if config.provider == LLMProvider.OPENAI:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=config.model_name,
            temperature=temperature,
            api_key=api_key,
            **kwargs,
        )
    elif config.provider == LLMProvider.GEMINI:
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=config.model_name,
            temperature=temperature,
            google_api_key=api_key,
            **kwargs,
        )
    else:
        raise ValueError(f"Provedor não implementado: {config.provider}")


def get_model_display_info() -> list[dict[str, str]]:
    """Retorna informações de exibição dos modelos disponíveis."""
    return [
        {
            "id": model_id,
            "display_name": config.display_name,
            "description": config.description,
            "provider": config.provider.value,
            "available": check_api_key_available(model_id),
        }
        for model_id, config in AVAILABLE_MODELS.items()
    ]
