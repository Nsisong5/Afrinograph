from __future__ import annotations

from afrinograph.shared.domain.errors import ApplicationError


class AdapterError(ApplicationError):
    """Base for all source-adapter errors. Carries whether a retry is safe."""

    def __init__(self, message: str, *, retryable: bool):
        super().__init__(message)
        self.retryable = retryable


class SourceUnavailableError(AdapterError):
    """Raised when an external source is unavailable (network error, timeout)."""

    def __init__(self, message: str = "Source unavailable", *, retryable: bool = True):
        super().__init__(message, retryable=retryable)


class AuthenticationError(AdapterError):
    """Raised when source authentication or authorization fails."""

    def __init__(self, message: str = "Authentication failed", *, retryable: bool = False):
        super().__init__(message, retryable=retryable)


class RateLimitedError(AdapterError):
    """Raised when rate limited by the external source."""

    def __init__(
        self,
        message: str = "Rate limited",
        *,
        retry_after_seconds: float | None = None,
        retryable: bool = True,
    ):
        super().__init__(message, retryable=retryable)
        self.retry_after_seconds = retry_after_seconds


class InvalidConfigurationError(AdapterError):
    """Raised when adapter configuration is invalid."""

    def __init__(self, message: str = "Invalid configuration", *, retryable: bool = False):
        super().__init__(message, retryable=retryable)


class MalformedResponseError(AdapterError):
    """Raised when source response is malformed or unexpected."""

    def __init__(self, message: str = "Malformed response", *, retryable: bool = False):
        super().__init__(message, retryable=retryable)


class InvalidCheckpointError(AdapterError):
    """Raised when a supplied checkpoint cannot be interpreted or resumed from."""

    def __init__(self, message: str = "Invalid checkpoint"):
        super().__init__(message, retryable=False)
