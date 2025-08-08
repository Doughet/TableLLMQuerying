"""
Exception hierarchy for the Table Querying Module.

This module defines all custom exceptions used throughout the system,
providing a clear error handling structure.
"""

from typing import Optional, Dict, Any


class TableQueryingError(Exception):
    """Base exception for all Table Querying Module errors."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.cause = cause
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary format."""
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'error_code': self.error_code,
            'details': self.details,
            'cause': str(self.cause) if self.cause else None
        }


# Configuration and Validation Errors
class ConfigurationError(TableQueryingError):
    """Raised when there are configuration issues."""
    pass


class ValidationError(TableQueryingError):
    """Raised when data validation fails."""
    pass


class ComponentNotFoundError(TableQueryingError):
    """Raised when a requested component is not found."""
    pass


class ComponentInitializationError(TableQueryingError):
    """Raised when component initialization fails."""
    pass


# Processing Errors
class ProcessingError(TableQueryingError):
    """Base class for processing-related errors."""
    pass


class DocumentProcessingError(ProcessingError):
    """Raised when document processing fails."""
    pass


class TableExtractionError(ProcessingError):
    """Raised when table extraction fails."""
    pass


class SchemaGenerationError(ProcessingError):
    """Raised when schema generation fails."""
    pass


class DescriptionGenerationError(ProcessingError):
    """Raised when description generation fails."""
    pass


# Database Errors
class DatabaseError(TableQueryingError):
    """Base class for database-related errors."""
    pass


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""
    pass


class DatabaseQueryError(DatabaseError):
    """Raised when database query execution fails."""
    pass


class DatabaseIntegrityError(DatabaseError):
    """Raised when database integrity constraints are violated."""
    pass


class TableNotFoundError(DatabaseError):
    """Raised when a requested table is not found."""
    pass


# LLM Service Errors
class LLMError(TableQueryingError):
    """Base class for LLM service errors."""
    pass


class LLMConnectionError(LLMError):
    """Raised when LLM service connection fails."""
    pass


class LLMRequestError(LLMError):
    """Raised when LLM request fails."""
    pass


class LLMResponseError(LLMError):
    """Raised when LLM response is invalid or unparseable."""
    pass


class LLMRateLimitError(LLMError):
    """Raised when LLM rate limit is exceeded."""
    pass


class LLMQuotaExceededError(LLMError):
    """Raised when LLM quota is exceeded."""
    pass


# Query Processing Errors
class QueryError(TableQueryingError):
    """Base class for query-related errors."""
    pass


class QueryParsingError(QueryError):
    """Raised when query parsing fails."""
    pass


class QueryExecutionError(QueryError):
    """Raised when query execution fails."""
    pass


class QueryTimeoutError(QueryError):
    """Raised when query execution times out."""
    pass


class UnsupportedQueryError(QueryError):
    """Raised when query type is not supported."""
    pass


# Chat Interface Errors
class ChatError(TableQueryingError):
    """Base class for chat interface errors."""
    pass


class ChatSessionError(ChatError):
    """Raised when chat session operations fail."""
    pass


class ChatContextError(ChatError):
    """Raised when chat context is invalid."""
    pass


# File and I/O Errors
class FileProcessingError(TableQueryingError):
    """Base class for file processing errors."""
    pass


class FileNotFoundError(FileProcessingError):
    """Raised when a required file is not found."""
    pass


class FileFormatError(FileProcessingError):
    """Raised when file format is not supported or invalid."""
    pass


class FileAccessError(FileProcessingError):
    """Raised when file access is denied."""
    pass


# Security and Permission Errors
class SecurityError(TableQueryingError):
    """Base class for security-related errors."""
    pass


class AuthenticationError(SecurityError):
    """Raised when authentication fails."""
    pass


class AuthorizationError(SecurityError):
    """Raised when authorization fails."""
    pass


class PermissionError(SecurityError):
    """Raised when operation is not permitted."""
    pass


# Utility functions for exception handling
def create_error_from_dict(error_dict: Dict[str, Any]) -> TableQueryingError:
    """Create an exception instance from dictionary representation."""
    error_type = error_dict.get('error_type', 'TableQueryingError')
    message = error_dict.get('message', 'Unknown error')
    error_code = error_dict.get('error_code')
    details = error_dict.get('details', {})
    
    # Map error type to exception class
    exception_classes = {
        'ConfigurationError': ConfigurationError,
        'ValidationError': ValidationError,
        'ProcessingError': ProcessingError,
        'DatabaseError': DatabaseError,
        'LLMError': LLMError,
        'QueryError': QueryError,
        'ChatError': ChatError,
        'FileProcessingError': FileProcessingError,
        'SecurityError': SecurityError,
    }
    
    exception_class = exception_classes.get(error_type, TableQueryingError)
    return exception_class(message, error_code, details)


def handle_exception(func):
    """Decorator for standardized exception handling."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except TableQueryingError:
            # Re-raise our custom exceptions as-is
            raise
        except Exception as e:
            # Wrap other exceptions in our base exception
            raise TableQueryingError(
                message=f"Unexpected error in {func.__name__}: {str(e)}",
                error_code="UNEXPECTED_ERROR",
                cause=e
            )
    return wrapper


class ErrorCollector:
    """Utility class for collecting and managing multiple errors."""
    
    def __init__(self):
        self.errors: List[TableQueryingError] = []
        self.warnings: List[str] = []
    
    def add_error(self, error: TableQueryingError) -> None:
        """Add an error to the collection."""
        self.errors.append(error)
    
    def add_warning(self, warning: str) -> None:
        """Add a warning to the collection."""
        self.warnings.append(warning)
    
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0
    
    def get_error_summary(self) -> str:
        """Get a summary of all errors."""
        if not self.has_errors():
            return "No errors"
        
        return f"{len(self.errors)} error(s): " + "; ".join([e.message for e in self.errors])
    
    def raise_if_errors(self) -> None:
        """Raise an exception if there are any errors."""
        if self.has_errors():
            if len(self.errors) == 1:
                raise self.errors[0]
            else:
                raise ProcessingError(
                    message=f"Multiple errors occurred: {self.get_error_summary()}",
                    error_code="MULTIPLE_ERRORS",
                    details={"errors": [e.to_dict() for e in self.errors]}
                )