"""Database health check."""

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.infrastructure.database.session import SessionLocal


async def check_database_health() -> bool:
    """Return the database health status."""

    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))

        return True

    except SQLAlchemyError:
        return False