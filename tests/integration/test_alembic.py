import os

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from afrinograph.config import settings


@pytest.mark.integration
@pytest.mark.asyncio
async def test_alembic_upgrade_head_no_op() -> None:
    """Test that running alembic upgrade head against test database succeeds as a no-op with zero tables."""
    test_db_url = settings.test_database_url
    sync_test_db_url = test_db_url.replace("postgresql+asyncpg://", "postgresql://")
    os.environ["DATABASE_URL"] = test_db_url

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", sync_test_db_url)

    command.upgrade(alembic_cfg, "head")

    engine = create_async_engine(test_db_url)
    async with engine.connect() as conn:
        result_all = await conn.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        )
        all_tables = [row[0] for row in result_all.fetchall()]
        for t in all_tables:
            assert t == "alembic_version"

    await engine.dispose()
