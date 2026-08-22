"""Load personality configuration for the runtime execution."""

from __future__ import annotations

from typing import Any, Protocol

from app.runtime.context import RuntimeContext
from app.runtime.state import RuntimeState


class PersonalityProviderProtocol(Protocol):
    """Contract for providing personality configuration."""

    async def get_personality(
        self,
        state: RuntimeState,
    ) -> dict[str, Any]:
        """Return personality configuration for the current state."""
        ...


class PersonalityNode:
    """Load personality configuration into runtime context."""

    def __init__(
        self,
        provider: PersonalityProviderProtocol | None = None,
    ) -> None:
        self._provider = provider

    async def execute(
        self,
        state: RuntimeState,
        context: RuntimeContext,
    ) -> RuntimeState:
        """Load personality configuration."""

        provider = self._provider

        if provider is None:
            if not context.has_service("personality_provider"):
                raise RuntimeError(
                    "Personality provider has not been configured."
                )

            provider = context.get_service(
                "personality_provider",
            )

        personality = await provider.get_personality(
            state,
        )

        context.metadata["personality"] = personality

        return state