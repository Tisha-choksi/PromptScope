import asyncio
import logging
from typing import Optional

from app.services.llm.base import BaseLLMProvider, LLMResponse
from app.services.llm.openai_provider import OpenAIProvider
from app.services.llm.anthropic_provider import AnthropicProvider
from app.services.llm.gemini_provider import GeminiProvider
from app.services.llm.perplexity_provider import PerplexityProvider

logger = logging.getLogger(__name__)


class LLMOrchestrator:
    def __init__(self):
        self.providers: dict[str, BaseLLMProvider] = {}
        self._register_providers()

    def _register_providers(self) -> None:
        for provider in (
            OpenAIProvider(),
            AnthropicProvider(),
            GeminiProvider(),
            PerplexityProvider(),
        ):
            self.providers[provider.provider_name] = provider

    def get_available_providers(self) -> list[str]:
        return [
            name
            for name, provider in self.providers.items()
            if provider.is_available()
        ]

    async def query_provider(self, provider_name: str, prompt: str) -> LLMResponse:
        provider = self.providers.get(provider_name)
        if provider is None:
            return LLMResponse(
                provider=provider_name,
                model="unknown",
                prompt_text=prompt,
                response_text="",
                tokens_used=None,
                latency_ms=0,
                error=f"Provider '{provider_name}' is not registered",
                success=False,
            )
        if not provider.is_available():
            return LLMResponse(
                provider=provider_name,
                model=provider.default_model,
                prompt_text=prompt,
                response_text="",
                tokens_used=None,
                latency_ms=0,
                error=f"Provider '{provider_name}' is not available (missing API key or dependency)",
                success=False,
            )
        try:
            return await provider.generate(prompt)
        except Exception as e:
            logger.exception("Unexpected error querying provider %s", provider_name)
            return LLMResponse(
                provider=provider_name,
                model=provider.default_model,
                prompt_text=prompt,
                response_text="",
                tokens_used=None,
                latency_ms=0,
                error=str(e),
                success=False,
            )

    async def query_all(
        self,
        prompt: str,
        providers: Optional[list[str]] = None,
    ) -> list[LLMResponse]:
        target_providers = providers if providers is not None else self.get_available_providers()
        if not target_providers:
            logger.warning("No providers available to query")
            return []

        tasks = [self.query_provider(name, prompt) for name in target_providers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        responses: list[LLMResponse] = []
        for provider_name, result in zip(target_providers, results):
            if isinstance(result, BaseException):
                logger.error(
                    "gather exception for provider %s: %s", provider_name, result
                )
                responses.append(
                    LLMResponse(
                        provider=provider_name,
                        model="unknown",
                        prompt_text=prompt,
                        response_text="",
                        tokens_used=None,
                        latency_ms=0,
                        error=str(result),
                        success=False,
                    )
                )
            else:
                responses.append(result)  # type: ignore[arg-type]
        return responses

    async def query_with_retry(
        self,
        provider_name: str,
        prompt: str,
        max_retries: int = 3,
    ) -> LLMResponse:
        last_response: Optional[LLMResponse] = None
        delay = 1.0
        for attempt in range(1, max_retries + 1):
            response = await self.query_provider(provider_name, prompt)
            if response.success:
                return response
            last_response = response
            if attempt < max_retries:
                logger.warning(
                    "Provider %s failed (attempt %d/%d): %s — retrying in %.1fs",
                    provider_name,
                    attempt,
                    max_retries,
                    response.error,
                    delay,
                )
                await asyncio.sleep(delay)
                delay = min(delay * 2, 10.0)
            else:
                logger.error(
                    "Provider %s failed after %d attempts: %s",
                    provider_name,
                    max_retries,
                    response.error,
                )
        # last_response is always set because max_retries >= 1
        assert last_response is not None
        return last_response
