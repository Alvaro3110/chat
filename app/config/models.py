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
    "databricks-gpt-5-2": ModelConfig(
        provider=ModelProvider.DATABRICKS,
        display_name="GPT-5.2",
        task=ModelTask.CHAT,
        endpoint_name="databricks-gpt-5-2",
        description="GPT-5.2 via Databricks Model Serving",
        enabled=True,
        supports_tools=False,
    ),
    "databricks-gpt-5-1": ModelConfig(
        provider=ModelProvider.DATABRICKS,
        display_name="GPT-5.1",
        task=ModelTask.CHAT,
        endpoint_name="databricks-gpt-5-1",
        description="GPT-5.1 via Databricks Model Serving",
        enabled=True,
        supports_tools=False,
    ),
    "databricks-gpt-oss-120b": ModelConfig(
        provider=ModelProvider.DATABRICKS,
        display_name="GPT-OSS 120B",
        task=ModelTask.CHAT,
        endpoint_name="databricks-gpt-oss-120b",
        description="GPT-OSS 120B via Databricks Model Serving",
        enabled=True,
        supports_tools=False,
    ),
    "databricks-gpt-oss-20b": ModelConfig(
        provider=ModelProvider.DATABRICKS,
        display_name="GPT-OSS 20B",
        task=ModelTask.CHAT,
        endpoint_name="databricks-gpt-oss-20b",
        description="GPT-OSS 20B via Databricks Model Serving",
        enabled=True,
        supports_tools=False,
    ),
    "databricks-meta-llama-3-3-70b-instruct": ModelConfig(
        provider=ModelProvider.DATABRICKS,
        display_name="Llama 3.3 70B Instruct",
        task=ModelTask.CHAT,
        endpoint_name="databricks-meta-llama-3-3-70b-instruct",
        description="Meta Llama 3.3 70B via Databricks Model Serving",
        enabled=True,
        supports_tools=False,
    ),
    "databricks-meta-llama-3-1-8b-instruct": ModelConfig(
        provider=ModelProvider.DATABRICKS,
        display_name="Llama 3.1 8B Instruct",
        task=ModelTask.CHAT,
        endpoint_name="databricks-meta-llama-3-1-8b-instruct",
        description="Meta Llama 3.1 8B via Databricks Model Serving",
        enabled=True,
        supports_tools=False,
    ),
    "databricks-meta-llama-3-1-405b-instruct": ModelConfig(
        provider=ModelProvider.DATABRICKS,
        display_name="Llama 3.1 405B Instruct",
        task=ModelTask.CHAT,
        endpoint_name="databricks-meta-llama-3-1-405b-instruct",
        description="Meta Llama 3.1 405B via Databricks Model Serving",
        enabled=True,
        supports_tools=False,
    ),
    "databricks-qwen3-next-80b-a3b-instruct": ModelConfig(
        provider=ModelProvider.DATABRICKS,
        display_name="Qwen3 Next 80B Instruct",
        task=ModelTask.CHAT,
        endpoint_name="databricks-qwen3-next-80b-a3b-instruct",
        description="Qwen3 Next 80B via Databricks Model Serving",
        enabled=True,
        supports_tools=False,
    ),
    "databricks-llama-4-maverick": ModelConfig(
        provider=ModelProvider.DATABRICKS,
        display_name="Llama 4 Maverick",
        task=ModelTask.CHAT,
        endpoint_name="databricks-llama-4-maverick",
        description="Llama 4 Maverick via Databricks Model Serving",
        enabled=True,
        supports_tools=False,
    ),
    "databricks-gemma-3-12b": ModelConfig(
        provider=ModelProvider.DATABRICKS,
        display_name="Gemma 3 12B",
        task=ModelTask.CHAT,
        endpoint_name="databricks-gemma-3-12b",
        description="Gemma 3 12B via Databricks Model Serving",
        enabled=True,
        supports_tools=False,
    ),
    "databricks-gte-large-en": ModelConfig(
        provider=ModelProvider.DATABRICKS,
        display_name="GTE Large EN",
        task=ModelTask.EMBEDDING,
        endpoint_name="databricks-gte-large-en",
        description="GTE Large EN Embedding via Databricks",
        enabled=True,
        supports_tools=False,
    ),
    "databricks-bge-large-en": ModelConfig(
        provider=ModelProvider.DATABRICKS,
        display_name="BGE Large EN",
        task=ModelTask.EMBEDDING,
        endpoint_name="databricks-bge-large-en",
        description="BGE Large EN Embedding via Databricks",
        enabled=True,
        supports_tools=False,
    ),
    "databricks-qwen3-embedding-0-6b": ModelConfig(
        provider=ModelProvider.DATABRICKS,
        display_name="Qwen3 Embedding 0.6B",
        task=ModelTask.EMBEDDING,
        endpoint_name="databricks-qwen3-embedding-0-6b",
        description="Qwen3 Embedding 0.6B via Databricks",
        enabled=True,
        supports_tools=False,
    ),
    "gpt-4o-mini": ModelConfig(
        provider=ModelProvider.OPENAI,
        display_name="GPT-4o Mini",
        task=ModelTask.CHAT,
        model_name="gpt-4o-mini",
        description="Modelo OpenAI (somente se selecionado explicitamente)",
        enabled=True,
        supports_tools=True,
    ),
    "gpt-4o": ModelConfig(
        provider=ModelProvider.OPENAI,
        display_name="GPT-4o",
        task=ModelTask.CHAT,
        model_name="gpt-4o",
        description="Modelo OpenAI (somente se selecionado explicitamente)",
        enabled=True,
        supports_tools=True,
    ),
}

DEFAULT_MODEL = "databricks-meta-llama-3-3-70b-instruct"
FALLBACK_MODEL = None


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
