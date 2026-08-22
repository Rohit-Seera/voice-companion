"""Application exceptions."""


class WeingsError(Exception):
    """Base exception for the application."""


class ConfigurationError(WeingsError):
    """Raised when the application configuration is invalid."""


class ValidationError(WeingsError):
    """Raised when validation fails."""


class AuthenticationError(WeingsError):
    """Raised when authentication fails."""


class AuthorizationError(WeingsError):
    """Raised when the user is not authorized."""


class ProviderError(WeingsError):
    """Raised when an AI provider fails."""


class RuntimeError(WeingsError):
    """Raised when the runtime encounters an error."""


class DatabaseError(WeingsError):
    """Raised when a database operation fails."""


class CacheError(WeingsError):
    """Raised when a cache operation fails."""


class VectorStoreError(WeingsError):
    """Raised when a vector database operation fails."""


class ServiceError(WeingsError):
    """Raised when an external service fails."""