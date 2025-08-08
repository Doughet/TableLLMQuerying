"""
Table Summarizer module for generating LLM descriptions of tables.

Based on the existing descriptor_mistral.py logic, this module handles the generation
of natural language descriptions of tables using LLM models.
"""

import os
import json
import requests
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class TableSummarizer:
    """Generates intelligent descriptions of tables using LLM models."""
    
    def __init__(self, api_key: Optional[str] = None, model_id: str = "mistral-small"):
        """
        Initialize the TableSummarizer.
        
        Args:
            api_key: BHub API key. If not provided, will use YOUR_API_KEY environment variable
            model_id: Model to use for generation
        """
        self.api_key = api_key or os.getenv("YOUR_API_KEY") or "sk-olympia-c1212a60ef6e_254664cd5156954c"
        if not self.api_key:
            raise ValueError("Please provide a BHub API key either as parameter or set YOUR_API_KEY environment variable")
        
        self.model_id = model_id
        self.base_url = "https://api.olympia.bhub.cloud/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"TableSummarizer initialized with model {model_id}")
    
    def _generate_response(self, prompt: str, max_tokens: int = 1000) -> str:
        """
        Generate response using the LLM model.
        
        Args:
            prompt: The input prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response
        """
        try:
            payload = {
                "model": self.model_id,
                "stream": False,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.3
            }
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            
            if 'choices' in result and len(result['choices']) > 0:
                message = result['choices'][0]['message']
                return message['content'].strip()
            
            return "No response generated"
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise Exception(f"Table description generation failed: {e}")
    
    def describe_table_from_schema(self, schema: Dict[str, Any], context: Optional[str] = None) -> str:
        """
        Generate a natural language description of a table based on its schema.
        
        Args:
            schema: Schema dictionary from SchemaProcessor
            context: Optional context about the document/domain
            
        Returns:
            Natural language description of the table
        """
        if not schema.get("success", False):
            return f"Unable to describe table {schema.get('table_id', 'unknown')}: {schema.get('error', 'Schema extraction failed')}"
        
        # Extract key information from schema
        table_id = schema.get('table_id', 'unknown')
        rows, cols = schema.get('original_shape', (0, 0))
        columns = schema.get('columns', [])
        dtypes = schema.get('dtypes', {})
        sample_data = schema.get('sample_data', [])
        
        # Build the prompt for LLM
        prompt = self._build_table_description_prompt(
            table_id, rows, cols, columns, dtypes, sample_data, context
        )
        
        try:
            description = self._generate_response(prompt, max_tokens=800)
            logger.info(f"Generated description for table {table_id}")
            return description
        except Exception as e:
            logger.error(f"Failed to generate description for table {table_id}: {e}")
            return f"Table {table_id}: A table with {rows} rows and {cols} columns. Failed to generate detailed description."
    
    def describe_multiple_tables(self, schemas: List[Dict[str, Any]], context: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Generate descriptions for multiple tables.
        
        Args:
            schemas: List of schema dictionaries
            context: Optional context about the document/domain
            
        Returns:
            List of dictionaries with table descriptions
        """
        descriptions = []
        
        for schema in schemas:
            table_id = schema.get('table_id', len(descriptions) + 1)
            
            try:
                description = self.describe_table_from_schema(schema, context)
                
                descriptions.append({
                    "table_id": table_id,
                    "description": description,
                    "status": "success",
                    "schema": schema
                })
                
            except Exception as e:
                logger.error(f"Failed to describe table {table_id}: {e}")
                descriptions.append({
                    "table_id": table_id,
                    "description": f"Failed to generate description: {str(e)}",
                    "status": "error",
                    "schema": schema
                })
        
        successful_descriptions = sum(1 for desc in descriptions if desc["status"] == "success")
        logger.info(f"Generated {successful_descriptions}/{len(descriptions)} table descriptions")
        
        return descriptions
    
    def _build_table_description_prompt(self, table_id: int, rows: int, cols: int, 
                                      columns: List[str], dtypes: Dict[str, str], 
                                      sample_data: List[Dict], context: Optional[str] = None) -> str:
        """
        Build a comprehensive prompt for table description generation.
        """
        context_info = f" The table comes from a {context} document." if context else ""
        
        prompt = f"""Analyze this table and provide a clear, concise description that explains what the table contains and its purpose.{context_info}

Table Information:
- Table ID: {table_id}
- Dimensions: {rows} rows × {cols} columns
- Column Names: {', '.join(columns)}

Column Types:
"""
        
        for col, dtype in dtypes.items():
            prompt += f"- {col}: {dtype}\n"
        
        if sample_data:
            prompt += f"\nSample Data (first few rows):\n"
            for i, row in enumerate(sample_data[:3], 1):
                prompt += f"Row {i}: {row}\n"
        
        prompt += """
Please provide a description that:
1. Explains what type of data this table contains
2. Describes the main purpose or function of the table  
3. Highlights any notable patterns or relationships in the data
4. Mentions key columns and their significance
5. Is concise but informative (2-4 sentences)

Description:"""
        
        return prompt
    
    def create_table_summary_report(self, descriptions: List[Dict[str, Any]]) -> str:
        """
        Create a comprehensive report of all table descriptions.
        
        Args:
            descriptions: List of table description dictionaries
            
        Returns:
            Formatted report string
        """
        report = "TABLE SUMMARY REPORT\n"
        report += "=" * 50 + "\n\n"
        
        successful_count = sum(1 for desc in descriptions if desc["status"] == "success")
        total_count = len(descriptions)
        
        report += f"Total Tables: {total_count}\n"
        report += f"Successfully Described: {successful_count}\n"
        report += f"Failed: {total_count - successful_count}\n\n"
        
        for desc in descriptions:
            table_id = desc.get("table_id", "unknown")
            status = desc.get("status", "unknown")
            description = desc.get("description", "No description available")
            
            report += f"TABLE {table_id} ({status.upper()})\n"
            report += "-" * 30 + "\n"
            report += f"{description}\n\n"
        
        return report