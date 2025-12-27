"""Custom exceptions for Institutional Analytics Engine."""


class InstitutionalAnalyticsException(Exception):
    """Base exception for institutional analytics errors."""
    pass


class InsufficientCohortSizeError(InstitutionalAnalyticsException):
    """Raised when cohort size is below minimum threshold."""
    pass


class InvalidScopeError(InstitutionalAnalyticsException):
    """Raised when aggregation scope is invalid."""
    pass


class DataAccessError(InstitutionalAnalyticsException):
    """Raised when unable to access source data."""
    pass


class PersistenceError(InstitutionalAnalyticsException):
    """Raised when unable to persist analytics snapshot."""
    pass
