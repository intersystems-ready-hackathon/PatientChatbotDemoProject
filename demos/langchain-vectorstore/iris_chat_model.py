"""
IRISChatModel — LangChain BaseChatModel backed by InterSystems AI Hub ConfigStore.

This is a demo-quality implementation of the pattern described in:
  https://usconfluence.iscinternal.com/pages/viewpage.action?pageId=1102084080
  ("User Story: Building a simple chatbot with LangChain/4J")

The production version is tracked as DP-445282 (Aohan Dang / Aleks Djakovic).

Usage (ConfigStore mode — named config resolved from IRIS AIGateway tables):
    import iris
    from iris_chat_model import IRISChatModel
    from langchain.chat_models import init_chat_model

    conn = iris.connect("localhost:1972/USER", "_SYSTEM", "SYS")
    model = IRISChatModel.from_config("openai-demo", connection=conn)
    result = model.invoke([HumanMessage(content="Hello!")])

Usage (direct mode — pass provider directly, no ConfigStore needed):
    import iris_llm
    from iris_chat_model import IRISChatModel

    provider = iris_llm.Provider.new_openai(api_key="sk-...")
    model = IRISChatModel(provider=provider, model_name="gpt-4o-mini")
    result = model.invoke([HumanMessage(content="Hello!")])
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Iterator, List, Optional, Sequence

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult

logger = logging.getLogger("iris_chat_model")


def _to_iris_messages(messages: Sequence[BaseMessage]) -> list[dict[str, str]]:
    """Convert LangChain messages to iris_llm dict format."""
    result = []
    for m in messages:
        if isinstance(m, SystemMessage):
            role = "system"
        elif isinstance(m, AIMessage):
            role = "assistant"
        else:
            role = "user"
        result.append({"role": role, "content": str(m.content)})
    return result


class IRISChatModel(BaseChatModel):
    """
    LangChain BaseChatModel backed by an iris_llm.Provider.

    Supports two initialization modes:
    - Direct: pass provider + model_name explicitly
    - ConfigStore: use from_config() classmethod to resolve from IRIS AIGateway
    """

    provider: Any
    model_name: str = "gpt-4o-mini"
    provider_name: str = ""

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_config(
        cls,
        provider_name: str,
        connection,
        iris_native=None,
    ) -> "IRISChatModel":
        """
        Resolve a named LLM configuration from the IRIS AI Hub ConfigStore.

        Args:
            provider_name: Logical provider name registered in AIGateway_Storage.LLMProvider
            connection: IRIS DB-API connection
            iris_native: IRIS Native API object (for Wallet credential resolution).
                         If None, falls back to env var OPENAI_API_KEY for demo purposes.
        """
        import iris
        import iris_llm

        # Try full ProviderFactory path (requires AIGateway tables + Wallet)
        if iris_native is not None:
            try:
                import sys

                sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../ai-hub/python"))
                from iris_agent.config.provider import ProviderFactory

                factory = ProviderFactory(connection, iris_native)
                provider = factory.from_config(provider_name)
                # Resolve model from config
                cursor = connection.cursor()
                cursor.execute(
                    "SELECT DefaultModel FROM AIGateway_Storage.LLMProvider WHERE Name = ?",
                    [provider_name],
                )
                row = cursor.fetchone()
                model_name = row[0] if row and row[0] else "gpt-4o-mini"
                return cls(provider=provider, model_name=model_name, provider_name=provider_name)
            except Exception as e:
                logger.warning("ProviderFactory failed (%s), falling back to env var", e)

        # Demo fallback: resolve from IRIS SQL + env var API key
        cursor = connection.cursor()
        cursor.execute(
            """SELECT ProviderType, DefaultModel, ApiBaseUrl
               FROM AIGateway_Storage.LLMProvider WHERE Name = ?""",
            [provider_name],
        )
        row = cursor.fetchone()
        if row is None:
            raise KeyError(
                f"Provider {provider_name!r} not found in AIGateway_Storage.LLMProvider.\n"
                f"Run seed_configstore.py first to register it."
            )
        provider_type, model_name, api_base_url = row
        model_name = model_name or "gpt-4o-mini"

        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY not set and no Wallet available")

        provider = iris_llm.Provider.new_openai(api_key=api_key)
        logger.info("Resolved provider %r from ConfigStore (demo mode)", provider_name)
        return cls(provider=provider, model_name=model_name, provider_name=provider_name)

    @property
    def _llm_type(self) -> str:
        return "iris-chat-model"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        iris_messages = _to_iris_messages(messages)
        raw = self.provider.chat_complete(self.model_name, iris_messages)
        data = json.loads(raw)
        content = data.get("content", "")
        usage = data.get("usage", {})
        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content=content))],
            llm_output={"usage": usage, "model": data.get("model", self.model_name)},
        )

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        iris_messages = _to_iris_messages(messages)
        for chunk_str in self.provider.stream_chat_complete(self.model_name, iris_messages):
            try:
                data = json.loads(chunk_str)
                content = data.get("content", "")
            except (json.JSONDecodeError, TypeError):
                content = str(chunk_str)
            if content:
                chunk = ChatGenerationChunk(message=AIMessageChunk(content=content))
                if run_manager:
                    run_manager.on_llm_new_token(content)
                yield chunk
