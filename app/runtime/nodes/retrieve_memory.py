"""Retrieve relevant memories for the current runtime execution."""

from __future__ import annotations

from app.engines.memory.engine import MemoryEngine
from app.engines.memory.schemas import MemorySearchRequest
from app.runtime.context import RuntimeContext
from app.runtime.state import RuntimeState


class RetrieveMemoryNode:
    """Retrieve relevant memories and attach them to runtime state."""

    def __init__(
        self,
        memory_engine: MemoryEngine | None = None,
    ) -> None:
        self._memory_engine = memory_engine

    async def execute(
        self,
        state: RuntimeState,
        context: RuntimeContext,
    ) -> RuntimeState:
        """Retrieve memories relevant to the current input."""

        memory_engine = self._memory_engine

        if memory_engine is None:
            if not context.has_service("memory_engine"):
                raise RuntimeError(
                    "Memory engine has not been configured."
                )

            memory_engine = context.get_service(
                "memory_engine",
            )

        request = MemorySearchRequest(
            query=state.input,
        )

        memories = await memory_engine.search(
            request,
        )

        state.memories = memories

        return state