"""
Wrapper para modelos Databricks usando databricks-sdk.
Implementa interface compatível com LangChain BaseChatModel.
"""

import logging
from collections.abc import Iterator
from typing import Any

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult

logger = logging.getLogger(__name__)


class ChatDatabricks(BaseChatModel):
    """
    Chat model wrapper para Databricks Foundation Model APIs.
    Usa databricks-sdk para comunicação com endpoints de Model Serving.
    """

    host: str
    token: str
    endpoint: str
    temperature: float = 0.0
    max_tokens: int = 4096
    _client: Any = None

    class Config:
        arbitrary_types_allowed = True

    def __init__(
        self,
        host: str,
        token: str,
        endpoint: str,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        **kwargs: Any,
    ):
        super().__init__(
            host=host,
            token=token,
            endpoint=endpoint,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Inicializa o cliente Databricks SDK."""
        try:
            from databricks.sdk import WorkspaceClient

            self._client = WorkspaceClient(
                host=self.host,
                token=self.token,
            )
            logger.info(f"Databricks client initialized for endpoint: {self.endpoint}")
        except ImportError:
            logger.warning(
                "databricks-sdk not installed. Install with: pip install databricks-sdk"
            )
            self._client = None
        except Exception as e:
            logger.error(f"Failed to initialize Databricks client: {e}")
            self._client = None

    @property
    def _llm_type(self) -> str:
        """Retorna o tipo do LLM."""
        return "databricks"

    @property
    def _identifying_params(self) -> dict[str, Any]:
        """Retorna parâmetros identificadores do modelo."""
        return {
            "endpoint": self.endpoint,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

    def _convert_messages_to_databricks_format(
        self, messages: list[BaseMessage]
    ) -> list[dict[str, str]]:
        """
        Converte mensagens LangChain para formato Databricks.

        Args:
            messages: Lista de mensagens LangChain

        Returns:
            Lista de dicionários no formato Databricks
        """
        converted = []
        for message in messages:
            if isinstance(message, SystemMessage):
                converted.append({"role": "system", "content": message.content})
            elif isinstance(message, HumanMessage):
                converted.append({"role": "user", "content": message.content})
            elif isinstance(message, AIMessage):
                converted.append({"role": "assistant", "content": message.content})
            else:
                converted.append({"role": "user", "content": str(message.content)})
        return converted

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        Gera resposta usando o endpoint Databricks.

        Args:
            messages: Lista de mensagens de entrada
            stop: Sequências de parada opcionais
            run_manager: Callback manager opcional
            **kwargs: Argumentos adicionais

        Returns:
            ChatResult com a resposta gerada
        """
        if self._client is None:
            return self._generate_fallback(messages)

        databricks_messages = self._convert_messages_to_databricks_format(messages)

        try:
            response = self._call_databricks_endpoint(
                databricks_messages,
                stop=stop,
                **kwargs,
            )

            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")

            message = AIMessage(content=content)
            generation = ChatGeneration(message=message)

            return ChatResult(generations=[generation])

        except Exception as e:
            logger.error(f"Error calling Databricks endpoint: {e}")
            return self._generate_fallback(messages, error=str(e))

    def _call_databricks_endpoint(
        self,
        messages: list[dict[str, str]],
        stop: list[str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Faz chamada ao endpoint de Model Serving do Databricks.

        Args:
            messages: Mensagens no formato Databricks
            stop: Sequências de parada
            **kwargs: Argumentos adicionais

        Returns:
            Resposta do endpoint
        """
        import requests

        url = f"{self.host.rstrip('/')}/serving-endpoints/{self.endpoint}/invocations"

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

        payload = {
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        if stop:
            payload["stop"] = stop

        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()

        return response.json()

    def _generate_fallback(
        self,
        messages: list[BaseMessage],
        error: str | None = None,
    ) -> ChatResult:
        """
        Gera resposta de fallback quando o cliente não está disponível.

        Args:
            messages: Mensagens de entrada
            error: Mensagem de erro opcional

        Returns:
            ChatResult com mensagem de fallback
        """
        if error:
            content = (
                f"Erro ao conectar com Databricks: {error}. "
                "Verifique as configurações DATABRICKS_HOST e DATABRICKS_TOKEN."
            )
        else:
            content = (
                "Cliente Databricks não inicializado. "
                "Instale databricks-sdk e configure as variáveis de ambiente."
            )

        message = AIMessage(content=content)
        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])

    def _stream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> Iterator[ChatGeneration]:
        """
        Streaming não suportado diretamente - usa geração normal.
        """
        result = self._generate(messages, stop, run_manager, **kwargs)
        yield from result.generations

    def invoke(
        self,
        input: list[BaseMessage] | str,
        config: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> AIMessage:
        """
        Invoca o modelo com as mensagens de entrada.

        Args:
            input: Mensagens de entrada ou string
            config: Configuração opcional
            **kwargs: Argumentos adicionais

        Returns:
            AIMessage com a resposta
        """
        if isinstance(input, str):
            messages = [HumanMessage(content=input)]
        else:
            messages = input

        result = self._generate(messages, **kwargs)

        if result.generations:
            return result.generations[0].message

        return AIMessage(content="Não foi possível gerar resposta.")
