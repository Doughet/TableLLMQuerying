"""
Schema Processor module for creating flattened schemas from HTML tables.

Based on the existing preprocessing.py logic, this module handles the extraction
of schemas from HTML tables using pandas and creates flattened representations.
"""

from typing import List, Dict, Any, Optional
import pandas as pd
from io import StringIO
import logging

logger = logging.getLogger(__name__)


class SchemaProcessor:
    """Handles schema extraction and flattening from HTML tables."""
    
    def __init__(self):
        """Initialize the SchemaProcessor."""
        logger.info("SchemaProcessor initialized")
    
    def extract_schema_from_html_table(self, html_table: str, table_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Extract schema from HTML table using pandas, flattening multi-index tables.
        
        Args:
            html_table: HTML table string
            table_id: Optional table identifier
            
        Returns:
            Dictionary with schema information and flattened table data
        """
        try:
            # Read HTML table into pandas DataFrame
            dfs = pd.read_html(StringIO(html_table))
            
            if not dfs:
                return {"table_id": table_id, "error": "No tables found in HTML"}
            
            # Take the first table
            df = dfs[0]
            
            schema = {
                "table_id": table_id,
                "original_shape": df.shape,
                "has_multi_index": False,
                "flattened": False,
                "columns": [],
                "dtypes": {},
                "sample_data": []
            }
            
            # Check if we have multi-index columns
            if isinstance(df.columns, pd.MultiIndex):
                schema["has_multi_index"] = True
                
                # Flatten multi-index columns by joining levels with underscores
                flattened_columns = []
                for col in df.columns:
                    # Join non-empty parts of the multi-index
                    col_parts = [str(part) for part in col if str(part) not in ['', 'Unnamed: 0', 'Unnamed']]
                    flattened_name = '_'.join(col_parts) if col_parts else f"col_{len(flattened_columns)}"
                    flattened_columns.append(flattened_name)
                
                df.columns = flattened_columns
                schema["flattened"] = True
                logger.info(f"Flattened multi-index columns for table {table_id}")
            
            # Process column information
            for col in df.columns:
                col_name = str(col)
                col_values = df[col].astype(str).tolist()
                inferred_type = self._infer_type_from_values(col_values)
                
                schema["columns"].append(col_name)
                schema["dtypes"][col_name] = inferred_type
            
            # Get sample data (first few rows)
            sample_size = min(5, len(df))
            if sample_size > 0:
                schema["sample_data"] = df.head(sample_size).to_dict('records')
            
            # Add processed DataFrame for storage
            schema["dataframe"] = df
            schema["success"] = True
            
            logger.info(f"Successfully extracted schema for table {table_id}: {df.shape[0]} rows, {df.shape[1]} columns")
            
            return schema
            
        except Exception as e:
            logger.error(f"Error extracting schema from table {table_id}: {e}")
            return {
                "table_id": table_id,
                "error": f"Schema extraction failed: {str(e)}",
                "success": False
            }
    
    def extract_schemas_from_tables(self, html_tables: List[str]) -> List[Dict[str, Any]]:
        """
        Extract schemas from multiple HTML tables.
        
        Args:
            html_tables: List of HTML table strings
            
        Returns:
            List of schema dictionaries
        """
        schemas = []
        
        for i, table_html in enumerate(html_tables):
            table_id = i + 1
            schema = self.extract_schema_from_html_table(table_html, table_id)
            schemas.append(schema)
        
        successful_schemas = sum(1 for schema in schemas if schema.get("success", False))
        logger.info(f"Successfully extracted {successful_schemas}/{len(schemas)} table schemas")
        
        return schemas
    
    def _infer_type_from_values(self, values: List[str]) -> str:
        """Infer data type from a list of values."""
        if not values:
            return "string"
        
        # Filter out empty values
        non_empty_values = [v for v in values if v and v.strip() and v != '-']
        
        if not non_empty_values:
            return "string"
        
        # Check type consistency
        integer_count = sum(1 for v in non_empty_values if self._is_integer(v))
        float_count = sum(1 for v in non_empty_values if self._is_float(v))
        boolean_count = sum(1 for v in non_empty_values if self._is_boolean(v))
        
        total = len(non_empty_values)
        
        # If most values are integers
        if integer_count / total > 0.8:
            return "integer"
        
        # If most values are floats (including integers)
        if float_count / total > 0.8:
            return "float"
        
        # If most values are booleans
        if boolean_count / total > 0.8:
            return "boolean"
        
        return "string"
    
    def _is_integer(self, value: str) -> bool:
        """Check if a string represents an integer."""
        try:
            int(value)
            return True
        except ValueError:
            return False
    
    def _is_float(self, value: str) -> bool:
        """Check if a string represents a float."""
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    def _is_boolean(self, value: str) -> bool:
        """Check if a string represents a boolean."""
        return value.lower() in ['true', 'false', 'yes', 'no', 'on', 'off', '1', '0']
    
    def create_schema_summary(self, schema: Dict[str, Any]) -> str:
        """
        Create a human-readable summary of a table schema.
        
        Args:
            schema: Schema dictionary
            
        Returns:
            Human-readable schema summary
        """
        if not schema.get("success", False):
            return f"Table {schema.get('table_id', 'unknown')}: Schema extraction failed - {schema.get('error', 'Unknown error')}"
        
        table_id = schema.get('table_id', 'unknown')
        rows, cols = schema.get('original_shape', (0, 0))
        columns = schema.get('columns', [])
        dtypes = schema.get('dtypes', {})
        
        summary = f"Table {table_id}:\n"
        summary += f"  Shape: {rows} rows × {cols} columns\n"
        
        if schema.get('has_multi_index'):
            summary += "  Multi-index columns detected and flattened\n"
        
        summary += "  Columns:\n"
        for col in columns:
            col_type = dtypes.get(col, 'unknown')
            summary += f"    - {col} ({col_type})\n"
        
        return summary