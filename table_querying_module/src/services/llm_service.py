"""
Abstract LLM Service Interface.

This module defines the interface for LLM services, making it easy to 
plug in different LLM providers (OpenAI, Anthropic, local models, etc.).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional, List


@dataclass
class LLMResponse:
    """Standard response format for LLM services."""
    content: str
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class LLMService(ABC):
    """Abstract base class for LLM services."""
    
    def __init__(self, **config):
        """
        Initialize the LLM service.
        
        Args:
            **config: Service-specific configuration parameters
        """
        self.config = config
    
    @abstractmethod
    def generate_completion(self, prompt: str, **kwargs) -> LLMResponse:
        """
        Generate a completion for the given prompt.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional generation parameters (temperature, max_tokens, etc.)
            
        Returns:
            LLMResponse with the generated content
        """
        pass
    
    @abstractmethod
    def generate_chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """
        Generate a chat completion for the given messages.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            **kwargs: Additional generation parameters
            
        Returns:
            LLMResponse with the generated content
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the LLM service is available and properly configured.
        
        Returns:
            True if service is ready to use, False otherwise
        """
        pass
    
    def generate_table_description(self, schema: Dict[str, Any], context_hint: str = "") -> LLMResponse:
        """
        Generate a description for a table based on its schema.
        This is a convenience method that can be overridden for service-specific optimizations.
        
        Args:
            schema: Table schema dictionary
            context_hint: Optional context to improve description quality
            
        Returns:
            LLMResponse with table description
        """
        prompt = self._build_table_description_prompt(schema, context_hint)
        return self.generate_completion(prompt, temperature=0.1, max_tokens=300)
    
    def generate_sql_query(self, user_query: str, database_schema: Dict[str, Any]) -> LLMResponse:
        """
        Generate SQL query from natural language.
        This is a convenience method that can be overridden for service-specific optimizations.
        
        Args:
            user_query: Natural language query
            database_schema: Database schema information
            
        Returns:
            LLMResponse with SQL query
        """
        prompt = self._build_sql_generation_prompt(user_query, database_schema)
        return self.generate_completion(prompt, temperature=0.0, max_tokens=200)
    
    def analyze_query_feasibility(self, user_query: str, available_tables: List[Dict[str, Any]]) -> LLMResponse:
        """
        Analyze if a user query can be fulfilled with available tables.
        
        Args:
            user_query: User's natural language query
            available_tables: List of available table metadata
            
        Returns:
            LLMResponse with analysis result (JSON format)
        """
        prompt = self._build_query_analysis_prompt(user_query, available_tables)
        return self.generate_completion(prompt, temperature=0.1, max_tokens=500)
    
    def _build_table_description_prompt(self, schema: Dict[str, Any], context_hint: str = "") -> str:
        """Build prompt for table description generation."""
        table_id = schema.get('table_id', 'unknown')
        rows = schema.get('rows', 0)
        columns = schema.get('columns', [])
        
        context_text = f"\nContext: {context_hint}" if context_hint else ""
        
        return f"""Analyze the following table and provide a clear, informative description.

Table ID: {table_id}
Rows: {rows}
Columns: {', '.join(columns)}{context_text}

Table Data Sample:
{schema.get('sample_data', 'No sample data available')}

Please provide:
1. What type of data this table contains
2. The main purpose or use case of this table
3. Any notable patterns or relationships in the data
4. Which columns are most important for understanding the table

Respond with a single paragraph description that would help someone quickly understand this table's content and purpose."""
    
    def _build_sql_generation_prompt(self, user_query: str, database_schema: Dict[str, Any]) -> str:
        """Build prompt for SQL generation."""
        return f"""You are an expert SQL query generator. Generate a SQLite-compatible SQL query to answer the user's question.

Database Schema:
{self._format_database_schema(database_schema)}

User Question: "{user_query}"

Important Rules:
1. ONLY return the SQL query, nothing else
2. Use exact table and column names from the schema
3. Use SQLite-compatible syntax
4. For table_data.row_data (JSON object), use json_extract(row_data, '$.\"ColumnName\"') to access fields
5. Cast JSON values to correct types - use CAST(json_extract(...) AS INTEGER) for integers, CAST(json_extract(...) AS REAL) for numbers
6. json_extract() returns raw values - for strings compare with 'Value', NOT '\"Value\"' (no extra quotes)

Generate ONLY the SQL query (no explanations, no markdown formatting):"""
    
    def _build_query_analysis_prompt(self, user_query: str, available_tables: List[Dict[str, Any]]) -> str:
        """Build prompt for query analysis."""
        tables_context = self._format_tables_context(available_tables)
        
        return f"""You are an expert database query analyst. Determine if a user's question can be answered by querying the available table data.

{tables_context}

User Query: "{user_query}"

Analyze whether this query can be fulfilled by querying the available tables. Consider:
1. Does the query ask for information that could be contained in the tables?
2. Are the required data fields likely present in the table columns?
3. Is the query asking for data aggregation, filtering, or specific lookups that are feasible with SQL?

Respond with a JSON object in this exact format:
{{
    "is_fulfillable": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "Detailed explanation of your analysis",
    "suggested_approach": "How to approach this query (if fulfillable) or alternative suggestions",
    "required_tables": ["list", "of", "table_ids", "needed"]
}}

Be precise and only return the JSON object."""
    
    def _format_database_schema(self, database_schema: Dict[str, Any]) -> str:
        """Format database schema for prompts."""
        # This can be overridden by specific implementations
        return str(database_schema)
    
    def _format_tables_context(self, available_tables: List[Dict[str, Any]]) -> str:
        """Format available tables context for prompts."""
        if not available_tables:
            return "No tables available in the database."
        
        context_parts = ["Available tables in the database:"]
        
        for table in available_tables:
            table_info = [
                f"- Table: {table.get('table_id', 'Unknown')}",
                f"  Source: {table.get('source_file', 'Unknown')}",
                f"  Rows: {table.get('rows', 0)}, Columns: {table.get('columns', 0)}"
            ]
            
            if table.get('column_names'):
                columns = table['column_names']
                if isinstance(columns, str):
                    import json
                    try:
                        columns = json.loads(columns)
                    except:
                        pass
                table_info.append(f"  Columns: {', '.join(columns) if isinstance(columns, list) else columns}")
            
            if table.get('description'):
                table_info.append(f"  Description: {table['description']}")
            
            context_parts.append("\n".join(table_info))
        
        return "\n\n".join(context_parts)