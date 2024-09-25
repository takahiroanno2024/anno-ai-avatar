import os
import random
from typing import Any, AsyncGenerator, Dict, List, Optional, TypeVar, Union

import sentry_sdk
from loguru import logger
from openai import DEFAULT_MAX_RETRIES as OPENAI_DEFAULT_MAX_RETRIES
from openai import AsyncAzureOpenAI, AsyncOpenAI, NotFoundError, RateLimitError
import os, asyncio
from together import AsyncTogether

from vocode import sentry_span_tags
from vocode.streaming.action.abstract_factory import AbstractActionFactory
from vocode.streaming.action.default_factory import DefaultActionFactory
from vocode.streaming.agent.base_agent import GeneratedResponse, RespondAgent, StreamedResponse
from vocode.streaming.agent.abstract_factory import AbstractAgentFactory
from vocode.streaming.agent.openai_utils import (
    format_openai_chat_messages_from_transcript,
    merge_event_logs,
    get_openai_chat_messages_from_transcript,
    openai_get_tokens,
    vector_db_result_to_openai_chat_message,
)
from vocode.streaming.agent.streaming_utils import collate_response_async, stream_response_async
from vocode.streaming.models.actions import FunctionCallActionTrigger
from vocode.streaming.models.agent import ChatGPTAgentConfig, AzureOpenAIConfig, VectorDBConfig, LLMFallback
from vocode.streaming.agent.base_agent import BaseAgent, RespondAgent
from vocode.streaming.agent.chat_gpt_agent import ChatGPTAgent
from vocode.streaming.models.events import Sender
from vocode.streaming.models.message import BaseMessage, BotBackchannel, LLMToken
from vocode.streaming.models.transcript import Message
from vocode.streaming.vector_db.factory import VectorDBFactory
from vocode.utils.sentry_utils import CustomSentrySpans, sentry_create_span

import aiohttp

class CustomChatGPTAgentConfig(ChatGPTAgentConfig, type=""):  # type: ignore
    filler_words=["なるほど！", "はい！", "わかりました！"],
    rag_url: str

CustomChatGPTAgentConfigType = TypeVar("CustomChatGPTAgentConfigType", bound=CustomChatGPTAgentConfig)

def instantiate_openai_client(agent_config: CustomChatGPTAgentConfig, model_fallback: bool = False):
    if False:
        return AsyncAzureOpenAI(
            azure_endpoint=agent_config.azure_params.base_url,
            api_key=agent_config.azure_params.api_key,
            api_version=agent_config.azure_params.api_version,
            max_retries=0 if model_fallback else OPENAI_DEFAULT_MAX_RETRIES,
        )
    else:
        if agent_config.openai_api_key is not None:
            logger.info("Using OpenAI API key override")
        return AsyncTogether(
            api_key=agent_config.openai_api_key or os.environ["TOGETHER_API_KEY"],
        )

async def fetch_related_info(self, query: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{self.agent_config.rag_url}/get_info?query={query}&top_k=2", ssl=False) as response:
            response.raise_for_status()  # This line checks for errors in the response.
            data = await response.json()
            print("RAG data", data)
            return str(data)


class CustomChatGPTAgent(ChatGPTAgent[CustomChatGPTAgentConfigType]):
    def __init__(
        self,
        agent_config: CustomChatGPTAgentConfigType,
        **kwargs,
    ):
        super().__init__(
            agent_config=agent_config,
            **kwargs,
        )
        self.openai_client = instantiate_openai_client(
            agent_config, model_fallback=agent_config.llm_fallback is not None
        )

    async def generate_response(
        self,
        human_input: str,
        conversation_id: str,
        is_interrupt: bool = False,
        bot_was_in_medias_res: bool = False,
    ) -> AsyncGenerator[GeneratedResponse, None]:
        assert self.transcript is not None

        using_input_streaming_synthesizer = (
            self.conversation_state_manager.using_input_streaming_synthesizer()
        )
        ResponseClass = (
                StreamedResponse if using_input_streaming_synthesizer else GeneratedResponse
        )
        MessageType = LLMToken if using_input_streaming_synthesizer else BaseMessage

        yield ResponseClass(
            message=MessageType(text=random.choice(self.agent_config.filler_words)),
            is_interruptible=True,
        )

        related_info = await fetch_related_info(self, human_input)
        merged_event_logs = merge_event_logs(event_logs=self.transcript.event_logs)
        messages = get_openai_chat_messages_from_transcript(
                        merged_event_logs=merged_event_logs,
                        prompt_preamble=self.agent_config.prompt_preamble + "\n\n# 参考情報:" + related_info,
                        )
        chat_parameters = self.get_chat_parameters(messages)
        # togetherではmax_tokensは必須
        chat_parameters["max_tokens"] = 1024
        chat_parameters["temperature"] = 0
        chat_parameters["stream"] = True
        chat_parameters["model"] = self.agent_config.model_name

        #openai_chat_messages: List = chat_parameters.get("messages", [])
        openai_chat_messages: List = chat_parameters.get("messages", [])
        print(openai_chat_messages)

        backchannelled = "false"
        backchannel: Optional[BotBackchannel] = None
        if (
            self.agent_config.use_backchannels
            and not bot_was_in_medias_res
            and self.should_backchannel(human_input)
        ):
            backchannel = self.choose_backchannel()
        elif self.agent_config.first_response_filler_message and self.is_first_response():
            backchannel = BotBackchannel(text=self.agent_config.first_response_filler_message)

        if backchannel is not None:
            # The LLM needs the backchannel context manually - otherwise we're in a race condition
            # between sending the response and generating ChatGPT's response
            openai_chat_messages.append({"role": "assistant", "content": backchannel.text})
            yield GeneratedResponse(
                message=backchannel,
                is_interruptible=True,
            )
            backchannelled = "true"

        span_tags = sentry_span_tags.value
        if span_tags:
            span_tags["prior_backchannel"] = backchannelled
            sentry_span_tags.set(span_tags)

        first_sentence_total_span = sentry_create_span(
            sentry_callable=sentry_sdk.start_span, op=CustomSentrySpans.LLM_FIRST_SENTENCE_TOTAL
        )

        ttft_span = sentry_create_span(
            sentry_callable=sentry_sdk.start_span, op=CustomSentrySpans.TIME_TO_FIRST_TOKEN
        )

        stream = await self._create_openai_stream(chat_parameters)

        response_generator = collate_response_async
        if using_input_streaming_synthesizer:
            response_generator = stream_response_async
        async for message in response_generator(
            conversation_id=conversation_id,
            gen=openai_get_tokens(
                stream,
            ),
            get_functions=True,
            sentry_span=ttft_span,
        ):
            if first_sentence_total_span:
                first_sentence_total_span.finish()

            if isinstance(message, str):
                yield ResponseClass(
                    message=MessageType(text=message),
                    is_interruptible=True,
                )
            else:
                yield ResponseClass(
                    message=message,
                    is_interruptible=True,
                )

class CustomChatGPTAgentFactory(AbstractAgentFactory):
    """Factory class for creating agents based on the provided agent configuration."""

    def create_agent(self, agent_config: CustomChatGPTAgentConfig) -> BaseAgent:
        """Creates an agent based on the provided agent configuration.

        Args:
            agent_config (AgentConfig): The configuration for the agent to be created.

        Returns:
            BaseAgent: The created agent.

        Raises:
            Exception: If the agent configuration type is not recognized.
        """
        return CustomChatGPTAgent(agent_config=agent_config)
