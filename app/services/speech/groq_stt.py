"""Groq Whisper speech-to-text adapter."""

from __future__ import annotations

import io

from groq import AsyncGroq

from app.core.settings import settings
from app.services.speech.contracts import TranscriptionResult


class GroqWhisperSTT:
    """Speech-to-text provider backed by Groq Whisper Large V3 Turbo."""

    def __init__(self) -> None:
        api_key = settings.ai.groq.api_key

        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not configured.")

        self._client = AsyncGroq(api_key=api_key)
        self._model = "whisper-large-v3-turbo"

    async def transcribe(
        self,
        audio: bytes,
        *,
        content_type: str,
        language: str | None = None,
    ) -> TranscriptionResult:
        """Transcribe in-memory audio using Groq Whisper Large V3 Turbo."""

        extension_map = {
            "audio/wav": "wav",
            "audio/x-wav": "wav",
            "audio/mpeg": "mp3",
            "audio/ogg": "ogg",
            "audio/webm": "webm",
        }

        extension = extension_map.get(
            content_type,
            "wav",
        )

        filename = f"audio.{extension}"

        request_kwargs: dict[str, object] = {
            "file": (
                filename,
                io.BytesIO(audio),
                content_type,
            ),
            "model": self._model,
            "response_format": "verbose_json",
        }

        if language:
            request_kwargs["language"] = language

        response = await self._client.audio.transcriptions.create(
            **request_kwargs,
        )

        text = getattr(response, "text", "").strip()

        response_language = getattr(
            response,
            "language",
            None,
        )

        duration = getattr(
            response,
            "duration",
            None,
        )

        return TranscriptionResult(
            text=text,
            language=(
                str(response_language)
                if response_language
                else language
            ),
            duration_seconds=(
                float(duration)
                if duration is not None
                else None
            ),
        )

    async def close(self) -> None:
        """Close the underlying Groq client."""

        await self._client.close()