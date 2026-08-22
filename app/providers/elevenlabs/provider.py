"""ElevenLabs text-to-speech provider."""

from __future__ import annotations

from collections.abc import AsyncIterator

from elevenlabs import AsyncElevenLabs

from app.core.settings import settings
from app.services.speech.contracts import AudioResult


class ElevenLabsTTS:
    """ElevenLabs implementation of the voice companion TTS contract."""

    name = "elevenlabs"

    def __init__(self) -> None:
        config = settings.elevenlabs

        if not config.api_key:
            raise RuntimeError(
                "ElevenLabs API key is not configured."
            )

        if not config.voice_id:
            raise RuntimeError(
                "ElevenLabs voice ID is not configured."
            )

        self._voice_id = config.voice_id
        self._model = config.model

        self._client = AsyncElevenLabs(
            api_key=config.api_key,
        )

    async def synthesize(
        self,
        text: str,
        *,
        voice: str | None = None,
        language: str | None = None,
    ) -> AudioResult:
        """Generate complete MP3 audio."""

        del language

        voice_id = voice or self._voice_id

        try:
            audio_stream = self._client.text_to_speech.convert(
                voice_id=voice_id,
                text=text,
                model_id=self._model,
                output_format="mp3_44100_128",
            )

            chunks: list[bytes] = []

            async for chunk in audio_stream:
                if isinstance(chunk, bytes):
                    chunks.append(chunk)

            return AudioResult(
                data=b"".join(chunks),
                content_type="audio/mpeg",
            )

        except Exception as error:
            raise RuntimeError(
                "ElevenLabs synthesis failed."
            ) from error

    async def stream(
        self,
        text: str,
        *,
        voice: str | None = None,
        language: str | None = None,
    ) -> AsyncIterator[bytes]:
        """Stream MP3 audio chunks from ElevenLabs."""

        del language

        voice_id = voice or self._voice_id

        try:
            audio_stream = self._client.text_to_speech.convert(
                voice_id=voice_id,
                text=text,
                model_id=self._model,
                output_format="mp3_44100_128",
            )

            async for chunk in audio_stream:
                if isinstance(chunk, bytes):
                    yield chunk

        except Exception as error:
            raise RuntimeError(
                "ElevenLabs streaming failed."
            ) from error

    async def close(self) -> None:
        """Close the ElevenLabs client."""

        close_method = getattr(self._client, "close", None)

        if close_method is not None:
            result = close_method()

            if hasattr(result, "__await__"):
                await result
