"""
Core interfaces for the Table Querying Module.

This module defines the highest-level interfaces that define the system's
architecture. Components implementing these interfaces can be easily swapped.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Iterator, AsyncIterator
from pathlib import Path

from .types import (
    Document, Table, Schema, Description, Query, QueryResult,
    ProcessingResult, ChatResponse, ValidationResult, ComponentConfig
)
from .exceptions import TableQueryingError


# Document Processing Interfaces
class DocumentProcessor(ABC):
    """High-level interface for complete document processing."""
    
    @abstractmethod
    def process_document(self, document: Document) -> ProcessingResult:
        """
        Process a complete document through the entire pipeline.
        
        Args:
            document: Document to process
            
        Returns:
            Complete processing result
        """
        pass
    
    @abstractmethod
    def process_file(self, file_path: Path) -> ProcessingResult:
        """
        Process a file through the entire pipeline.
        
        Args:
            file_path: Path to file to process
            
        Returns:
            Complete processing result
        """
        pass
    
    @abstractmethod
    def validate_document(self, document: Document) -> ValidationResult:
        """Validate document format and content."""
        pass


class TableExtractor(ABC):
    """Interface for extracting tables from documents."""
    
    @abstractmethod
    def extract_tables(self, document: Document) -> List[Table]:
        """
        Extract tables from a document.
        
        Args:
            document: Document to extract tables from
            
        Returns:
            List of extracted tables
        """
        pass
    
    @abstractmethod
    def supported_formats(self) -> List[str]:
        """Get list of supported document formats."""
        pass
    
    @abstractmethod
    def validate_table(self, table: Table) -> ValidationResult:
        """Validate extracted table."""
        pass


class SchemaGenerator(ABC):
    """Interface for generating table schemas."""
    
    @abstractmethod
    def generate_schema(self, table: Table) -> Schema:
        """
        Generate schema for a table.
        
        Args:
            table: Table to analyze
            
        Returns:
            Generated schema
        """
        pass
    
    @abstractmethod
    def generate_schemas(self, tables: List[Table]) -> List[Schema]:
        """Generate schemas for multiple tables."""
        pass
    
    @abstractmethod
    def infer_types(self, data: List[Dict[str, Any]]) -> Dict[str, str]:
        """Infer data types from sample data."""
        pass


class TableDescriptor(ABC):
    """Interface for generating table descriptions."""
    
    @abstractmethod
    def describe_table(self, schema: Schema, context: Optional[str] = None) -> Description:
        """
        Generate description for a table based on its schema.
        
        Args:
            schema: Table schema
            context: Optional context for better descriptions
            
        Returns:
            Generated description
        """
        pass
    
    @abstractmethod
    def describe_tables(self, schemas: List[Schema], context: Optional[str] = None) -> List[Description]:
        """Generate descriptions for multiple tables."""
        pass
    
    @abstractmethod
    def validate_description(self, description: Description) -> ValidationResult:
        """Validate generated description."""
        pass


# Data Access Interfaces
class DatabaseClient(ABC):
    """Interface for database operations."""
    
    @abstractmethod
    def store_processing_result(self, result: ProcessingResult) -> bool:
        """Store complete processing result in database."""
        pass
    
    @abstractmethod
    def get_table_by_id(self, table_id: str) -> Optional[Schema]:
        """Retrieve table schema by ID."""
        pass
    
    @abstractmethod
    def search_tables(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[Schema]:
        """Search for tables matching criteria."""
        pass
    
    @abstractmethod
    def execute_query(self, query: Query) -> QueryResult:
        """Execute a structured query against the database."""
        pass
    
    @abstractmethod
    def get_database_summary(self) -> Dict[str, Any]:
        """Get database statistics and summary."""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Check database health and connectivity."""
        pass


# LLM Integration Interfaces
class LLMClient(ABC):
    """Interface for LLM service interactions."""
    
    @abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text completion for a prompt."""
        pass
    
    @abstractmethod
    def generate_description(self, schema: Schema, context: Optional[str] = None) -> Description:
        """Generate table description using LLM."""
        pass
    
    @abstractmethod
    def generate_sql(self, natural_query: str, database_schema: Dict[str, Any]) -> str:
        """Generate SQL query from natural language."""
        pass
    
    @abstractmethod
    def analyze_query(self, query: str, available_tables: List[Schema]) -> Dict[str, Any]:
        """Analyze if query can be fulfilled with available data."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if LLM service is available."""
        pass


# Query Processing Interfaces
class QueryProcessor(ABC):
    """Interface for processing user queries."""
    
    @abstractmethod
    def process_query(self, query: Query) -> QueryResult:
        """
        Process a user query and return results.
        
        Args:
            query: User query to process
            
        Returns:
            Query execution result
        """
        pass
    
    @abstractmethod
    def parse_natural_language(self, text: str) -> Query:
        """Parse natural language into structured query."""
        pass
    
    @abstractmethod
    def validate_query(self, query: Query) -> ValidationResult:
        """Validate query structure and feasibility."""
        pass
    
    @abstractmethod
    def get_query_suggestions(self, partial_query: str) -> List[str]:
        """Get query suggestions based on partial input."""
        pass


