"""Weings AI backend application."""

from fastapi import FastAPI

from app.api.router import router as api_router
from app.core.lifecycle import lifespan


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""

    application = FastAPI(
        title="Weings AI",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    application.include_router(api_router)

    return application


app = create_application()
