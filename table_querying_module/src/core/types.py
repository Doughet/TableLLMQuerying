"""
Core type definitions for the Table Querying Module.

This module defines all the core data types and structures used throughout
the system, providing a single source of truth for data formats.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union, TypeVar, Generic
from datetime import datetime
from enum import Enum
from pathlib import Path

# Generic type variables
T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')


# Enumerations
class DocumentFormat(Enum):
    """Supported document formats."""
    HTML = "html"
    MARKDOWN = "markdown"
    JSON = "json"
    XML = "xml"


class TableFormat(Enum):
    """Table representation formats."""
    HTML = "html"
    JSON = "json"
    CSV = "csv"
    DATAFRAME = "dataframe"


class DataType(Enum):
    """Supported data types for table columns."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    JSON = "json"
    UNKNOWN = "unknown"


class ProcessingStatus(Enum):
    """Processing status values."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Core data structures
@dataclass
class Document:
    """Represents a document to be processed."""
    content: str
    source_path: Optional[Path] = None
    format: DocumentFormat = DocumentFormat.HTML
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def filename(self) -> str:
        """Get the filename from source path."""
        return self.source_path.name if self.source_path else "unknown"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'content': self.content,
            'source_path': str(self.source_path) if self.source_path else None,
            'format': self.format.value,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class Table:
    """Represents an extracted table."""
    table_id: str
    content: str
    format: TableFormat
    position: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_document: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'table_id': self.table_id,
            'content': self.content,
            'format': self.format.value,
            'position': self.position,
            'metadata': self.metadata,
            'source_document': self.source_document
        }


@dataclass
class Schema:
    """Represents a table schema."""
    table_id: str
    columns: List[str]
    column_types: Dict[str, DataType]
    row_count: int
    sample_data: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def column_count(self) -> int:
        """Get the number of columns."""
        return len(self.columns)
    
    def get_column_type(self, column: str) -> DataType:
        """Get the data type for a column."""
        return self.column_types.get(column, DataType.UNKNOWN)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'table_id': self.table_id,
            'columns': self.columns,
            'column_types': {k: v.value for k, v in self.column_types.items()},
            'row_count': self.row_count,
            'sample_data': self.sample_data,
            'metadata': self.metadata
        }


@dataclass
class Description:
    """Represents a table description."""
    table_id: str
    content: str
    summary: Optional[str] = None
    key_insights: List[str] = field(default_factory=list)
    confidence: float = 1.0
    generated_by: Optional[str] = None
    generated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'table_id': self.table_id,
            'content': self.content,
            'summary': self.summary,
            'key_insights': self.key_insights,
            'confidence': self.confidence,
            'generated_by': self.generated_by,
            'generated_at': self.generated_at.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class Query:
    """Represents a user query."""
    content: str
    query_type: str = "natural_language"
    context: Dict[str, Any] = field(default_factory=dict)
    filters: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'content': self.content,
            'query_type': self.query_type,
            'context': self.context,
            'filters': self.filters,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class QueryResult:
    """Represents the result of a query."""
    success: bool
    data: List[Dict[str, Any]]
    query: Optional[Query] = None
    execution_time: float = 0.0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def row_count(self) -> int:
        """Get the number of rows returned."""
        return len(self.data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'success': self.success,
            'data': self.data,
            'query': self.query.to_dict() if self.query else None,
            'execution_time': self.execution_time,
            'error_message': self.error_message,
            'row_count': self.row_count,
            'metadata': self.metadata
        }


@dataclass
class ProcessingResult:
    """Represents the result of document processing."""
    success: bool
    document: Document
    tables: List[Table] = field(default_factory=list)
    schemas: List[Schema] = field(default_factory=list)
    descriptions: List[Description] = field(default_factory=list)
    status: ProcessingStatus = ProcessingStatus.COMPLETED
    error_message: Optional[str] = None
    processing_time: float = 0.0
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def table_count(self) -> int:
        """Get the number of tables processed."""
        return len(self.tables)
    
    @property
    def successful_tables(self) -> int:
        """Get the number of successfully processed tables."""
        return len([t for t in self.tables if t.table_id in [s.table_id for s in self.schemas]])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'success': self.success,
            'document': self.document.to_dict(),
            'tables': [t.to_dict() for t in self.tables],
            'schemas': [s.to_dict() for s in self.schemas],
            'descriptions': [d.to_dict() for d in self.descriptions],
            'status': self.status.value,
            'error_message': self.error_message,
            'processing_time': self.processing_time,
            'session_id': self.session_id,
            'table_count': self.table_count,
            'successful_tables': self.successful_tables,
            'metadata': self.metadata
        }


@dataclass
class ChatResponse:
    """Represents a chat response."""
    content: str
    query: Query
    query_result: Optional[QueryResult] = None
    success: bool = True
    response_type: str = "answer"
    suggestions: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    response_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'content': self.content,
            'query': self.query.to_dict(),
            'query_result': self.query_result.to_dict() if self.query_result else None,
            'success': self.success,
            'response_type': self.response_type,
            'suggestions': self.suggestions,
            'error_message': self.error_message,
            'response_time': self.response_time,
            'metadata': self.metadata
        }


# Configuration types
@dataclass
class ComponentConfig:
    """Base configuration for components."""
    component_type: str
    implementation: str
    config: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    priority: int = 0
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self.config[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'component_type': self.component_type,
            'implementation': self.implementation,
            'config': self.config,
            'enabled': self.enabled,
            'priority': self.priority
        }


@dataclass
class SystemConfig:
    """System-wide configuration."""
    components: Dict[str, ComponentConfig] = field(default_factory=dict)
    global_settings: Dict[str, Any] = field(default_factory=dict)
    environment: str = "development"
    debug: bool = False
    
    def get_component_config(self, component_type: str) -> Optional[ComponentConfig]:
        """Get configuration for a specific component type."""
        return self.components.get(component_type)
    
    def add_component_config(self, component_type: str, config: ComponentConfig) -> None:
        """Add configuration for a component."""
        self.components[component_type] = config
    
    def get_global_setting(self, key: str, default: Any = None) -> Any:
        """Get a global setting value."""
        return self.global_settings.get(key, default)


# Result containers
@dataclass
class ValidationResult:
    """Result of validation operations."""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_error(self, message: str) -> None:
        """Add an error message."""
        self.errors.append(message)
        self.valid = False
    
    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)
    
    def get_error_summary(self) -> str:
        """Get a summary of validation errors and warnings."""
        summary_parts = []
        
        if self.errors:
            summary_parts.append(f"Errors: {'; '.join(self.errors)}")
        
        if self.warnings:
            summary_parts.append(f"Warnings: {'; '.join(self.warnings)}")
        
        return " | ".join(summary_parts) if summary_parts else "No issues found"


# Generic containers
@dataclass
class PagedResult(Generic[T]):
    """Paginated result container."""
    items: List[T]
    total_count: int
    page: int
    page_size: int
    has_next: bool = False
    has_previous: bool = False
    
    @property
    def total_pages(self) -> int:
        """Calculate total number of pages."""
        return (self.total_count + self.page_size - 1) // self.page_size