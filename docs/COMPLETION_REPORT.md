# Weings AI Voice Companion Backend Completion Report

## Scope

The website work is paused. This delivery completes the backend Voice Companion slice inside the existing frozen skeleton without changing the locked top-level architecture.

## Implemented Files

- `app/runtime/companion_workflow.py` wires the default companion workflow through existing runtime nodes.
- `app/services/speech/contracts.py` defines provider-neutral STT/TTS contracts.
- `app/services/speech/service.py` implements voice sessions, turns, barge-in cancellation, STT/TTS orchestration, and safe provider error handling.
- `app/services/speech/expression.py` maps runtime emotion/context into constrained frontend animation directives.
- `app/api/v1/voice.py` exposes authenticated voice session, turn, cancel, transcription, and synthesis endpoints.
- `app/core/lifecycle.py` now creates and closes the voice companion service with application lifespan.
- `app/api/v1/health.py` now includes liveness and readiness probes.
- `.env.example`, `Dockerfile`, `docker-compose.yml`, and `docs/README.md` were filled for local/deployment handoff.

## API Contract

- `POST /api/v1/voice/sessions`
- `POST /api/v1/voice/sessions/{session_id}/turns`
- `POST /api/v1/voice/sessions/{session_id}/cancel`
- `POST /api/v1/voice/transcriptions`
- `POST /api/v1/voice/synthesis`
- `POST /api/v1/voice/synthesis/stream`
- `GET /api/v1/health/live`
- `GET /api/v1/health/ready`

## Validation

Commands run successfully:

```powershell
python -m compileall -q app tests
```

```powershell
.testenv\Scripts\python.exe -m pytest tests\api\test_voice.py tests\services\speech\test_service.py -q
```

Result:

```text
7 passed, 1 warning
```

```powershell
.testenv\Scripts\python.exe -m pytest -q --import-mode=importlib
```

Result:

```text
702 passed, 2 warnings
```

The plain `pytest -q` collection mode hits duplicate test basename collisions already present in the skeleton test layout. `--import-mode=importlib` resolves that collection issue and the full suite passes.

## Security Review

Reviewed the new voice surface for authentication, authorization, ownership, sensitive content handling, and resource limits.

Controls in place:

- Voice endpoints require a valid bearer JWT.
- `voice:use` permission is enforced before voice operations.
- Sessions are owned by JWT subject and cross-user access returns a generic `404`.
- Raw audio is bounded by `VOICE_MAX_AUDIO_BYTES`.
- Audio stays in memory; no temporary file write contract was introduced.
- Voice transcript and audio content are not logged by the voice API.
- Provider/runtime exceptions are mapped to generic responses.
- Audio and synthesis responses use `Cache-Control: no-store`.
- Production startup validates JWT secret strength through the existing JWT service.

No source-backed vulnerability was found in the new voice implementation during this focused pass.

## Remaining Product Gaps

- Real STT/TTS adapters still need to be selected and wired behind the provider-neutral contracts.
- Persistent users, conversations, long-term memory, and Alembic migrations remain a next phase because the frozen skeleton does not yet define complete domain models for those tables.
- The animation/Live2D/2D character layer should consume the `expression` directive fields and map them to face, gaze, gesture, and lip-sync animation states.
