"""Build the prompt used by downstream LLM nodes."""

from __future__ import annotations

from typing import Any

from app.runtime.context import RuntimeContext
from app.runtime.state import RuntimeState


class PromptBuilderNode:
    """Build a structured prompt from runtime context."""

    def build_prompt(
        self,
        state: RuntimeState,
        context: RuntimeContext,
    ) -> str:
        """Build a prompt from the current runtime information."""

        sections: list[str] = []

        character = context.metadata.get("character")

        if isinstance(character, dict):
            name = character.get("name")
            description = character.get("description")

            if name:
                sections.append(f"Character: {name}")

            if description:
                sections.append(
                    f"Character identity: {description}"
                )

        sections.append(
            f"User: {state.input}"
        )

        personality = context.metadata.get(
            "personality",
        )

        if personality:
            sections.append(
                f"Personality: {personality}"
            )

        relationship = context.metadata.get(
            "relationship",
        )

        if relationship:
            sections.append(
                f"Relationship: {relationship}"
            )

        emotion = context.metadata.get(
            "emotion",
        )

        if emotion:
            sections.append(
                f"Emotion: {emotion}"
            )

        if state.memories:
            sections.append(
                f"Memories: {state.memories}"
            )

        return "\n\n".join(sections)

    async def execute(
        self,
        state: RuntimeState,
        context: RuntimeContext,
    ) -> RuntimeState:
        """Build and store the prompt."""

        prompt = self.build_prompt(
            state,
            context,
        )

        context.metadata["prompt"] = prompt

        return state