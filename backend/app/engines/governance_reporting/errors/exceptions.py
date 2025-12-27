"""Custom exceptions for Governance Reporting Engine."""


class GovernanceReportingException(Exception):
    """Base exception for governance reporting errors."""
    pass


class InvalidReportTypeError(GovernanceReportingException):
    """Raised when report type is invalid."""
    pass


class DataAccessError(GovernanceReportingException):
    """Raised when unable to access source data."""
    pass


class PersistenceError(GovernanceReportingException):
    """Raised when unable to persist governance report."""
    pass
