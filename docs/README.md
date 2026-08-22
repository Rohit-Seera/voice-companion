# Weings AI Voice Companion Backend

This package keeps the frozen backend architecture intact and completes the first production-shaped Voice Companion slice: authenticated sessions, turn processing through the existing runtime pipeline, safe expression directives for the animated companion UI, provider-neutral speech contracts, lifecycle wiring, health probes, and focused tests.

## What Is Implemented

- `POST /api/v1/voice/sessions` creates an authenticated voice session owned by the JWT subject.
- `POST /api/v1/voice/sessions/{session_id}/turns` accepts text, runs the existing runtime graph, and returns assistant text plus animation/expression directives.
- `POST /api/v1/voice/sessions/{session_id}/cancel` supports barge-in style cancellation.
- `POST /api/v1/voice/transcriptions` accepts bounded in-memory audio and calls an injected speech-to-text provider.
- `POST /api/v1/voice/synthesis` and `/synthesis/stream` expose provider-neutral text-to-speech hooks.
- `/api/v1/health/live` and `/api/v1/health/ready` split liveness from dependency readiness.

The speech service intentionally defines stable provider contracts instead of hardcoding a paid vendor SDK. Add STT/TTS adapters behind `app.services.speech.contracts` when you choose the final provider.

## Local Run

```powershell
Copy-Item .env.example .env
# Set SECURITY_JWT_SECRET_KEY to a random 64+ character value before using auth endpoints.
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Docker:

```powershell
docker compose up --build
```

## Frontend Contract

For the current 2D/3D companion UI, the important response shape is:

```json
{
  "session_id": "uuid",
  "turn_id": "uuid",
  "text": "Good luck Rohit, I am with you.",
  "expression": {
    "emotion": "supportive",
    "face": "soft_concern",
    "eyes": "gentle_focus",
    "gesture": "hand_to_heart",
    "mouth": "soft_smile",
    "intensity": 0.65,
    "duration_ms": 4200
  }
}
```

The animation layer should map `expression.face`, `eyes`, `gesture`, `mouth`, `intensity`, and `duration_ms` to your character rig, Live2D-style layers, or sprite animation pack.

## Security Notes

- Voice APIs require a JWT with `voice:use` permission.
- Session ownership is enforced server side; cross-user session access returns a generic `404`.
- Raw audio is bounded by `VOICE_MAX_AUDIO_BYTES` and processed in memory only.
- User transcript and audio content are not logged by the voice API.
- Production startup validates JWT secret strength and security settings.
- TTS/STT providers are optional adapters; missing providers return safe `503` responses.

## Known Gaps For Next Phase

- Persistent user accounts, conversation transcripts, and long-term memory migration scripts are not added here because the frozen skeleton does not yet define those domain models.
- Real STT/TTS adapters still need provider selection and credentials.
- Full pytest execution could not be completed in the Codex sandbox because the bundled archive virtualenv is CPython 3.13-specific while only the local bundled runtime is executable here.
