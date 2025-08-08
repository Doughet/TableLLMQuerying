"""
Table Extractor module for extracting tables from HTML documents.

Based on the existing preprocessing.py logic, this module handles the extraction
of HTML tables from documents and conversion to markdown format.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from bs4 import BeautifulSoup
from docling.document_converter import DocumentConverter
import re
import logging

logger = logging.getLogger(__name__)


class TableExtractor:
    """Handles extraction of tables from HTML documents."""
    
    def __init__(self):
        """Initialize the TableExtractor."""
        self.converter = DocumentConverter()
        logger.info("TableExtractor initialized")
    
    def extract_html_tables(self, html_content: str) -> List[str]:
        """
        Extract all HTML tables from the full HTML page.
        
        Args:
            html_content: Full HTML content as string
            
        Returns:
            List of HTML table strings
        """
        # Parse the HTML content
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all table elements
        tables = soup.find_all('table')
        
        # Convert each table back to HTML string
        table_html_list = []
        for table in tables:
            table_html_list.append(str(table))
        
        logger.info(f"Extracted {len(table_html_list)} HTML tables")
        return table_html_list
    
    def extract_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        Extract tables and markdown content from an HTML file.
        
        Args:
            file_path: Path to the HTML file
            
        Returns:
            Dictionary containing:
            - html_content: Original HTML content
            - html_tables: List of HTML table strings
            - markdown_content: Markdown conversion of the document
            - markdown_chunks: Markdown split at table boundaries
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is not supported
        """
        input_path = Path(file_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        if not input_path.suffix.lower() in ['.html', '.htm']:
            raise ValueError(f"Unsupported file format: {input_path.suffix}. Only HTML files are supported.")
        
        # Read HTML content
        with open(input_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Extract HTML tables
        html_tables = self.extract_html_tables(html_content)
        
        # Convert to markdown
        markdown_content = self._html_to_markdown(input_path)
        
        # Split markdown at table boundaries
        markdown_chunks = self._split_markdown_at_tables(markdown_content)
        
        logger.info(f"Processed file {file_path}: {len(html_tables)} HTML tables, {len(markdown_chunks)} markdown chunks")
        
        return {
            'html_content': html_content,
            'html_tables': html_tables,
            'markdown_content': markdown_content,
            'markdown_chunks': markdown_chunks,
            'source_file': str(input_path)
        }
    
    def _html_to_markdown(self, file_path: Path) -> str:
        """
        Convert HTML file to markdown using docling.
        
        Args:
            file_path: Path to the HTML file
            
        Returns:
            Markdown content as string
        """
        # Convert document to markdown
        result = self.converter.convert(file_path)
        
        # Export to Markdown format
        markdown_content = result.document.export_to_markdown()
        
        return markdown_content
    
    def _split_markdown_at_tables(self, markdown_content: str) -> List[str]:
        """
        Split markdown content every time it encounters a table.
        
        Args:
            markdown_content: Markdown content to split
            
        Returns:
            List of markdown chunks split at table boundaries
        """
        # Pattern to match markdown tables (lines that start with |)
        table_pattern = r'^(\|.*\|)$'
        
        lines = markdown_content.split('\n')
        chunks = []
        current_chunk = []
        in_table = False
        
        for line in lines:
            # Check if line is part of a table
            is_table_line = bool(re.match(table_pattern, line.strip()))
            
            # If we encounter a table line and we're not in a table
            if is_table_line and not in_table:
                # Save the current chunk if it has content
                if current_chunk:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = []
                in_table = True
                current_chunk.append(line)
            
            # If we're in a table and encounter a non-table line
            elif in_table and not is_table_line:
                # Check if it's a table separator line (contains only |, -, :, and spaces)
                separator_pattern = r'^[\|\-\:\s]*$'
                if re.match(separator_pattern, line.strip()) and line.strip():
                    # This is a table separator, keep it in the table
                    current_chunk.append(line)
                else:
                    # End of table - save table chunk and start new chunk
                    if current_chunk:
                        chunks.append('\n'.join(current_chunk))
                        current_chunk = []
                    in_table = False
                    current_chunk.append(line)
            
            # Normal processing - add line to current chunk
            else:
                current_chunk.append(line)
        
        # Add the final chunk if it has content
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        # Filter out empty chunks
        chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
        
        return chunks
    
    def identify_table_chunks(self, markdown_chunks: List[str]) -> List[int]:
        """
        Identify which chunks contain tables.
        
        Args:
            markdown_chunks: List of markdown chunks
            
        Returns:
            List of indices indicating which chunks contain tables
        """
        table_positions = []
        table_pattern = r'^(\|.*\|)$'
        
        for i, chunk in enumerate(markdown_chunks):
            # Check if chunk contains table content by looking for markdown table lines
            lines = chunk.strip().split('\n')
            table_line_count = sum(1 for line in lines if re.match(table_pattern, line.strip()))
            
            # If more than half the lines are table lines, consider this chunk a table
            if lines and table_line_count > len(lines) * 0.5:
                table_positions.append(i)
        
        logger.info(f"Identified {len(table_positions)} table chunks at positions: {table_positions}")
        return table_positions