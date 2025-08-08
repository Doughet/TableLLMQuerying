"""
Chat Interface for interacting with table data through natural language queries.

This module provides the main interface that combines query analysis and SQL generation
to answer user questions about processed table data.
"""

import logging
import sqlite3
import json
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

from query_analyzer import QueryAnalyzer, AnalysisResult
from sql_generator import SQLGenerator

logger = logging.getLogger(__name__)


class ChatInterface:
    """Main interface for chatting with table data using natural language queries."""
    
    def __init__(self, db_path: str, api_key: str, model_id: str = "mistral-small"):
        """
        Initialize the ChatInterface.
        
        Args:
            db_path: Path to the SQLite database with table data
            api_key: BHub API key for LLM calls
            model_id: Model to use for analysis and SQL generation
        """
        self.db_path = db_path
        self.api_key = api_key
        self.model_id = model_id
        
        # Initialize components
        self.query_analyzer = QueryAnalyzer(api_key, model_id)
        self.sql_generator = SQLGenerator(api_key, model_id)
        
        # Verify database exists
        if not Path(db_path).exists():
            raise FileNotFoundError(f"Database not found: {db_path}")
        
        logger.info(f"ChatInterface initialized with database: {db_path}")
    
    def chat(self, user_query: str) -> Union[str, str]:
        """
        Process a user query and return either SQL query or "IMPOSSIBLE".
        
        This is the main entry point that:
        1. Analyzes if the query is fulfillable
        2. If yes, generates SQL query with retry logic (up to 5 attempts)
        3. Returns the SQL query or "IMPOSSIBLE"
        
        Args:
            user_query: The user's question/request
            
        Returns:
            Either the SQL query string or "IMPOSSIBLE"
        """
        logger.info(f"Processing user query: {user_query}")
        
        try:
            # Step 1: Get database schema and available tables
            database_info = self._get_database_info()
            
            if not database_info['tables']:
                logger.warning("No tables found in database")
                return "IMPOSSIBLE"
            
            # Step 2: Analyze if query is fulfillable
            analysis = self.query_analyzer.analyze_query(user_query, database_info['tables'])
            
            if not analysis.is_fulfillable:
                logger.info(f"Query determined to be not fulfillable: {analysis.reasoning}")
                return "IMPOSSIBLE"
            
            logger.info(f"Query is fulfillable (confidence: {analysis.confidence:.2f})")
            
            # Step 3: Generate SQL query with retry logic
            sql_result = self.sql_generator.generate_sql(
                user_query, 
                database_info,
                self.db_path
            )
            
            return sql_result
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return "IMPOSSIBLE"
    
    def _get_database_info(self) -> Dict[str, Any]:
        """Get information about the database schema and available tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row  # Enable column access by name
                cursor = conn.cursor()
                
                # Get all tables with their metadata
                cursor.execute("""
                    SELECT table_id, source_file, rows, columns, 
                           column_names, column_types, description
                    FROM tables 
                    ORDER BY created_at DESC
                """)
                
                tables = []
                for row in cursor.fetchall():
                    tables.append(dict(row))
                
                # Get count of table_data entries for each table
                cursor.execute("""
                    SELECT table_id, COUNT(*) as row_count 
                    FROM table_data 
                    GROUP BY table_id
                """)
                
                row_counts = dict(cursor.fetchall())
                
                # Add actual row counts to table info
                for table in tables:
                    table['actual_rows'] = row_counts.get(table['table_id'], 0)
                
                return {
                    'tables': tables,
                    'total_tables': len(tables),
                    'database_path': self.db_path
                }
                
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return {'tables': [], 'total_tables': 0, 'database_path': self.db_path}
    
    def execute_sql_query(self, sql_query: str) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return results.
        
        Note: This method is for testing/debugging purposes.
        The main chat() method only returns the SQL query.
        
        Args:
            sql_query: SQL query to execute
            
        Returns:
            Query results as list of dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute(sql_query)
                results = [dict(row) for row in cursor.fetchall()]
                
                logger.info(f"Query executed successfully, returned {len(results)} rows")
                return results
                
        except sqlite3.Error as e:
            logger.error(f"Error executing SQL query: {e}")
            logger.debug(f"Failed query: {sql_query}")
            return []
    
    def get_database_summary(self) -> Dict[str, Any]:
        """Get a summary of the current database contents."""
        info = self._get_database_info()
        
        summary = {
            'total_tables': info['total_tables'],
            'database_path': info['database_path']
        }
        
        if info['tables']:
            # Add statistics
            total_rows = sum(table.get('actual_rows', 0) for table in info['tables'])
            source_files = set(table.get('source_file', '') for table in info['tables'])
            
            summary.update({
                'total_data_rows': total_rows,
                'unique_source_files': len(source_files),
                'source_files': list(source_files),
                'sample_tables': [
                    {
                        'table_id': table['table_id'],
                        'source_file': table['source_file'],
                        'rows': table.get('actual_rows', 0),
                        'columns': table.get('columns', 0),
                        'description': (table.get('description', '')[:100] + '...' 
                                      if table.get('description', '') and len(table.get('description', '')) > 100
                                      else table.get('description', ''))
                    }
                    for table in info['tables'][:3]  # First 3 tables as samples
                ]
            })
        
        return summary
    
    def list_available_tables(self) -> List[Dict[str, Any]]:
        """List all available tables with their basic information."""
        info = self._get_database_info()
        return info['tables']