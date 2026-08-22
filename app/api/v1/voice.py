"""Authenticated HTTP API for the provider-neutral voice companion."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from app.core.settings import settings
from app.services.speech.exceptions import (
    VoiceProcessingError,
    VoiceProviderUnavailableError,
    VoiceSessionAccessError,
    VoiceSessionNotFoundError,
    VoiceTurnCancelledError,
    VoiceTurnInProgressError,
)
from app.services.speech.service import VoiceCompanionService


router = APIRouter(prefix="/voice", tags=["voice"])

_bearer_scheme = HTTPBearer(auto_error=False)
_NO_STORE_HEADERS = {"Cache-Control": "no-store"}


class VoiceSessionResponse(BaseModel):
    """A caller-owned companion session."""

    session_id: UUID
    status: str = "idle"


class VoiceTurnRequest(BaseModel):
    """A transcript ready to be handled by the companion runtime."""

    transcript: str = Field(min_length=1, max_length=8_000)
    language: str | None = Field(default=None, max_length=16)


class ExpressionResponse(BaseModel):
    """Constrained frontend animation instructions for a response."""

    emotion: str
    expression: str
    gesture: str
    gaze: str
    lip_sync: str


class TokenUsageResponse(BaseModel):
    """Provider token usage available after a completed runtime turn."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class VoiceTurnResponse(BaseModel):
    """Companion text and animation instructions for a client."""

    session_id: UUID
    request_id: UUID
    text: str
    expression: ExpressionResponse
    token_usage: TokenUsageResponse


class TranscriptionResponse(BaseModel):
    """A normalized STT response."""

    transcript: str
    language: str | None = None
    duration_seconds: float | None = None


class SynthesisRequest(BaseModel):
    """Parameters sent to a configured text-to-speech provider."""

    text: str = Field(min_length=1, max_length=8_000)
    voice: str | None = Field(default=None, max_length=128)
    language: str | None = Field(default=None, max_length=16)


class CancelTurnResponse(BaseModel):
    """Result of a client barge-in cancellation request."""

    cancelled: bool


async def require_voice_claims(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        _bearer_scheme,
    ),
) -> dict[str, object]:
    """Enforce the existing JWT and VOICE permission without eager secrets."""

    try:
        from app.security.auth import get_current_claims
        from app.security.permissions import Permission, has_permission

        claims = await get_current_claims(credentials)

        if not has_permission(claims, Permission.VOICE):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )

        return claims

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable.",
        ) from error


def get_voice_service(request: Request) -> VoiceCompanionService:
    """Return the lifespan-owned companion service."""

    service = getattr(
        request.app.state,
        "voice_companion_service",
        None,
    )

    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Voice service unavailable.",
        )

    return service


def get_subject(claims: dict[str, object]) -> str:
    """Extract the authenticated subject from JWT claims."""

    subject = claims.get("sub")

    if not isinstance(subject, str) or not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication claims.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return subject


def map_voice_error(error: Exception) -> HTTPException:
    """Map internal voice errors to safe HTTP responses."""

    if isinstance(
        error,
        (
            VoiceSessionNotFoundError,
            VoiceSessionAccessError,
        ),
    ):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voice session not found.",
        )

    if isinstance(error, VoiceTurnInProgressError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A voice turn is already in progress.",
        )

    if isinstance(error, VoiceTurnCancelledError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Voice turn was interrupted.",
        )

    if isinstance(error, VoiceProviderUnavailableError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Voice provider unavailable.",
        )

    if isinstance(error, VoiceProcessingError):
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Voice request could not be completed.",
        )

    if isinstance(error, ValueError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid voice request.",
        )

    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Voice service unavailable.",
    )


