"""
Example: Creating a Custom Database Service

This example shows how to create a custom database service that can be plugged
into the table querying system. This example implements a PostgreSQL service.
"""

import logging
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from src.services.database_service import DatabaseService, TableMetadata, QueryResult

logger = logging.getLogger(__name__)


class PostgreSQLDatabaseService(DatabaseService):
    """
    Custom database service for PostgreSQL.
    
    This demonstrates how to implement the DatabaseService interface
    for a custom database provider.
    
    Note: This example requires psycopg2 or psycopg2-binary:
    pip install psycopg2-binary
    """
    
    def __init__(self, host: str = "localhost", port: int = 5432, database: str = "tables", 
                 username: str = "postgres", password: str = "", **kwargs):
        """
        Initialize PostgreSQL database service.
        
        Args:
            host: PostgreSQL server host
            port: PostgreSQL server port
            database: Database name
            username: Database username
            password: Database password
            **kwargs: Additional configuration
        """
        super().__init__(
            host=host, port=port, database=database, 
            username=username, password=password, **kwargs
        )
        
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.timeout = kwargs.get('timeout', 30.0)
        self.auto_commit = kwargs.get('auto_commit', True)
        
        # Connection pool settings
        self.min_connections = kwargs.get('min_connections', 1)
        self.max_connections = kwargs.get('max_connections', 10)
        
        logger.info(f"PostgreSQLDatabaseService initialized for {host}:{port}/{database}")
    
    def _get_connection(self):
        """Get database connection. In real implementation, use connection pooling."""
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.username,
                password=self.password,
                connect_timeout=int(self.timeout)
            )
            
            if self.auto_commit:
                conn.autocommit = True
            
            return conn
        except ImportError:
            raise RuntimeError("psycopg2 is required for PostgreSQL service. Install with: pip install psycopg2-binary")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    def initialize(self) -> bool:
        """Initialize PostgreSQL database with required schema."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                
                # Create tables table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tables (
                        id SERIAL PRIMARY KEY,
                        table_id VARCHAR(255) UNIQUE NOT NULL,
                        source_file VARCHAR(500) NOT NULL,
                        rows INTEGER NOT NULL,
                        columns INTEGER NOT NULL,
                        column_names JSONB NOT NULL,
                        column_types JSONB NOT NULL,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create table_data table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS table_data (
                        id SERIAL PRIMARY KEY,
                        table_id VARCHAR(255) NOT NULL,
                        row_index INTEGER NOT NULL,
                        row_data JSONB NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (table_id) REFERENCES tables (table_id) ON DELETE CASCADE
                    )
                """)
                
                # Create processing_sessions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS processing_sessions (
                        id SERIAL PRIMARY KEY,
                        session_id VARCHAR(255) UNIQUE NOT NULL,
                        source_file VARCHAR(500) NOT NULL,
                        total_tables INTEGER DEFAULT 0,
                        successful_tables INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_tables_source_file ON tables(source_file)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_table_data_table_id ON table_data(table_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_source_file ON processing_sessions(source_file)")
                
                if not self.auto_commit:
                    conn.commit()
                
                logger.info("PostgreSQL database initialized successfully")
                return True
                
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL database: {e}")
            return False
        finally:
            if 'conn' in locals():
                conn.close()
    
    def is_available(self) -> bool:
        """Check if PostgreSQL database is available."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except Exception:
            return False
        finally:
            if 'conn' in locals():
                conn.close()
    
    def store_table(self, table_data: Dict[str, Any], session_id: str) -> bool:
        """Store a table with metadata and row data."""
        if not self.validate_table_data(table_data):
            logger.error("Invalid table data format")
            return False
        
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                
                # Insert table metadata
                cursor.execute("""
                    INSERT INTO tables 
                    (table_id, source_file, rows, columns, column_names, column_types, description)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (table_id) DO UPDATE SET
                        source_file = EXCLUDED.source_file,
                        rows = EXCLUDED.rows,
                        columns = EXCLUDED.columns,
                        column_names = EXCLUDED.column_names,
                        column_types = EXCLUDED.column_types,
                        description = EXCLUDED.description
                """, (
                    table_data['table_id'],
                    table_data['source_file'],
                    table_data['rows'],
                    table_data['columns'],
                    json.dumps(table_data['column_names']),
                    json.dumps(table_data['column_types']),
                    table_data.get('description', '')
                ))
                
                # Delete existing row data for this table
                cursor.execute("DELETE FROM table_data WHERE table_id = %s", (table_data['table_id'],))
                
                # Insert row data
                for row_index, row in enumerate(table_data['row_data']):
                    cursor.execute("""
                        INSERT INTO table_data (table_id, row_index, row_data)
                        VALUES (%s, %s, %s)
                    """, (
                        table_data['table_id'],
                        row_index,
                        json.dumps(row)
                    ))
                
                if not self.auto_commit:
                    conn.commit()
                
                logger.info(f"Successfully stored table {table_data['table_id']}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to store table {table_data.get('table_id', 'unknown')}: {e}")
            return False
        finally:
            if 'conn' in locals():
                conn.close()
    
    def get_table_metadata(self, table_id: str) -> Optional[TableMetadata]:
        """Retrieve metadata for a specific table."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT table_id, source_file, rows, columns, column_names, column_types, description, created_at
                    FROM tables WHERE table_id = %s
                """, (table_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                return TableMetadata(
                    table_id=row[0],
                    source_file=row[1],
                    rows=row[2],
                    columns=row[3],
                    column_names=row[4] if isinstance(row[4], list) else json.loads(row[4]),
                    column_types=row[5] if isinstance(row[5], dict) else json.loads(row[5]),
                    description=row[6],
                    created_at=row[7]
                )
                
        except Exception as e:
            logger.error(f"Failed to get metadata for table {table_id}: {e}")
            return None
        finally:
            if 'conn' in locals():
                conn.close()
    
    def get_all_tables(self) -> List[TableMetadata]:
        """Retrieve metadata for all stored tables."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT table_id, source_file, rows, columns, column_names, column_types, description, created_at
                    FROM tables ORDER BY created_at DESC
                """)
                
                tables = []
                for row in cursor.fetchall():
                    try:
                        tables.append(TableMetadata(
                            table_id=row[0],
                            source_file=row[1],
                            rows=row[2],
                            columns=row[3],
                            column_names=row[4] if isinstance(row[4], list) else json.loads(row[4]),
                            column_types=row[5] if isinstance(row[5], dict) else json.loads(row[5]),
                            description=row[6],
                            created_at=row[7]
                        ))
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.warning(f"Skipping table {row[0]} due to data error: {e}")
                        continue
                
                return tables
                
        except Exception as e:
            logger.error(f"Failed to get all tables: {e}")
            return []
        finally:
            if 'conn' in locals():
                conn.close()
    
    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> QueryResult:
        """Execute a raw SQL query."""
        try:
            from psycopg2.extras import RealDictCursor
            
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                
                # Convert parameters to tuple if provided
                params = tuple(parameters.values()) if parameters else None
                
                cursor.execute(query, params)
                
                # Handle different query types
                if query.strip().upper().startswith('SELECT'):
                    rows = cursor.fetchall()
                    
                    # Convert to list of dictionaries
                    data = [dict(row) for row in rows]
                    
                    return QueryResult(
                        success=True,
                        data=data,
                        metadata={"rows_returned": len(data)}
                    )
                else:
                    # For non-SELECT queries
                    if not self.auto_commit:
                        conn.commit()
                    
                    return QueryResult(
                        success=True,
                        data=[],
                        metadata={"rows_affected": cursor.rowcount}
                    )
                    
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return QueryResult(
                success=False,
                data=[],
                error=str(e)
            )
        finally:
            if 'conn' in locals():
                conn.close()
    
    # Implement other required methods...
    # (For brevity, showing key methods. In real implementation, implement all abstract methods)
    
    def table_exists(self, table_id: str) -> bool:
        """Check if a table exists in the database."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 FROM tables WHERE table_id = %s", (table_id,))
                return cursor.fetchone() is not None
        except Exception:
            return False
        finally:
            if 'conn' in locals():
                conn.close()
    
    def get_database_summary(self) -> Dict[str, Any]:
        """Get summary statistics about the database."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                
                # Get table counts
                cursor.execute("SELECT COUNT(*) FROM tables")
                total_tables = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM table_data")
                total_rows = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM processing_sessions")
                total_sessions = cursor.fetchone()[0]
                
                # Get source file info
                cursor.execute("SELECT COUNT(DISTINCT source_file) FROM tables")
                unique_sources = cursor.fetchone()[0]
                
                return {
                    'total_tables': total_tables,
                    'total_rows': total_rows,
                    'total_sessions': total_sessions,
                    'unique_source_files': unique_sources,
                    'database_host': f"{self.host}:{self.port}",
                    'database_name': self.database
                }
                
        except Exception as e:
            logger.error(f"Failed to get database summary: {e}")
            return {}
        finally:
            if 'conn' in locals():
                conn.close()
    
    def clear_database(self) -> bool:
        """Clear all data from the database."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                
                cursor.execute("DELETE FROM table_data")
                cursor.execute("DELETE FROM tables")
                cursor.execute("DELETE FROM processing_sessions")
                
                if not self.auto_commit:
                    conn.commit()
                
                logger.info("Database cleared successfully")
                return True
                
        except Exception as e:
            logger.error(f"Failed to clear database: {e}")
            return False
        finally:
            if 'conn' in locals():
                conn.close()
    
    # Implement remaining abstract methods for completeness...
    def get_tables_by_source(self, source_file: str) -> List[TableMetadata]:
        # Implementation similar to get_all_tables but with WHERE clause
        pass
    
    def get_table_data(self, table_id: str, limit: Optional[int] = None, offset: Optional[int] = None) -> QueryResult:
        # Implementation for retrieving table row data
        pass
    
    def search_tables(self, search_term: str, search_fields: Optional[List[str]] = None) -> List[TableMetadata]:
        # Implementation for searching tables
        pass
    
    def create_session(self, source_file: str) -> str:
        # Implementation for creating processing sessions
        pass
    
    def update_session(self, session_id: str, total_tables: int, successful_tables: int) -> bool:
        # Implementation for updating session stats
        pass
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        # Implementation for retrieving session info
        pass
    
    def backup_database(self, backup_path: str) -> bool:
        # Implementation for database backup (using pg_dump)
        pass
    
    def restore_database(self, backup_path: str) -> bool:
        # Implementation for database restore (using psql)
        pass


def example_usage():
    """Example of how to use the custom PostgreSQL service."""
    
    # Import the service factory
    from src.services.service_factory import ServiceFactory, ServiceConfig
    
    # Register the custom service
    ServiceFactory.register_database_service("postgresql", PostgreSQLDatabaseService)
    
    # Create configuration for the custom service
    config = ServiceConfig(
        llm_service_type="bhub",
        llm_api_key="your-api-key",
        db_service_type="postgresql",
        db_extra_config={
            "host": "localhost",
            "port": 5432,
            "database": "tables",
            "username": "postgres",
            "password": "your-password"
        }
    )
    
    # Create services
    try:
        llm_service, db_service = ServiceFactory.create_services(config)
        
        # Test the database service
        if db_service.is_available():
            print("PostgreSQL database service is available!")
            summary = db_service.get_database_summary()
            print(f"Database summary: {summary}")
        else:
            print("PostgreSQL database service is not available.")
        
        # The services can now be used with the table processing system
        print("Custom PostgreSQL database service is ready to use!")
        
    except Exception as e:
        print(f"Error creating services: {e}")


if __name__ == "__main__":
    # Run the example
    example_usage()