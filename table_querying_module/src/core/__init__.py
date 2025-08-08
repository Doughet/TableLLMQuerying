"""
Core abstractions and interfaces for the Table Querying Module.

This package provides the highest-level interfaces and component definitions
that define the system architecture.
"""

from .interfaces import *
from .types import *
from .exceptions import *
from .registry import ComponentRegistry
from .context import ProcessingContext

__all__ = [
    # Interfaces
    'DocumentProcessor', 'TableExtractor', 'SchemaGenerator', 'TableDescriptor',
    'DatabaseClient', 'LLMClient', 'QueryProcessor', 'ChatInterface',
    
    # Types
    'Document', 'Table', 'Schema', 'Description', 'Query', 'QueryResult',
    'ProcessingResult', 'ChatResponse',
    
    # Exceptions
    'TableQueryingError', 'ProcessingError', 'DatabaseError', 'LLMError',
    'ConfigurationError', 'ValidationError',
    
    # Registry and Context
    'ComponentRegistry', 'ProcessingContext'
]