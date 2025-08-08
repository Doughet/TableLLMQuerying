"""
SQL Generator for creating SQL queries from user requests.

This module uses LLM to generate SQL queries based on user prompts and database schema.
It includes retry logic to handle failed attempts and validation.
"""

import logging
import requests
import json
import sqlite3
import re
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SQLResult:
    """Result of SQL generation attempt."""
    success: bool
    sql_query: Optional[str]
    error: Optional[str]
    attempt: int
    reasoning: str


class SQLGenerator:
    """Generates SQL queries from user requests with retry logic."""
    
    def __init__(self, api_key: str, model_id: str = "mistral-small", max_retries: int = 5):
        """
        Initialize the SQLGenerator.
        
        Args:
            api_key: BHub API key for LLM calls
            model_id: Model to use for SQL generation
            max_retries: Maximum number of retry attempts
        """
        self.api_key = api_key
        self.model_id = model_id
        self.max_retries = max_retries
        self.api_url = "https://api.olympia.bhub.cloud/v1/chat/completions"
        logger.info(f"SQLGenerator initialized with model {model_id}, max_retries={max_retries}")
    
    def generate_sql(self, user_query: str, database_schema: Dict[str, Any], 
                     db_path: str) -> Union[str, str]:
        """
        Generate SQL query from user request with retry logic.
        
        Args:
            user_query: The user's question/request
            database_schema: Schema information about available tables
            db_path: Path to the database for validation
            
        Returns:
            Either the SQL query string or "IMPOSSIBLE" if it cannot be generated
        """
        logger.info(f"Generating SQL for query: {user_query}")
        
        for attempt in range(1, self.max_retries + 1):
            logger.info(f"SQL generation attempt {attempt}/{self.max_retries}")
            
            try:
                result = self._attempt_sql_generation(user_query, database_schema, attempt)
                
                if result.success:
                    # Validate the SQL query
                    if self._validate_sql(result.sql_query, db_path):
                        logger.info(f"Successfully generated SQL on attempt {attempt}")
                        return result.sql_query
                    else:
                        logger.warning(f"Generated SQL failed validation on attempt {attempt}")
                        continue
                else:
                    logger.warning(f"SQL generation failed on attempt {attempt}: {result.error}")
                    continue
                    
            except Exception as e:
                logger.error(f"Error during SQL generation attempt {attempt}: {e}")
                continue
        
        logger.error(f"Failed to generate valid SQL after {self.max_retries} attempts")
        return "IMPOSSIBLE"
    
    def _attempt_sql_generation(self, user_query: str, database_schema: Dict[str, Any], 
                               attempt: int) -> SQLResult:
        """Attempt to generate SQL query."""
        
        # Create SQL generation prompt
        prompt = self._create_sql_prompt(user_query, database_schema, attempt)
        
        try:
            # Get LLM response
            response = self._call_llm(prompt)
            
            # Extract SQL from response
            sql_query = self._extract_sql(response)
            
            if sql_query:
                return SQLResult(
                    success=True,
                    sql_query=sql_query,
                    error=None,
                    attempt=attempt,
                    reasoning=f"SQL extracted successfully from LLM response"
                )
            else:
                return SQLResult(
                    success=False,
                    sql_query=None,
                    error="Could not extract valid SQL from LLM response",
                    attempt=attempt,
                    reasoning="No valid SQL found in response"
                )
                
        except Exception as e:
            return SQLResult(
                success=False,
                sql_query=None,
                error=str(e),
                attempt=attempt,
                reasoning=f"Exception during SQL generation: {str(e)}"
            )
    
    def _create_sql_prompt(self, user_query: str, database_schema: Dict[str, Any], attempt: int) -> str:
        """Create the prompt for SQL generation."""
        
        # Build database schema context
        schema_context = self._build_schema_context(database_schema)
        
        # Add retry-specific guidance
        retry_guidance = ""
        if attempt > 1:
            retry_guidance = f"""
This is attempt {attempt}. Previous attempts failed. Please:
1. Double-check table and column names match exactly
2. Use proper SQL syntax for SQLite
3. Make sure to handle text fields with proper quoting
4. Consider case sensitivity
"""

        return f"""You are an expert SQL query generator. Generate a SQLite-compatible SQL query to answer the user's question.

Database Schema:
{schema_context}

User Question: "{user_query}"

{retry_guidance}

Important Rules:
1. ONLY return the SQL query, nothing else
2. Use exact table and column names from the schema
3. Use SQLite-compatible syntax
4. For text searches, use LIKE with wildcards (%)
5. For table_data.row_data (JSON object), use json_extract(row_data, '$."ColumnName"') to access fields
6. IMPORTANT: Cast JSON values to correct types - use CAST(json_extract(...) AS INTEGER) for integers, CAST(json_extract(...) AS REAL) for numbers
7. IMPORTANT: json_extract() returns raw values - for strings compare with 'Value', NOT '"Value"' (no extra quotes)
8. Use proper JOIN syntax if multiple tables are needed
9. Add appropriate WHERE clauses for filtering
10. Use aggregation functions (COUNT, SUM, AVG, etc.) when appropriate

Examples of good SQL queries:
- SELECT * FROM tables WHERE source_file LIKE '%minecraft%';
- SELECT COUNT(*) FROM table_data WHERE table_id = 'sample_table_1';
- SELECT column_names, description FROM tables WHERE rows > 5;
- SELECT row_data FROM table_data WHERE table_id = 'sample_table_1' AND json_extract(row_data, '$."Player Name"') = 'Alex';
- SELECT AVG(CAST(json_extract(row_data, '$."Value"') AS REAL)) FROM table_data WHERE json_extract(row_data, '$."Type"') = 'Tool';
- SELECT row_data FROM table_data WHERE CAST(json_extract(row_data, '$."Level"') AS INTEGER) > 20;
- SELECT row_data FROM table_data WHERE CAST(json_extract(row_data, '$."Health"') AS INTEGER) = 20;
- SELECT json_extract(row_data, '$."Player Name"') FROM table_data WHERE CAST(json_extract(row_data, '$."Level"') AS INTEGER) <= 18;

Generate ONLY the SQL query (no explanations, no markdown formatting):"""

    def _build_schema_context(self, database_schema: Dict[str, Any]) -> str:
        """Build schema context for SQL generation."""
        tables_info = database_schema.get('tables', [])
        
        if not tables_info:
            return "No tables available."
        
        context_parts = [
            "Available tables:",
            "",
            "1. tables (metadata about processed tables):",
            "   - id (INTEGER PRIMARY KEY)",
            "   - table_id (TEXT) - unique identifier for each table", 
            "   - source_file (TEXT) - original HTML file name",
            "   - rows (INTEGER) - number of data rows",
            "   - columns (INTEGER) - number of columns",
            "   - column_names (TEXT) - JSON array of column names",
            "   - column_types (TEXT) - JSON array of column types",
            "   - description (TEXT) - LLM-generated table description",
            "   - created_at (TIMESTAMP)",
            "",
            "2. table_data (actual table row data):",
            "   - id (INTEGER PRIMARY KEY)",
            "   - table_id (TEXT) - references tables.table_id",
            "   - row_index (INTEGER) - row number within table",
            "   - row_data (TEXT) - JSON object with column names as keys",
            "   - created_at (TIMESTAMP)",
            "",
            "3. processing_sessions (processing session tracking):",
            "   - id (INTEGER PRIMARY KEY)",
            "   - session_id (TEXT UNIQUE)",
            "   - source_file (TEXT)",
            "   - total_tables (INTEGER)",
            "   - successful_tables (INTEGER)",
            "   - created_at (TIMESTAMP)"
        ]
        
        # Add specific table information if available
        if tables_info:
            context_parts.extend([
                "",
                "Current data in 'tables':"
            ])
            
            for table in tables_info[:5]:  # Show first 5 tables as examples
                table_desc = [
                    f"- table_id: '{table.get('table_id', 'unknown')}'",
                    f"  source_file: '{table.get('source_file', 'unknown')}'",
                    f"  rows: {table.get('rows', 0)}, columns: {table.get('columns', 0)}"
                ]
                
                if table.get('column_names'):
                    try:
                        columns = json.loads(table['column_names']) if isinstance(table['column_names'], str) else table['column_names']
                        types = json.loads(table['column_types']) if isinstance(table['column_types'], str) else table['column_types']
                        
                        # Create detailed column info with types
                        column_info = []
                        for col in columns:
                            col_type = types.get(col, 'string') if isinstance(types, dict) else 'string'
                            column_info.append(f"{col} ({col_type})")
                        
                        table_desc.append(f"  columns: {column_info}")
                    except:
                        pass
                
                context_parts.append("  " + "\n  ".join(table_desc))
        
        return "\n".join(context_parts)
    
    def _call_llm(self, prompt: str) -> str:
        """Make API call to LLM."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_id,
            "stream": False,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 200,
            "temperature": 0.0
        }
        
        response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    
    def _extract_sql(self, response: str) -> Optional[str]:
        """Extract SQL query from LLM response."""
        response = response.strip()
        
        # Remove common markdown formatting
        if response.startswith("```sql"):
            response = response[6:]
        elif response.startswith("```"):
            response = response[3:]
        
        if response.endswith("```"):
            response = response[:-3]
        
        response = response.strip()
        
        # Basic SQL validation - should start with SELECT, INSERT, UPDATE, DELETE, etc.
        sql_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "WITH"]
        response_upper = response.upper()
        
        if not any(response_upper.startswith(keyword) for keyword in sql_keywords):
            logger.warning(f"Response doesn't start with SQL keyword: {response[:50]}...")
            return None
        
        # Add semicolon if not present
        if not response.endswith(';'):
            response += ';'
        
        return response
    
    def _validate_sql(self, sql_query: str, db_path: str) -> bool:
        """Validate SQL query by trying to execute it (dry run)."""
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # For SELECT queries, add LIMIT 0 to test syntax without returning data
                if sql_query.upper().strip().startswith('SELECT'):
                    test_query = sql_query.rstrip(';') + ' LIMIT 0;'
                    cursor.execute(test_query)
                else:
                    # For other queries, we can't easily test without side effects
                    # So we'll just check if it parses
                    cursor.execute("EXPLAIN QUERY PLAN " + sql_query)
                
                return True
                
        except sqlite3.Error as e:
            logger.warning(f"SQL validation failed: {e}")
            logger.debug(f"Failed SQL: {sql_query}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during SQL validation: {e}")
            return False