@router.post(
    "/sessions",
    response_model=VoiceSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_session(
    claims: Annotated[
        dict[str, object],
        Depends(require_voice_claims),
    ],
    service: Annotated[
        VoiceCompanionService,
        Depends(get_voice_service),
    ],
) -> VoiceSessionResponse:
    """Create a session scoped to the authenticated user."""

    session = await service.create_session(
        get_subject(claims),
    )

    return VoiceSessionResponse(
        session_id=session.id,
    )


@router.post(
    "/sessions/{session_id}/turns",
    response_model=VoiceTurnResponse,
)
async def process_turn(
    session_id: UUID,
    payload: VoiceTurnRequest,
    claims: Annotated[
        dict[str, object],
        Depends(require_voice_claims),
    ],
    service: Annotated[
        VoiceCompanionService,
        Depends(get_voice_service),
    ],
) -> VoiceTurnResponse:
    """Process one text transcript through the companion runtime."""

    try:
        turn = await service.process_turn(
            session_id=session_id,
            owner_id=get_subject(claims),
            transcript=payload.transcript,
            language=payload.language,
        )

    except Exception as error:
        raise map_voice_error(error) from error

    return VoiceTurnResponse(
        session_id=turn.session_id,
        request_id=turn.request_id,
        text=turn.text,
        expression=ExpressionResponse(
            emotion=turn.expression.emotion,
            expression=turn.expression.expression,
            gesture=turn.expression.gesture,
            gaze=turn.expression.gaze,
            lip_sync=turn.expression.lip_sync,
        ),
        token_usage=TokenUsageResponse(
            prompt_tokens=turn.token_usage.prompt_tokens,
            completion_tokens=turn.token_usage.completion_tokens,
            total_tokens=turn.token_usage.total_tokens,
        ),
    )


@router.post(
    "/sessions/{session_id}/audio-turn",
)
async def process_audio_turn(
    session_id: UUID,
    request: Request,
    claims: Annotated[
        dict[str, object],
        Depends(require_voice_claims),
    ],
    service: Annotated[
        VoiceCompanionService,
        Depends(get_voice_service),
    ],
    language: str | None = None,
    voice: str | None = None,
) -> Response:
    """
    Process one audio turn through:

    STT -> Aiko companion runtime -> ElevenLabs TTS.
    """

    content_length = request.headers.get("content-length")

    if content_length is not None:
        try:
            if int(content_length) > settings.voice.max_audio_bytes:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="Audio payload is too large.",
                )

        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid content length.",
            ) from error

    try:
        audio = await request.body()

        if len(audio) > settings.voice.max_audio_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Audio payload is too large.",
            )

        result = await service.process_audio_turn(
            session_id=session_id,
            owner_id=get_subject(claims),
            audio=audio,
            content_type=request.headers.get(
                "content-type",
                "",
            ),
            language=language,
            voice=voice,
        )

    except HTTPException:
        raise

    except Exception as error:
        raise map_voice_error(error) from error

    turn = result.turn

    headers = {
        **_NO_STORE_HEADERS,
        "X-Voice-Request-Id": str(
            turn.request_id,
        ),
        "X-Voice-Session-Id": str(
            turn.session_id,
        ),
        "X-Voice-Transcript": result.transcript,
        "X-Voice-Response": turn.text,
        "X-Voice-Emotion": turn.expression.emotion,
        "X-Voice-Expression": turn.expression.expression,
        "X-Voice-Gesture": turn.expression.gesture,
        "X-Voice-Gaze": turn.expression.gaze,
        "X-Voice-Lip-Sync": turn.expression.lip_sync,
        "X-Voice-Prompt-Tokens": str(
            turn.token_usage.prompt_tokens,
        ),
        "X-Voice-Completion-Tokens": str(
            turn.token_usage.completion_tokens,
        ),
        "X-Voice-Total-Tokens": str(
            turn.token_usage.total_tokens,
        ),
    }

    return Response(
        content=result.audio.data,
        media_type=result.audio.content_type,
        headers=headers,
    )


@router.post(
    "/sessions/{session_id}/cancel",
    response_model=CancelTurnResponse,
)
async def cancel_turn(
    session_id: UUID,
    claims: Annotated[
        dict[str, object],
        Depends(require_voice_claims),
    ],
    service: Annotated[
        VoiceCompanionService,
        Depends(get_voice_service),
    ],
) -> CancelTurnResponse:
    """Interrupt the caller's active response for barge-in support."""

    try:
        cancelled = await service.cancel_turn(
            session_id,
            get_subject(claims),
        )

    except Exception as error:
        raise map_voice_error(error) from error

    return CancelTurnResponse(
        cancelled=cancelled,
    )


@router.post(
    "/transcriptions",
    response_model=TranscriptionResponse,
)
async def transcribe_audio(
    request: Request,
    claims: Annotated[
        dict[str, object],
        Depends(require_voice_claims),
    ],
    service: Annotated[
        VoiceCompanionService,
        Depends(get_voice_service),
    ],
    language: str | None = None,
) -> TranscriptionResponse:
    """Transcribe raw audio without retaining the source bytes on disk."""

    del claims

    content_length = request.headers.get("content-length")

    if content_length is not None:
        try:
            if int(content_length) > settings.voice.max_audio_bytes:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="Audio payload is too large.",
                )

        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid content length.",
            ) from error

    try:
        audio = await request.body()

        result = await service.transcribe(
            audio,
            content_type=request.headers.get(
                "content-type",
                "",
            ),
            language=language,
        )

    except HTTPException:
        raise

    except Exception as error:
        raise map_voice_error(error) from error

    return TranscriptionResponse(
        transcript=result.text,
        language=result.language,
        duration_seconds=result.duration_seconds,
    )


@router.post(
    "/synthesis",
)
async def synthesize_audio(
    payload: SynthesisRequest,
    claims: Annotated[
        dict[str, object],
        Depends(require_voice_claims),
    ],
    service: Annotated[
        VoiceCompanionService,
        Depends(get_voice_service),
    ],
) -> Response:
    """Generate a non-persistent audio response using configured TTS."""

    del claims

    try:
        audio = await service.synthesize(
            payload.text,
            voice=payload.voice,
            language=payload.language,
        )

    except Exception as error:
        raise map_voice_error(error) from error

    return Response(
        content=audio.data,
        media_type=audio.content_type,
        headers=_NO_STORE_HEADERS,
    )


@router.post(
    "/synthesis/stream",
)
async def stream_synthesis_audio(
    payload: SynthesisRequest,
    claims: Annotated[
        dict[str, object],
        Depends(require_voice_claims),
    ],
    service: Annotated[
        VoiceCompanionService,
        Depends(get_voice_service),
    ],
) -> StreamingResponse:
    """Stream generated TTS audio without persisting it."""

    del claims

    try:
        service.ensure_synthesis_available()

    except Exception as error:
        raise map_voice_error(error) from error

    async def audio_stream() -> AsyncIterator[bytes]:
        try:
            async for chunk in service.stream_synthesis(
                payload.text,
                voice=payload.voice,
                language=payload.language,
            ):
                yield chunk

        except Exception as error:
            raise map_voice_error(error) from error

    return StreamingResponse(
        audio_stream(),
        media_type="audio/mpeg",
        headers=_NO_STORE_HEADERS,
    )