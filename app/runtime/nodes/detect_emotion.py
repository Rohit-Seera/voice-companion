"""Detect the user's current emotional state."""

from __future__ import annotations

from typing import Any, Protocol

from app.runtime.context import RuntimeContext
from app.runtime.state import RuntimeState


class EmotionProviderProtocol(Protocol):
    """Contract for detecting user emotion."""

    async def detect_emotion(
        self,
        state: RuntimeState,
    ) -> dict[str, Any]:
        """Detect emotion from the current runtime state."""
        ...


class DetectEmotionNode:
    """Detect and attach the current user emotion."""

    def __init__(
        self,
        provider: EmotionProviderProtocol | None = None,
    ) -> None:
        self._provider = provider

    async def execute(
        self,
        state: RuntimeState,
        context: RuntimeContext,
    ) -> RuntimeState:
        """Detect the current user emotion."""

        provider = self._provider

        if provider is None:
            if not context.has_service("emotion_provider"):
                raise RuntimeError(
                    "Emotion provider has not been configured."
                )

            provider = context.get_service(
                "emotion_provider",
            )

        emotion = await provider.detect_emotion(
            state,
        )

        context.metadata["emotion"] = emotion

        return state