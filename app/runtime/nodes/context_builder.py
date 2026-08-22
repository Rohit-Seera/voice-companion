"""Build the context used by downstream runtime nodes."""

from __future__ import annotations

from typing import Any

from app.runtime.context import RuntimeContext
from app.runtime.state import RuntimeState


class ContextBuilderNode:
    """Build a structured context from the current runtime state."""

    def execute_context(
        self,
        state: RuntimeState,
        context: RuntimeContext,
    ) -> dict[str, Any]:
        """Build and return the runtime context."""

        return {
            "input": state.input,
            "session_id": state.session_id,
            "workflow": state.workflow,
            "memories": list(state.memories),
            "metadata": dict(state.metadata),
        }

    async def execute(
        self,
        state: RuntimeState,
        context: RuntimeContext,
    ) -> RuntimeState:
        """Build context and attach it to runtime context."""

        built_context = self.execute_context(
            state,
            context,
        )

        context.metadata["built_context"] = built_context

        return state