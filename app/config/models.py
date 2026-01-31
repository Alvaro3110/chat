"""
Camada central de modelos para a plataforma multiagente.
Configuração declarativa de todos os modelos suportados.
"""

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ModelProvider(Enum):
    """Provedores de modelo suportados."""
    DATABRICKS = "databricks"
    OPENAI = "openai"


class ModelTask(Enum):
    """Tipos de tarefa suportados."""
    CHAT = "chat"
    CODE = "code"
    EMBEDDING = "embedding"


@dataclass
class ModelConfig:
    """Configuração declarativa de um modelo."""
    provider: ModelProvider
    display_name: str
    task: ModelTask
    enabled: bool = True
    endpoint_name: str | None = None
    model_name: str | None = None
    description: str = ""
    max_tokens: int = 4096
    temperature: float = 0.0
    supports_tools: bool = False
    extra_config: dict[str, Any] = field(default_factory=dict)


MODELS_REGISTRY: dict[str, ModelConfig] = {
    "databricks-meta-llama-3-3-70b-instruct": ModelConfig(
        provider=ModelProvider.DATABRICKS,
        display_name="Llama 3.3 70B Instruct",
        task=ModelTask.CHAT,
        endpoint_name="databricks-meta-llama-3-3-70b-instruct",
        description="Meta Llama 3.3 70B via Databricks Model Serving",
        enabled=True,
        supports_tools=False,
    ),
    "databricks-gpt-5-2": ModelConfig(
        provider=ModelProvider.DATABRICKS,
        display_name="GPT-5.2",
        task=ModelTask.CHAT,
        endpoint_name="databricks-gpt-5-2",
        description="GPT-5.2 via Databricks Model Serving",
        enabled=True,
        supports_tools=False,
    ),
    "databricks-dbrx-instruct": ModelConfig(
        provider=ModelProvider.DATABRICKS,
        display_name="DBRX Instruct",
        task=ModelTask.CHAT,
        endpoint_name="databricks-dbrx-instruct",
        description="Modelo DBRX da Databricks",
        enabled=True,
        supports_tools=False,
    ),
    "databricks-mixtral-8x7b-instruct": ModelConfig(
        provider=ModelProvider.DATABRICKS,
        display_name="Mixtral 8x7B Instruct",
        task=ModelTask.CHAT,
        endpoint_name="databricks-mixtral-8x7b-instruct",
        description="Mixtral 8x7B via Databricks Model Serving",
        enabled=True,
        supports_tools=False,
    ),
    "gpt-4o-mini": ModelConfig(
        provider=ModelProvider.OPENAI,
        display_name="GPT-4o Mini",
        task=ModelTask.CHAT,
        model_name="gpt-4o-mini",
        description="Modelo rápido e econômico da OpenAI (fallback)",
        enabled=True,
        supports_tools=True,
    ),
    "gpt-4o": ModelConfig(
        provider=ModelProvider.OPENAI,
        display_name="GPT-4o",
        task=ModelTask.CHAT,
        model_name="gpt-4o",
        description="Modelo mais avançado da OpenAI",
        enabled=True,
        supports_tools=True,
    ),
    "gpt-4-turbo": ModelConfig(
        provider=ModelProvider.OPENAI,
        display_name="GPT-4 Turbo",
        task=ModelTask.CHAT,
        model_name="gpt-4-turbo",
        description="GPT-4 otimizado para velocidade",
        enabled=True,
        supports_tools=True,
    ),
}

DEFAULT_MODEL = "databricks-meta-llama-3-3-70b-instruct"
FALLBACK_MODEL = "gpt-4o-mini"


def check_provider_available(provider: ModelProvider) -> bool:
    """Verifica se o provedor está configurado."""
    if provider == ModelProvider.DATABRICKS:
        host = os.getenv("DATABRICKS_HOST")
        token = os.getenv("DATABRICKS_TOKEN")
        available = bool(host and token)
        logger.debug(f"[DEBUG] Databricks provider check: host={bool(host)}, token={bool(token)}, available={available}")
        return available
    elif provider == ModelProvider.OPENAI:
        key = os.getenv("OPENAI_API_KEY")
        available = bool(key)
        logger.debug(f"[DEBUG] OpenAI provider check: available={available}")
        return available
    return False


def get_model_config(model_id: str) -> ModelConfig | None:
    """Retorna configuração de um modelo específico."""
    return MODELS_REGISTRY.get(model_id)


def get_enabled_models() -> list[str]:
    """Retorna lista de modelos habilitados."""
    return [
        model_id
        for model_id, config in MODELS_REGISTRY.items()
        if config.enabled
    ]


def get_available_models() -> list[str]:
    """Retorna lista de modelos habilitados e com provedor configurado."""
    available = []
    for model_id, config in MODELS_REGISTRY.items():
        if config.enabled and check_provider_available(config.provider):
            available.append(model_id)
    return available


def get_models_by_provider(provider: ModelProvider) -> list[str]:
    """Retorna lista de modelos de um provedor específico."""
    return [
        model_id
        for model_id, config in MODELS_REGISTRY.items()
        if config.provider == provider and config.enabled
    ]


def get_models_by_task(task: ModelTask) -> list[str]:
    """Retorna lista de modelos por tipo de tarefa."""
    return [
        model_id
        for model_id, config in MODELS_REGISTRY.items()
        if config.task == task and config.enabled
    ]


def get_chat_models() -> list[str]:
    """Retorna lista de modelos de chat disponíveis."""
    return get_models_by_task(ModelTask.CHAT)


def get_model_display_info(model_id: str) -> dict[str, str]:
    """Retorna informações de exibição de um modelo."""
    config = MODELS_REGISTRY.get(model_id)
    if config:
        return {
            "id": model_id,
            "name": config.display_name,
            "provider": config.provider.value,
            "task": config.task.value,
            "description": config.description,
            "supports_tools": str(config.supports_tools),
        }
    return {}


def get_all_providers() -> list[tuple[str, ModelProvider]]:
    """Retorna lista de todos os provedores com nomes de exibição."""
    return [
        ("Databricks", ModelProvider.DATABRICKS),
        ("OpenAI", ModelProvider.OPENAI),
    ]


def get_available_providers() -> list[tuple[str, ModelProvider]]:
    """Retorna lista de provedores configurados."""
    available = []
    for name, provider in get_all_providers():
        if check_provider_available(provider):
            available.append((name, provider))
    return available
