"""
SQLite Database Service Implementation.

This module provides a concrete implementation of the database service interface
for SQLite databases.
"""

import logging
import sqlite3
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from ..database_service import DatabaseService, TableMetadata, QueryResult

logger = logging.getLogger(__name__)


class SQLiteDatabaseService(DatabaseService):
    """SQLite implementation of the database service."""
    
    def __init__(self, db_path: str, **kwargs):
        """
        Initialize SQLite database service.
        
        Args:
            db_path: Path to SQLite database file
            **kwargs: Additional configuration
        """
        super().__init__(db_path=db_path, **kwargs)
        self.db_path = db_path
        self.auto_commit = kwargs.get('auto_commit', True)
        self.timeout = kwargs.get('timeout', 30.0)
        
        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"SQLiteDatabaseService initialized with database: {db_path}")
    
    def initialize(self) -> bool:
        """Initialize SQLite database with required schema."""
        try:
            with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
                cursor = conn.cursor()
                
                # Create tables table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tables (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        table_id TEXT UNIQUE NOT NULL,
                        source_file TEXT NOT NULL,
                        rows INTEGER NOT NULL,
                        columns INTEGER NOT NULL,
                        column_names TEXT NOT NULL,
                        column_types TEXT NOT NULL,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create table_data table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS table_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        table_id TEXT NOT NULL,
                        row_index INTEGER NOT NULL,
                        row_data TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (table_id) REFERENCES tables (table_id)
                    )
                """)
                
                # Create processing_sessions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS processing_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT UNIQUE NOT NULL,
                        source_file TEXT NOT NULL,
                        total_tables INTEGER DEFAULT 0,
                        successful_tables INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_tables_source_file ON tables(source_file)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_table_data_table_id ON table_data(table_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_source_file ON processing_sessions(source_file)")
                
                if self.auto_commit:
                    conn.commit()
                
                logger.info("SQLite database initialized successfully")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize SQLite database: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if SQLite database is available."""
        try:
            with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return True
        except Exception:
            return False
    
    def store_table(self, table_data: Dict[str, Any], session_id: str) -> bool:
        """Store a table with metadata and row data."""
        if not self.validate_table_data(table_data):
            logger.error("Invalid table data format")
            return False
        
        try:
            with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
                cursor = conn.cursor()
                
                # Insert table metadata
                cursor.execute("""
                    INSERT OR REPLACE INTO tables 
                    (table_id, source_file, rows, columns, column_names, column_types, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    table_data['table_id'],
                    table_data['source_file'],
                    table_data['rows'],
                    table_data['columns'],
                    json.dumps(table_data['column_names']),
                    json.dumps(table_data['column_types']),
                    table_data.get('description', '')
                ))
                
                # Delete existing row data for this table (in case of update)
                cursor.execute("DELETE FROM table_data WHERE table_id = ?", (table_data['table_id'],))
                
                # Insert row data
                for row_index, row in enumerate(table_data['row_data']):
                    cursor.execute("""
                        INSERT INTO table_data (table_id, row_index, row_data)
                        VALUES (?, ?, ?)
                    """, (
                        table_data['table_id'],
                        row_index,
                        json.dumps(row)
                    ))
                
                if self.auto_commit:
                    conn.commit()
                
                logger.info(f"Successfully stored table {table_data['table_id']}")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Failed to store table {table_data.get('table_id', 'unknown')}: {e}")
            return False
    
    def get_table_metadata(self, table_id: str) -> Optional[TableMetadata]:
        """Retrieve metadata for a specific table."""
        try:
            with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT table_id, source_file, rows, columns, column_names, column_types, description, created_at
                    FROM tables WHERE table_id = ?
                """, (table_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                return TableMetadata(
                    table_id=row[0],
                    source_file=row[1],
                    rows=row[2],
                    columns=row[3],
                    column_names=json.loads(row[4]),
                    column_types=json.loads(row[5]),
                    description=row[6],
                    created_at=datetime.fromisoformat(row[7]) if row[7] else None
                )
                
        except (sqlite3.Error, json.JSONDecodeError) as e:
            logger.error(f"Failed to get metadata for table {table_id}: {e}")
            return None
    
    def get_tables_by_source(self, source_file: str) -> List[TableMetadata]:
        """Retrieve all tables from a specific source file."""
        try:
            with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT table_id, source_file, rows, columns, column_names, column_types, description, created_at
                    FROM tables WHERE source_file = ?
                """, (source_file,))
                
                tables = []
                for row in cursor.fetchall():
                    try:
                        tables.append(TableMetadata(
                            table_id=row[0],
                            source_file=row[1],
                            rows=row[2],
                            columns=row[3],
                            column_names=json.loads(row[4]),
                            column_types=json.loads(row[5]),
                            description=row[6],
                            created_at=datetime.fromisoformat(row[7]) if row[7] else None
                        ))
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.warning(f"Skipping table {row[0]} due to data error: {e}")
                        continue
                
                return tables
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get tables for source {source_file}: {e}")
            return []
    
    def get_all_tables(self) -> List[TableMetadata]:
        """Retrieve metadata for all stored tables."""
        try:
            with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
                cursor = conn.cursor()
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
                            column_names=json.loads(row[4]),
                            column_types=json.loads(row[5]),
                            description=row[6],
                            created_at=datetime.fromisoformat(row[7]) if row[7] else None
                        ))
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.warning(f"Skipping table {row[0]} due to data error: {e}")
                        continue
                
                return tables
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get all tables: {e}")
            return []
    
    def table_exists(self, table_id: str) -> bool:
        """Check if a table exists in the database."""
        try:
            with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM tables WHERE table_id = ?", (table_id,))
                return cursor.fetchone() is not None
        except sqlite3.Error:
            return False
    
    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> QueryResult:
        """Execute a raw SQL query."""
        try:
            with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
                cursor = conn.cursor()
                
                # Convert parameters to tuple if provided
                params = tuple(parameters.values()) if parameters else ()
                
                cursor.execute(query, params)
                
                # Handle different query types
                if query.strip().upper().startswith('SELECT'):
                    columns = [desc[0] for desc in cursor.description] if cursor.description else []
                    rows = cursor.fetchall()
                    
                    # Convert to list of dictionaries
                    data = []
                    for row in rows:
                        row_dict = {}
                        for i, value in enumerate(row):
                            column_name = columns[i] if i < len(columns) else f"column_{i}"
                            row_dict[column_name] = value
                        data.append(row_dict)
                    
                    return QueryResult(
                        success=True,
                        data=data,
                        metadata={"rows_returned": len(data), "columns": columns}
                    )
                else:
                    # For non-SELECT queries
                    if self.auto_commit:
                        conn.commit()
                    
                    return QueryResult(
                        success=True,
                        data=[],
                        metadata={"rows_affected": cursor.rowcount}
                    )
                    
        except sqlite3.Error as e:
            logger.error(f"Query execution failed: {e}")
            return QueryResult(
                success=False,
                data=[],
                error=str(e)
            )
    
    def get_table_data(self, table_id: str, limit: Optional[int] = None, offset: Optional[int] = None) -> QueryResult:
        """Retrieve row data for a specific table."""
        try:
            query = "SELECT row_index, row_data FROM table_data WHERE table_id = ? ORDER BY row_index"
            params = [table_id]
            
            if limit is not None:
                query += " LIMIT ?"
                params.append(limit)
                
            if offset is not None:
                query += " OFFSET ?"
                params.append(offset)
            
            with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                data = []
                for row in cursor.fetchall():
                    try:
                        row_data = json.loads(row[1])
                        row_data['_row_index'] = row[0]  # Add row index
                        data.append(row_data)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Skipping row {row[0]} due to JSON decode error: {e}")
                        continue
                
                return QueryResult(
                    success=True,
                    data=data,
                    metadata={"table_id": table_id, "rows_returned": len(data)}
                )
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get data for table {table_id}: {e}")
            return QueryResult(
                success=False,
                data=[],
                error=str(e)
            )
    
    def search_tables(self, search_term: str, search_fields: Optional[List[str]] = None) -> List[TableMetadata]:
        """Search for tables based on metadata fields."""
        if search_fields is None:
            search_fields = ['table_id', 'source_file', 'description']
        
        try:
            # Build search query
            conditions = []
            params = []
            
            for field in search_fields:
                if field in ['table_id', 'source_file', 'description']:
                    conditions.append(f"{field} LIKE ?")
                    params.append(f"%{search_term}%")
            
            if not conditions:
                return []
            
            query = f"""
                SELECT table_id, source_file, rows, columns, column_names, column_types, description, created_at
                FROM tables WHERE {' OR '.join(conditions)}
                ORDER BY created_at DESC
            """
            
            with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                tables = []
                for row in cursor.fetchall():
                    try:
                        tables.append(TableMetadata(
                            table_id=row[0],
                            source_file=row[1],
                            rows=row[2],
                            columns=row[3],
                            column_names=json.loads(row[4]),
                            column_types=json.loads(row[5]),
                            description=row[6],
                            created_at=datetime.fromisoformat(row[7]) if row[7] else None
                        ))
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.warning(f"Skipping table {row[0]} due to data error: {e}")
                        continue
                
                return tables
                
        except sqlite3.Error as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def create_session(self, source_file: str) -> str:
        """Create a new processing session."""
        session_id = str(uuid.uuid4())
        
        try:
            with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO processing_sessions (session_id, source_file)
                    VALUES (?, ?)
                """, (session_id, source_file))
                
                if self.auto_commit:
                    conn.commit()
                
                logger.info(f"Created session {session_id} for {source_file}")
                return session_id
                
        except sqlite3.Error as e:
            logger.error(f"Failed to create session: {e}")
            return ""
    
    def update_session(self, session_id: str, total_tables: int, successful_tables: int) -> bool:
        """Update session statistics."""
        try:
            with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE processing_sessions 
                    SET total_tables = ?, successful_tables = ?
                    WHERE session_id = ?
                """, (total_tables, successful_tables, session_id))
                
                if self.auto_commit:
                    conn.commit()
                
                return cursor.rowcount > 0
                
        except sqlite3.Error as e:
            logger.error(f"Failed to update session {session_id}: {e}")
            return False
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session information."""
        try:
            with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT session_id, source_file, total_tables, successful_tables, created_at
                    FROM processing_sessions WHERE session_id = ?
                """, (session_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                return {
                    'session_id': row[0],
                    'source_file': row[1],
                    'total_tables': row[2],
                    'successful_tables': row[3],
                    'created_at': row[4]
                }
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get session info for {session_id}: {e}")
            return None
    
    def get_database_summary(self) -> Dict[str, Any]:
        """Get summary statistics about the database."""
        try:
            with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
                cursor = conn.cursor()
                
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
                    'database_path': self.db_path
                }
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get database summary: {e}")
            return {}
    
    def clear_database(self) -> bool:
        """Clear all data from the database."""
        try:
            with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM table_data")
                cursor.execute("DELETE FROM tables")
                cursor.execute("DELETE FROM processing_sessions")
                
                if self.auto_commit:
                    conn.commit()
                
                logger.info("Database cleared successfully")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Failed to clear database: {e}")
            return False
    
    def backup_database(self, backup_path: str) -> bool:
        """Create a backup of the database."""
        try:
            # Ensure backup directory exists
            Path(backup_path).parent.mkdir(parents=True, exist_ok=True)
            
            with sqlite3.connect(self.db_path, timeout=self.timeout) as source:
                with sqlite3.connect(backup_path) as backup:
                    source.backup(backup)
            
            logger.info(f"Database backed up to {backup_path}")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Failed to backup database: {e}")
            return False
    
    def restore_database(self, backup_path: str) -> bool:
        """Restore database from a backup."""
        try:
            if not Path(backup_path).exists():
                logger.error(f"Backup file does not exist: {backup_path}")
                return False
            
            with sqlite3.connect(backup_path, timeout=self.timeout) as backup:
                with sqlite3.connect(self.db_path) as target:
                    backup.backup(target)
            
            logger.info(f"Database restored from {backup_path}")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Failed to restore database: {e}")
            return False