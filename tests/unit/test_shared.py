from datetime import UTC, datetime

import pytest

from afrinograph.shared.domain.errors import (
    AfrinographError,
    ConflictError,
    DomainError,
    NotFoundError,
    ValidationError,
)
from afrinograph.shared.infrastructure.clock import SystemClock


@pytest.mark.unit
def test_system_clock_now() -> None:
    clock = SystemClock()
    t1 = clock.now()
    assert isinstance(t1, datetime)
    assert t1.tzinfo is not None
    assert t1.tzinfo == UTC


@pytest.mark.unit
def test_db_import_does_not_connect() -> None:
    """Verify that importing shared.infrastructure.db does not trigger an immediate database connection."""
    from afrinograph.shared.infrastructure.db import async_session_factory, engine
    assert engine is not None
    assert async_session_factory is not None
    assert engine.sync_engine.pool.checkedout() == 0


@pytest.mark.unit
def test_domain_exceptions() -> None:
    with pytest.raises(AfrinographError):
        raise DomainError("test domain error")
    with pytest.raises(AfrinographError):
        raise NotFoundError("test not found")
    with pytest.raises(AfrinographError):
        raise ConflictError("test conflict")
    with pytest.raises(AfrinographError):
        raise ValidationError("test validation")
