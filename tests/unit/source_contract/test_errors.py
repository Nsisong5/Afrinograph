from __future__ import annotations

import pytest

from afrinograph.modules.source_contract.domain.errors import (
    AdapterError,
    AuthenticationError,
    InvalidCheckpointError,
    InvalidConfigurationError,
    MalformedResponseError,
    RateLimitedError,
    SourceUnavailableError,
)


@pytest.mark.unit
def test_adapter_error_hierarchy() -> None:
    err = AdapterError("base", retryable=True)
    assert err.retryable is True
    assert isinstance(err, Exception)


@pytest.mark.unit
def test_source_unavailable_default_retryable() -> None:
    err = SourceUnavailableError()
    assert err.retryable is True
    assert isinstance(err, AdapterError)


@pytest.mark.unit
def test_authentication_error_default_retryable() -> None:
    err = AuthenticationError()
    assert err.retryable is False
    assert isinstance(err, AdapterError)


@pytest.mark.unit
def test_rate_limited_error_properties() -> None:
    err = RateLimitedError(retry_after_seconds=30.5)
    assert err.retryable is True
    assert err.retry_after_seconds == 30.5

    err_default = RateLimitedError()
    assert err_default.retry_after_seconds is None


@pytest.mark.unit
def test_invalid_configuration_error_default_retryable() -> None:
    err = InvalidConfigurationError()
    assert err.retryable is False


@pytest.mark.unit
def test_malformed_response_error_default_retryable() -> None:
    err = MalformedResponseError()
    assert err.retryable is False


@pytest.mark.unit
def test_invalid_checkpoint_error_properties() -> None:
    err = InvalidCheckpointError("bad token")
    assert err.retryable is False
    assert "bad token" in str(err)
