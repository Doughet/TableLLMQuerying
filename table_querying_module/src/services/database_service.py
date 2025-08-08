"""
Abstract Database Service Interface.

This module defines the interface for database services, making it easy to 
plug in different database providers (SQLite, PostgreSQL, MongoDB, etc.).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Union
from datetime import datetime


@dataclass
class TableMetadata:
    """Standard metadata format for stored tables."""
    table_id: str
    source_file: str
    rows: int
    columns: int
    column_names: List[str]
    column_types: Dict[str, str]
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'table_id': self.table_id,
            'source_file': self.source_file,
            'rows': self.rows,
            'columns': self.columns,
            'column_names': self.column_names,
            'column_types': self.column_types,
            'description': self.description,
            'created_at': self.created_at
        }


@dataclass
class QueryResult:
    """Standard result format for database queries."""
    success: bool
    data: List[Dict[str, Any]]
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class DatabaseService(ABC):
    """Abstract base class for database services."""
    
    def __init__(self, **config):
        """
        Initialize the database service.
        
        Args:
            **config: Service-specific configuration parameters
        """
        self.config = config
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the database and create necessary schemas.
        
        Returns:
            True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the database service is available and properly configured.
        
        Returns:
            True if service is ready to use, False otherwise
        """
        pass
    
    # Table Management
    
    @abstractmethod
    def store_table(self, table_data: Dict[str, Any], session_id: str) -> bool:
        """
        Store a single table with its metadata and row data.
        
        Args:
            table_data: Dictionary containing table metadata and row data
            session_id: Session identifier for tracking
            
        Returns:
            True if storage successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_table_metadata(self, table_id: str) -> Optional[TableMetadata]:
        """
        Retrieve metadata for a specific table.
        
        Args:
            table_id: Unique identifier for the table
            
        Returns:
            TableMetadata object or None if not found
        """
        pass
    
    @abstractmethod
    def get_tables_by_source(self, source_file: str) -> List[TableMetadata]:
        """
        Retrieve all tables from a specific source file.
        
        Args:
            source_file: Source file path
            
        Returns:
            List of TableMetadata objects
        """
        pass
    
    @abstractmethod
    def get_all_tables(self) -> List[TableMetadata]:
        """
        Retrieve metadata for all stored tables.
        
        Returns:
            List of TableMetadata objects
        """
        pass
    
    @abstractmethod
    def table_exists(self, table_id: str) -> bool:
        """
        Check if a table exists in the database.
        
        Args:
            table_id: Unique identifier for the table
            
        Returns:
            True if table exists, False otherwise
        """
        pass
    
    # Data Querying
    
    @abstractmethod
    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> QueryResult:
        """
        Execute a raw query against the database.
        
        Args:
            query: SQL or query string
            parameters: Optional query parameters
            
        Returns:
            QueryResult with query results
        """
        pass
    
    @abstractmethod
    def get_table_data(self, table_id: str, limit: Optional[int] = None, offset: Optional[int] = None) -> QueryResult:
        """
        Retrieve row data for a specific table.
        
        Args:
            table_id: Unique identifier for the table
            limit: Maximum number of rows to return
            offset: Number of rows to skip
            
        Returns:
            QueryResult with table row data
        """
        pass
    
    @abstractmethod
    def search_tables(self, search_term: str, search_fields: Optional[List[str]] = None) -> List[TableMetadata]:
        """
        Search for tables based on metadata fields.
        
        Args:
            search_term: Term to search for
            search_fields: Fields to search in (default: all text fields)
            
        Returns:
            List of matching TableMetadata objects
        """
        pass
    
    # Session Management
    
    @abstractmethod
    def create_session(self, source_file: str) -> str:
        """
        Create a new processing session.
        
        Args:
            source_file: Source file being processed
            
        Returns:
            Unique session identifier
        """
        pass
    
    @abstractmethod
    def update_session(self, session_id: str, total_tables: int, successful_tables: int) -> bool:
        """
        Update session statistics.
        
        Args:
            session_id: Session identifier
            total_tables: Total number of tables processed
            successful_tables: Number of successfully processed tables
            
        Returns:
            True if update successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session information.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with session information or None if not found
        """
        pass
    
    # Database Management
    
    @abstractmethod
    def get_database_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics about the database.
        
        Returns:
            Dictionary with database statistics
        """
        pass
    
    @abstractmethod
    def clear_database(self) -> bool:
        """
        Clear all data from the database.
        
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def backup_database(self, backup_path: str) -> bool:
        """
        Create a backup of the database.
        
        Args:
            backup_path: Path where to store the backup
            
        Returns:
            True if backup successful, False otherwise
        """
        pass
    
    @abstractmethod
    def restore_database(self, backup_path: str) -> bool:
        """
        Restore database from a backup.
        
        Args:
            backup_path: Path to the backup file
            
        Returns:
            True if restore successful, False otherwise
        """
        pass
    
    # Utility Methods
    
    def get_database_schema(self) -> Dict[str, Any]:
        """
        Get database schema information for LLM context.
        This is a convenience method that can be overridden.
        
        Returns:
            Dictionary with schema information
        """
        tables = self.get_all_tables()
        return {
            'tables': [table.to_dict() for table in tables],
            'total_tables': len(tables),
            'summary': self.get_database_summary()
        }
    
    def validate_table_data(self, table_data: Dict[str, Any]) -> bool:
        """
        Validate table data format before storage.
        
        Args:
            table_data: Table data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        required_fields = ['table_id', 'source_file', 'rows', 'columns', 'column_names', 'row_data']
        return all(field in table_data for field in required_fields)