class ChatInterface(ABC):
    """Interface for chat-based interactions."""
    
    @abstractmethod
    def process_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> ChatResponse:
        """
        Process a chat message and generate response.
        
        Args:
            message: User message
            context: Optional conversation context
            
        Returns:
            Chat response
        """
        pass
    
    @abstractmethod
    def start_session(self) -> str:
        """Start a new chat session."""
        pass
    
    @abstractmethod
    def end_session(self, session_id: str) -> bool:
        """End a chat session."""
        pass
    
    @abstractmethod
    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get chat history for a session."""
        pass


# Component Management Interfaces
class ComponentManager(ABC):
    """Interface for managing system components."""
    
    @abstractmethod
    def register_component(self, component_type: str, component_class: type, config: ComponentConfig) -> None:
        """Register a component implementation."""
        pass
    
    @abstractmethod
    def get_component(self, component_type: str) -> Any:
        """Get a component instance by type."""
        pass
    
    @abstractmethod
    def list_components(self) -> Dict[str, List[str]]:
        """List all registered components by type."""
        pass
    
    @abstractmethod
    def validate_component(self, component_type: str, component_class: type) -> ValidationResult:
        """Validate component implementation against interface."""
        pass


class PluginManager(ABC):
    """Interface for managing plugins."""
    
    @abstractmethod
    def load_plugin(self, plugin_path: Path) -> None:
        """Load a plugin from file."""
        pass
    
    @abstractmethod
    def discover_plugins(self, search_paths: List[Path]) -> List[str]:
        """Discover available plugins in search paths."""
        pass
    
    @abstractmethod
    def get_plugin_info(self, plugin_name: str) -> Dict[str, Any]:
        """Get information about a loaded plugin."""
        pass
    
    @abstractmethod
    def list_plugins(self) -> List[str]:
        """List all loaded plugins."""
        pass


# Configuration Management Interfaces
class ConfigurationManager(ABC):
    """Interface for managing system configuration."""
    
    @abstractmethod
    def load_config(self, config_path: Optional[Path] = None) -> Dict[str, Any]:
        """Load configuration from file or environment."""
        pass
    
    @abstractmethod
    def save_config(self, config: Dict[str, Any], config_path: Path) -> bool:
        """Save configuration to file."""
        pass
    
    @abstractmethod
    def get_component_config(self, component_type: str) -> ComponentConfig:
        """Get configuration for a specific component."""
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate configuration structure and values."""
        pass
    
    @abstractmethod
    def merge_configs(self, *configs: Dict[str, Any]) -> Dict[str, Any]:
        """Merge multiple configuration dictionaries."""
        pass


# Monitoring and Observability Interfaces
class MetricsCollector(ABC):
    """Interface for collecting system metrics."""
    
    @abstractmethod
    def record_processing_time(self, operation: str, duration: float) -> None:
        """Record processing time for an operation."""
        pass
    
    @abstractmethod
    def increment_counter(self, metric_name: str, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        pass
    
    @abstractmethod
    def record_gauge(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record a gauge metric value."""
        pass
    
    @abstractmethod
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of collected metrics."""
        pass


class Logger(ABC):
    """Interface for structured logging."""
    
    @abstractmethod
    def log_info(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log info message."""
        pass
    
    @abstractmethod
    def log_warning(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log warning message."""
        pass
    
    @abstractmethod
    def log_error(self, message: str, error: Optional[Exception] = None, context: Optional[Dict[str, Any]] = None) -> None:
        """Log error message."""
        pass
    
    @abstractmethod
    def log_debug(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log debug message."""
        pass


# Streaming and Async Interfaces
class StreamingProcessor(ABC):
    """Interface for streaming/async document processing."""
    
    @abstractmethod
    async def process_document_async(self, document: Document) -> AsyncIterator[ProcessingResult]:
        """Process document asynchronously with streaming results."""
        pass
    
    @abstractmethod
    def process_documents_batch(self, documents: List[Document]) -> Iterator[ProcessingResult]:
        """Process multiple documents in batch."""
        pass


class EventHandler(ABC):
    """Interface for handling system events."""
    
    @abstractmethod
    def on_processing_started(self, document: Document) -> None:
        """Handle processing start event."""
        pass
    
    @abstractmethod
    def on_processing_completed(self, result: ProcessingResult) -> None:
        """Handle processing completion event."""
        pass
    
    @abstractmethod
    def on_processing_failed(self, document: Document, error: TableQueryingError) -> None:
        """Handle processing failure event."""
        pass
    
    @abstractmethod
    def on_query_executed(self, query: Query, result: QueryResult) -> None:
        """Handle query execution event."""
        pass