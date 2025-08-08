"""
Table Database module for storing and querying table data and metadata.

Based on the existing preprocessing.py database logic, this module handles the storage
and retrieval of table data, schemas, and descriptions in a SQLite database.
"""

import sqlite3
import json
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TableDatabase:
    """Manages storage and querying of table data and metadata."""
    
    def __init__(self, db_path: str = "table_querying.db"):
        """
        Initialize the TableDatabase.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.init_database()
        logger.info(f"TableDatabase initialized with database: {db_path}")
    
    def init_database(self):
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create tables table for storing individual table data
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tables (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_id TEXT NOT NULL,
                    source_file TEXT NOT NULL,
                    table_type TEXT DEFAULT 'html',
                    rows INTEGER,
                    columns INTEGER,
                    column_names TEXT,
                    column_types TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    html_content TEXT,
                    schema_data TEXT,
                    description TEXT,
                    processing_session TEXT
                )
            ''')
            
            # Create table_data table for storing actual table rows
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS table_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_id TEXT NOT NULL,
                    row_index INTEGER NOT NULL,
                    row_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (table_id) REFERENCES tables (table_id)
                )
            ''')
            
            # Create processing_sessions table for tracking sessions
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processing_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    source_file TEXT NOT NULL,
                    total_tables INTEGER DEFAULT 0,
                    successful_tables INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            ''')
            
            # Create indexes for better query performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_table_id ON tables (table_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_source_file ON tables (source_file)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_id ON processing_sessions (session_id)')
            
            conn.commit()
        
        logger.info("Database tables initialized successfully")
    
    def start_processing_session(self, source_file: str) -> str:
        """
        Start a new processing session for a document.
        
        Args:
            source_file: Path to the source document
            
        Returns:
            Session ID
        """
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(source_file) % 10000}"
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO processing_sessions (session_id, source_file, metadata)
                VALUES (?, ?, ?)
            ''', (session_id, source_file, json.dumps({"started_at": datetime.now().isoformat()})))
            conn.commit()
        
        logger.info(f"Started processing session {session_id} for {source_file}")
        return session_id
    
    def store_table_data(self, table_id: str, schema: Dict[str, Any], description: str, 
                        session_id: str, source_file: str, html_content: str = "") -> bool:
        """
        Store table data, schema, and description in the database.
        
        Args:
            table_id: Unique identifier for the table
            schema: Schema dictionary from SchemaProcessor
            description: LLM-generated description
            session_id: Processing session ID
            source_file: Source document path
            html_content: Original HTML table content
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not schema.get("success", False):
                logger.warning(f"Cannot store table {table_id}: schema extraction failed")
                return False
            
            rows, cols = schema.get('original_shape', (0, 0))
            columns = schema.get('columns', [])
            dtypes = schema.get('dtypes', {})
            df = schema.get('dataframe')
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Store table metadata
                # Remove dataframe from schema for JSON serialization
                schema_for_storage = schema.copy()
                if 'dataframe' in schema_for_storage:
                    del schema_for_storage['dataframe']
                
                cursor.execute('''
                    INSERT INTO tables (
                        table_id, source_file, table_type, rows, columns,
                        column_names, column_types, html_content, schema_data,
                        description, processing_session
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    table_id, source_file, 'html', rows, cols,
                    json.dumps(columns), json.dumps(dtypes), html_content,
                    json.dumps(schema_for_storage), description, session_id
                ))
                
                # Store table row data if DataFrame is available
                if df is not None:
                    for idx, row in df.iterrows():
                        row_data = row.to_dict()
                        cursor.execute('''
                            INSERT INTO table_data (table_id, row_index, row_data)
                            VALUES (?, ?, ?)
                        ''', (table_id, int(idx), json.dumps(row_data)))
                
                conn.commit()
            
            logger.info(f"Successfully stored table {table_id} with {rows} rows and {cols} columns")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store table {table_id}: {e}")
            return False
    
    def store_multiple_tables(self, schemas: List[Dict[str, Any]], descriptions: List[Dict[str, Any]], 
                            session_id: str, source_file: str, html_tables: List[str] = None) -> int:
        """
        Store multiple tables from a processing session.
        
        Args:
            schemas: List of schema dictionaries
            descriptions: List of description dictionaries
            session_id: Processing session ID
            source_file: Source document path
            html_tables: Optional list of HTML table content
            
        Returns:
            Number of successfully stored tables
        """
        stored_count = 0
        html_tables = html_tables or []
        
        for i, (schema, desc_dict) in enumerate(zip(schemas, descriptions)):
            table_id = f"{Path(source_file).stem}_table_{schema.get('table_id', i+1)}"
            description = desc_dict.get('description', 'No description available')
            html_content = html_tables[i] if i < len(html_tables) else ""
            
            if self.store_table_data(table_id, schema, description, session_id, source_file, html_content):
                stored_count += 1
        
        # Update session statistics
        self.update_session_stats(session_id, len(schemas), stored_count)
        
        logger.info(f"Stored {stored_count}/{len(schemas)} tables for session {session_id}")
        return stored_count
    
    def update_session_stats(self, session_id: str, total_tables: int, successful_tables: int):
        """Update processing session statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE processing_sessions 
                SET total_tables = ?, successful_tables = ?
                WHERE session_id = ?
            ''', (total_tables, successful_tables, session_id))
            conn.commit()
    
    def query_tables_by_source(self, source_file: str) -> List[Dict[str, Any]]:
        """
        Query all tables from a specific source file.
        
        Args:
            source_file: Source document path
            
        Returns:
            List of table metadata dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT table_id, rows, columns, column_names, column_types, 
                       description, created_at
                FROM tables 
                WHERE source_file = ?
                ORDER BY created_at
            ''', (source_file,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'table_id': row[0],
                    'rows': row[1],
                    'columns': row[2],
                    'column_names': json.loads(row[3]) if row[3] else [],
                    'column_types': json.loads(row[4]) if row[4] else {},
                    'description': row[5],
                    'created_at': row[6]
                })
            
            return results
    
    def query_table_data(self, table_id: str) -> Optional[pd.DataFrame]:
        """
        Query the actual data for a specific table.
        
        Args:
            table_id: Table identifier
            
        Returns:
            DataFrame with table data or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT row_index, row_data
                FROM table_data
                WHERE table_id = ?
                ORDER BY row_index
            ''', (table_id,))
            
            rows = cursor.fetchall()
            if not rows:
                return None
            
            # Reconstruct DataFrame from stored row data
            data = []
            for _, row_data_json in rows:
                row_data = json.loads(row_data_json)
                data.append(row_data)
            
            return pd.DataFrame(data)
    
    def get_database_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the database contents.
        
        Returns:
            Dictionary with database statistics
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Count tables
            cursor.execute('SELECT COUNT(*) FROM tables')
            total_tables = cursor.fetchone()[0]
            
            # Count by type
            cursor.execute('SELECT table_type, COUNT(*) FROM tables GROUP BY table_type')
            tables_by_type = dict(cursor.fetchall())
            
            # Count unique sources
            cursor.execute('SELECT COUNT(DISTINCT source_file) FROM tables')
            unique_sources = cursor.fetchone()[0]
            
            # Get recent sessions
            cursor.execute('''
                SELECT session_id, source_file, total_tables, successful_tables, created_at
                FROM processing_sessions
                ORDER BY created_at DESC
                LIMIT 5
            ''')
            recent_sessions = [
                {
                    'session_id': row[0],
                    'source_file': row[1], 
                    'total_tables': row[2],
                    'successful_tables': row[3],
                    'created_at': row[4]
                }
                for row in cursor.fetchall()
            ]
            
            return {
                'total_tables': total_tables,
                'tables_by_type': tables_by_type,
                'unique_sources': unique_sources,
                'recent_sessions': recent_sessions
            }
    
    def clear_database(self):
        """Clear all data from the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM table_data')
            cursor.execute('DELETE FROM tables')
            cursor.execute('DELETE FROM processing_sessions')
            conn.commit()
        
        logger.info("Database cleared successfully")