from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from afrinograph.config import settings


def create_engine(database_url: str | None = None) -> AsyncEngine:
    """Creates an async SQLAlchemy engine. Lazy initialization: does not connect immediately."""
    url = database_url or settings.database_url
    return create_async_engine(url, echo=False, future=True)


# Module-level engine and session factory created lazily
engine: AsyncEngine = create_engine()
async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)
