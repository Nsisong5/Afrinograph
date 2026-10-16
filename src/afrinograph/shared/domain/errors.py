class AfrinographError(Exception):
    """Base exception for all Afrinograph domain and application errors."""


class DomainError(AfrinographError):
    """Base exception for domain rule violations."""


class NotFoundError(AfrinographError):
    """Raised when a requested resource is not found."""


class ConflictError(AfrinographError):
    """Raised when a resource conflict occurs (e.g., duplicate unique entity)."""


class ValidationError(AfrinographError):
    """Raised when input data or value object validation fails."""


class ApplicationError(AfrinographError):
    """Base exception for application-level errors."""


class AdapterError(ApplicationError):
    """Raised when an external data source adapter encounters an error."""
