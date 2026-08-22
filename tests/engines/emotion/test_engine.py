"""Tests for the emotion engine."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.enums import Workflow
from app.engines.emotion.engine import (
    EmotionEngine,
    EmotionResult,
)
from app.runtime.state import RuntimeState


@pytest.fixture
def state() -> RuntimeState:
    """Return a sample runtime state."""

    return RuntimeState(
        request_id=uuid4(),
        workflow=Workflow.CHAT,
        input="I am having a great day!",
    )


@pytest.mark.asyncio
async def test_default_emotion_is_neutral(
    state: RuntimeState,
) -> None:
    """Engine should provide a neutral fallback."""

    engine = EmotionEngine()

    result = await engine.detect_emotion(
        state,
    )

    assert result == {
        "emotion": "neutral",
        "confidence": 0.0,
    }


@pytest.mark.asyncio
async def test_uses_configured_detector(
    state: RuntimeState,
) -> None:
    """Engine should delegate detection to its detector."""

    detector = MagicMock()

    detector.detect_emotion = AsyncMock(
        return_value={
            "emotion": "happy",
            "confidence": 0.92,
        },
    )

    engine = EmotionEngine(detector)

    result = await engine.detect_emotion(
        state,
    )

    assert result == {
        "emotion": "happy",
        "confidence": 0.92,
    }

    detector.detect_emotion.assert_awaited_once_with(
        state,
    )


@pytest.mark.asyncio
async def test_detector_metadata_is_preserved(
    state: RuntimeState,
) -> None:
    """Detector output should be preserved."""

    detector = MagicMock()

    detector.detect_emotion = AsyncMock(
        return_value={
            "emotion": "sad",
            "confidence": 0.81,
            "intensity": 0.7,
            "source": "text",
        },
    )

    engine = EmotionEngine(detector)

    result = await engine.detect_emotion(
        state,
    )

    assert result["emotion"] == "sad"
    assert result["confidence"] == 0.81
    assert result["intensity"] == 0.7
    assert result["source"] == "text"


@pytest.mark.asyncio
async def test_invalid_detector_result_raises(
    state: RuntimeState,
) -> None:
    """Engine should reject invalid detector results."""

    detector = MagicMock()

    detector.detect_emotion = AsyncMock(
        return_value="happy",
    )

    engine = EmotionEngine(detector)

    with pytest.raises(
        TypeError,
        match="must return a dictionary",
    ):
        await engine.detect_emotion(
            state,
        )


def test_emotion_result_normalization() -> None:
    """EmotionResult should convert into runtime context data."""

    result = EmotionResult(
        emotion="happy",
        confidence=0.95,
        metadata={
            "intensity": 0.8,
            "source": "voice",
        },
    )

    normalized = EmotionEngine.normalize(
        result,
    )

    assert normalized == {
        "emotion": "happy",
        "confidence": 0.95,
        "intensity": 0.8,
        "source": "voice",
    }


def test_emotion_result_defaults() -> None:
    """EmotionResult should provide sensible defaults."""

    result = EmotionResult(
        emotion="neutral",
    )

    assert result.emotion == "neutral"
    assert result.confidence == 0.0
    assert result.metadata == {}


def test_emotion_result_is_immutable() -> None:
    """EmotionResult should be immutable."""

    result = EmotionResult(
        emotion="happy",
    )

    try:
        result.emotion = "sad"
    except AttributeError:
        pass
    else:
        raise AssertionError(
            "EmotionResult should be immutable."
        )