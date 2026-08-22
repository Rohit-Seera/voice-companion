"""Provider manager."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from typing import Any

from app.core.settings import settings
from app.providers.anthropic import AnthropicProvider
from app.providers.base.exceptions import (
    ProviderConfigurationError,
    ProviderError,
)
from app.providers.base.provider import BaseProvider
from app.providers.base.types import (
    EmbeddingResult,
    ProviderChunk,
    ProviderResponse,
)
from app.providers.deepseek import DeepSeekProvider
from app.providers.gemini import GeminiProvider
from app.providers.groq import GroqProvider
from app.providers.openai import OpenAIProvider
from app.providers.openrouter import OpenRouterProvider
from app.providers.qwen import QwenProvider


class ProviderManager:
    """Manage AI providers and provider fallback."""

    def __init__(
        self,
        providers: dict[str, BaseProvider] | None = None,
    ) -> None:
        self._providers: dict[str, BaseProvider] = (
            providers or {}
        )

        if not self._providers:
            self._register_default_providers()

    def _register_default_providers(self) -> None:
        """Register configured providers."""

        provider_classes: dict[str, type[BaseProvider]] = {
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider,
            "gemini": GeminiProvider,
            "groq": GroqProvider,
            "deepseek": DeepSeekProvider,
            "qwen": QwenProvider,
            "openrouter": OpenRouterProvider,
        }

        for name, provider_class in provider_classes.items():
            try:
                provider = provider_class()
            except ProviderError:
                continue

            self._providers[name] = provider

    @property
    def providers(self) -> dict[str, BaseProvider]:
        """Return registered providers."""

        return self._providers.copy()

    def register(
        self,
        provider: BaseProvider,
    ) -> None:
        """Register or replace a provider."""

        self._providers[provider.name] = provider

    def unregister(
        self,
        name: str,
    ) -> BaseProvider | None:
        """Remove and return a registered provider."""

        return self._providers.pop(name, None)

    def get(
        self,
        name: str,
    ) -> BaseProvider:
        """Return a provider by name."""

        try:
            return self._providers[name]
        except KeyError as error:
            raise ProviderConfigurationError(
                f"Provider '{name}' is not registered.",
                provider=name,
            ) from error

    def _fallback_order(
        self,
        primary: str,
    ) -> list[str]:
        """Build the configured provider fallback order."""

        fallback = settings.ai.fallback_provider

        order = [primary]

        if fallback and fallback != primary:
            order.append(fallback)

        return [
            name
            for name in order
            if name in self._providers
        ]

    async def generate(
        self,
        messages: Sequence[dict[str, Any]],
        *,
        provider: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        fallback: bool = True,
        **kwargs: Any,
    ) -> ProviderResponse:
        """Generate a response using the selected provider."""

        primary = (
            provider
            or settings.ai.default_provider
        )

        # If the caller explicitly selected a provider,
        # it must exist. Do not silently switch to fallback.
        if (
            provider is not None
            and provider not in self._providers
        ):
            raise ProviderConfigurationError(
                f"Provider '{provider}' is not registered.",
                provider=provider,
            )

        providers = (
            self._fallback_order(primary)
            if fallback
            else [primary]
        )

        errors: list[ProviderError] = []

        for name in providers:
            current = self.get(name)

            try:
                return await current.generate(
                    messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )

            except ProviderError as error:
                errors.append(error)

                if not error.retryable:
                    raise

        raise ProviderError(
            "All configured providers failed.",
            provider=primary,
            retryable=False,
        ) from (
            errors[-1]
            if errors
            else None
        )

    async def stream(
        self,
        messages: Sequence[dict[str, Any]],
        *,
        provider: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[ProviderChunk]:
        """Stream a response from the selected provider."""

        primary = (
            provider
            or settings.ai.default_provider
        )

        current = self.get(primary)

        async for chunk in current.stream(
            messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        ):
            yield chunk

    async def embed(
        self,
        texts: Sequence[str],
        *,
        provider: str | None = None,
        model: str | None = None,
        **kwargs: Any,
    ) -> EmbeddingResult:
        """Generate embeddings using the configured provider."""

        primary = (
            provider
            or settings.ai.embedding_provider
        )

        current = self.get(primary)

        return await current.embed(
            texts,
            model=model,
            **kwargs,
        )

    async def health_check(
        self,
        provider: str | None = None,
    ) -> dict[str, bool]:
        """Check the health of registered providers."""

        if provider:
            current = self.get(provider)

            return {
                provider: await current.health_check(),
            }

        results: dict[str, bool] = {}

        for name, current in self._providers.items():
            try:
                results[name] = await current.health_check()
            except Exception:
                results[name] = False

        return results

    async def close(self) -> None:
        """Close all registered providers."""

        for provider in self._providers.values():
            try:
                await provider.close()
            except Exception:
                continue