"""
Query Analyzer for determining if user requests can be fulfilled by querying tables.

This module uses LLM to analyze user prompts and determine if they can be answered
by querying the available table data in the database.
"""

import logging
import requests
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Result of query analysis."""
    is_fulfillable: bool
    confidence: float
    reasoning: str
    suggested_approach: str
    required_tables: List[str] = None


class QueryAnalyzer:
    """Analyzes user queries to determine if they can be fulfilled by table data."""
    
    def __init__(self, api_key: str, model_id: str = "gpt-3.5-turbo"):
        """
        Initialize the QueryAnalyzer.
        
        Args:
            api_key: API key for LLM calls
            model_id: Model to use for analysis
        """
        self.api_key = api_key
        self.model_id = model_id
        self.api_url = "https://api.openai.com/v1/chat/completions"
        logger.info(f"QueryAnalyzer initialized with model {model_id}")
    
    def analyze_query(self, user_query: str, available_tables: List[Dict[str, Any]]) -> AnalysisResult:
        """
        Analyze if a user query can be fulfilled by querying available tables.
        
        Args:
            user_query: The user's question/request
            available_tables: List of available table metadata
            
        Returns:
            AnalysisResult indicating if query is fulfillable
        """
        logger.info(f"Analyzing query: {user_query}")
        
        # Create context about available tables
        tables_context = self._build_tables_context(available_tables)
        
        # Create analysis prompt
        prompt = self._create_analysis_prompt(user_query, tables_context)
        
        try:
            # Get LLM analysis
            response = self._call_llm(prompt)
            
            # Parse response
            result = self._parse_analysis_response(response)
            
            logger.info(f"Analysis result: fulfillable={result.is_fulfillable}, confidence={result.confidence}")
            return result
            
        except Exception as e:
            logger.error(f"Error during query analysis: {e}")
            return AnalysisResult(
                is_fulfillable=False,
                confidence=0.0,
                reasoning=f"Analysis failed due to error: {str(e)}",
                suggested_approach="Please try rephrasing your query or check the system."
            )
    
    def _build_tables_context(self, available_tables: List[Dict[str, Any]]) -> str:
        """Build context string describing available tables."""
        if not available_tables:
            return "No tables available in the database."
        
        context_parts = ["Available tables in the database:"]
        
        for table in available_tables:
            table_info = [
                f"- Table: {table.get('table_id', 'Unknown')}",
                f"  Source: {table.get('source_file', 'Unknown')}",
                f"  Rows: {table.get('rows', 0)}, Columns: {table.get('columns', 0)}"
            ]
            
            # Add column information if available
            if table.get('column_names'):
                try:
                    columns = json.loads(table['column_names']) if isinstance(table['column_names'], str) else table['column_names']
                    table_info.append(f"  Columns: {', '.join(columns)}")
                except:
                    table_info.append(f"  Columns: {table['column_names']}")
            
            # Add description if available
            if table.get('description'):
                desc = table['description']
                table_info.append(f"  Description: {desc}")
            
            context_parts.append("\n".join(table_info))
        
        return "\n\n".join(context_parts)
    
    def _create_analysis_prompt(self, user_query: str, tables_context: str) -> str:
        """Create the prompt for LLM analysis."""
        return f"""You are an expert database query analyst. Your task is to determine if a user's question can be answered by querying the available table data.

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

Examples of fulfillable queries:
- "Show me all data from the inventory table"
- "What are the different categories in the products table?"
- "Find all entries where the price is greater than 100"
- "Count how many items are in stock"

Examples of non-fulfillable queries:
- "What's the weather today?" (not related to table data)
- "Generate a new table with random data" (creation, not querying)
- "Send an email to customer support" (action outside of database)

Be precise and only return the JSON object."""

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
            "max_tokens": 500,
            "temperature": 0.1
        }
        
        response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    
    def _parse_analysis_response(self, response: str) -> AnalysisResult:
        """Parse LLM response into AnalysisResult."""
        try:
            # Extract JSON from response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            
            data = json.loads(response)
            
            return AnalysisResult(
                is_fulfillable=data.get("is_fulfillable", False),
                confidence=float(data.get("confidence", 0.0)),
                reasoning=data.get("reasoning", "No reasoning provided"),
                suggested_approach=data.get("suggested_approach", "No suggestions provided"),
                required_tables=data.get("required_tables", [])
            )
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse analysis response: {e}")
            logger.debug(f"Raw response: {response}")
            
            # Fallback analysis based on keywords
            return self._fallback_analysis(response)
    
    def _fallback_analysis(self, response: str) -> AnalysisResult:
        """Fallback analysis when JSON parsing fails."""
        response_lower = response.lower()
        
        # Simple keyword-based analysis
        positive_keywords = ["yes", "true", "fulfillable", "can be", "possible"]
        negative_keywords = ["no", "false", "impossible", "cannot", "not possible"]
        
        positive_count = sum(1 for word in positive_keywords if word in response_lower)
        negative_count = sum(1 for word in negative_keywords if word in response_lower)
        
        is_fulfillable = positive_count > negative_count
        confidence = 0.3 if positive_count > 0 or negative_count > 0 else 0.1
        
        return AnalysisResult(
            is_fulfillable=is_fulfillable,
            confidence=confidence,
            reasoning=f"Fallback analysis based on response keywords. Raw response: {response[:200]}...",
            suggested_approach="Please try rephrasing your query for better analysis."
        )