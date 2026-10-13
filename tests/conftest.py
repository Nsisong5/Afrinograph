import pytest
from sqlalchemy import text

from afrinograph.config import settings
from afrinograph.shared.infrastructure.db import create_engine


@pytest.fixture(autouse=True, scope="function")
async def truncate_tables(request: pytest.FixtureRequest) -> None:
    """Truncate all tables in public schema between integration tests to ensure clean state."""
    # Only run DB truncation for integration tests
    if "integration" not in request.node.name and not any(m.name == "integration" for m in request.node.iter_markers()):
        yield
        return

    test_db_url = settings.test_database_url
    engine = create_engine(test_db_url)
    try:
        async with engine.begin() as conn:
            result = await conn.execute(
                text(
                    "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename != 'alembic_version'"
                )
            )
            tables = [row[0] for row in result.fetchall()]
            if tables:
                table_names = ", ".join(f'"{t}"' for t in tables)
                await conn.execute(text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE"))
    finally:
        await engine.dispose()
    yield
