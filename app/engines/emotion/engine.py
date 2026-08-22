"""Emotion engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.runtime.state import RuntimeState


@dataclass(slots=True, frozen=True)
class EmotionResult:
    """Represent a detected emotional state."""

    emotion: str
    confidence: float = 0.0
    metadata: dict[str, Any] = field(
        default_factory=dict,
    )


class EmotionEngine:
    """Detect and normalize the user's current emotion."""

    def __init__(
        self,
        detector: Any | None = None,
    ) -> None:
        self._detector = detector

    @property
    def detector(self) -> Any | None:
        """Return the configured emotion detector."""

        return self._detector

    async def detect_emotion(
        self,
        state: RuntimeState,
    ) -> dict[str, Any]:
        """Detect the user's current emotional state."""

        if self._detector is None:
            return {
                "emotion": "neutral",
                "confidence": 0.0,
            }

        result = await self._detector.detect_emotion(
            state,
        )

        if not isinstance(result, dict):
            raise TypeError(
                "Emotion detector must return a dictionary."
            )

        return result

    @staticmethod
    def normalize(
        result: EmotionResult,
    ) -> dict[str, Any]:
        """Convert an EmotionResult into runtime context."""

        return {
            "emotion": result.emotion,
            "confidence": result.confidence,
            **result.metadata,
        }