"""Application lifecycle."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.logger import get_logger
from app.core.settings import settings

logger = get_logger(__name__)


async def startup(app: FastAPI) -> None:
    """Run application startup tasks."""

    logger.info("Starting Weings AI backend...")

    settings.validate_runtime_configuration()

    from app.services.speech.service import build_voice_companion_service

    app.state.voice_companion_service = (
        build_voice_companion_service()
    )

    logger.info("Startup completed.")


async def shutdown(app: FastAPI) -> None:
    """Run application shutdown tasks."""

    logger.info("Shutting down Weings AI backend...")

    service = getattr(
        app.state,
        "voice_companion_service",
        None,
    )

    if service is not None:
        await service.close()

    # These clients are created by the existing infrastructure modules. They
    # are closed here instead of leaking sockets during server reloads/tests.
    from app.infrastructure.cache.client import redis_client
    from app.infrastructure.database.engine import engine
    from app.infrastructure.vectorstore.client import qdrant_client

    await redis_client.aclose()
    await qdrant_client.close()
    await engine.dispose()

    logger.info("Shutdown completed.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan."""

    await startup(app)

    yield

    await shutdown(app)
