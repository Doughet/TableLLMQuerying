"""
Result Exporter for saving query results to various formats.

This module provides a clean interface for exporting query results
to different file formats (CSV, JSON, TXT).
"""

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class ResultExporter:
    """Clean, modular interface for exporting query results."""
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize the ResultExporter.
        
        Args:
            output_dir: Directory to save results. If None, uses current directory.
        """
        self.output_dir = Path(output_dir) if output_dir else Path.cwd()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"ResultExporter initialized with output directory: {self.output_dir}")
    
    def export(self, 
               results: List[Dict[str, Any]], 
               format: str = "csv",
               filename: Optional[str] = None,
               query: Optional[str] = None) -> str:
        """
        Export query results to specified format.
        
        Args:
            results: Query results as list of dictionaries
            format: Export format ('csv', 'json', 'txt')
            filename: Custom filename (without extension)
            query: Original SQL query for metadata
            
        Returns:
            Path to the saved file
        """
        if not results:
            logger.warning("No results to export")
            return ""
        
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"query_results_{timestamp}"
        
        format = format.lower()
        
        if format == "csv":
            return self._export_csv(results, filename, query)
        elif format == "json":
            return self._export_json(results, filename, query)
        elif format == "txt":
            return self._export_txt(results, filename, query)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_csv(self, results: List[Dict[str, Any]], filename: str, query: Optional[str] = None) -> str:
        """Export results to CSV format."""
        filepath = self.output_dir / f"{filename}.csv"
        
        if not results:
            return str(filepath)
        
        # Get all unique fieldnames from all rows
        fieldnames = set()
        for row in results:
            fieldnames.update(row.keys())
        fieldnames = sorted(fieldnames)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Add metadata as comments if query provided
            if query:
                csvfile.write(f"# Query: {query}\n")
                csvfile.write(f"# Exported: {datetime.now().isoformat()}\n")
                csvfile.write(f"# Rows: {len(results)}\n")
            
            writer.writeheader()
            writer.writerows(results)
        
        logger.info(f"Exported {len(results)} rows to CSV: {filepath}")
        return str(filepath)
    
    def _export_json(self, results: List[Dict[str, Any]], filename: str, query: Optional[str] = None) -> str:
        """Export results to JSON format."""
        filepath = self.output_dir / f"{filename}.json"
        
        export_data = {
            "metadata": {
                "exported_at": datetime.now().isoformat(),
                "total_rows": len(results),
                "query": query or "Not provided"
            },
            "results": results
        }
        
        with open(filepath, 'w', encoding='utf-8') as jsonfile:
            json.dump(export_data, jsonfile, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Exported {len(results)} rows to JSON: {filepath}")
        return str(filepath)
    
    def _export_txt(self, results: List[Dict[str, Any]], filename: str, query: Optional[str] = None) -> str:
        """Export results to human-readable text format."""
        filepath = self.output_dir / f"{filename}.txt"
        
        with open(filepath, 'w', encoding='utf-8') as txtfile:
            # Header with metadata
            txtfile.write("=" * 60 + "\n")
            txtfile.write("QUERY RESULTS\n")
            txtfile.write("=" * 60 + "\n")
            if query:
                txtfile.write(f"Query: {query}\n")
            txtfile.write(f"Exported: {datetime.now().isoformat()}\n")
            txtfile.write(f"Total Rows: {len(results)}\n")
            txtfile.write("=" * 60 + "\n\n")
            
            if not results:
                txtfile.write("No results found.\n")
                return str(filepath)
            
            # Get column widths for formatting
            if results:
                columns = list(results[0].keys())
                col_widths = {}
                for col in columns:
                    max_width = max(
                        len(str(col)),
                        max(len(str(row.get(col, ''))) for row in results)
                    )
                    col_widths[col] = min(max_width, 50)  # Cap at 50 chars
                
                # Header row
                header = " | ".join(col.ljust(col_widths[col]) for col in columns)
                txtfile.write(header + "\n")
                txtfile.write("-" * len(header) + "\n")
                
                # Data rows
                for i, row in enumerate(results, 1):
                    row_data = " | ".join(
                        str(row.get(col, '')).ljust(col_widths[col])[:col_widths[col]]
                        for col in columns
                    )
                    txtfile.write(f"{row_data}\n")
                    
                    # Add separator every 10 rows for readability
                    if i % 10 == 0:
                        txtfile.write("-" * len(header) + "\n")
        
        logger.info(f"Exported {len(results)} rows to TXT: {filepath}")
        return str(filepath)
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported export formats."""
        return ["csv", "json", "txt"]
    
    def set_output_directory(self, output_dir: str):
        """Change the output directory."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory changed to: {self.output_dir}")