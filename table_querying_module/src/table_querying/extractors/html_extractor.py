"""
HTML Table Extractor.

This module handles extraction of tables from HTML documents using BeautifulSoup
and docling for document conversion.
"""

from typing import List, Dict, Any
from pathlib import Path
from bs4 import BeautifulSoup
from docling.document_converter import DocumentConverter
import re
import logging

from .base_extractor import BaseTableExtractor, ExtractionResult

logger = logging.getLogger(__name__)


class HTMLTableExtractor(BaseTableExtractor):
    """Extracts tables from HTML documents."""
    
    def __init__(self):
        """Initialize the HTML table extractor."""
        super().__init__()
        self.converter = DocumentConverter()
        self.logger.info("HTMLTableExtractor initialized")
    
    def supports_file_type(self, file_path: str) -> bool:
        """Check if this is an HTML file."""
        return Path(file_path).suffix.lower() in ['.html', '.htm']
    
    def get_supported_extensions(self) -> List[str]:
        """Get supported HTML file extensions."""
        return ['.html', '.htm']
    
    def extract_from_file(self, file_path: str) -> ExtractionResult:
        """
        Extract tables and content from an HTML file.
        
        Args:
            file_path: Path to the HTML file
            
        Returns:
            ExtractionResult containing extracted HTML tables and markdown content
        """
        try:
            self.validate_file(file_path)
            
            input_path = Path(file_path)
            
            # Read HTML content
            with open(input_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Extract HTML tables
            html_tables = self._extract_html_tables(html_content)
            
            # Convert to markdown
            markdown_content = self._html_to_markdown(input_path)
            
            # Split markdown at table boundaries
            markdown_chunks = self._split_markdown_at_tables(markdown_content)
            
            extracted_data = {
                'html_content': html_content,
                'html_tables': html_tables,
                'markdown_content': markdown_content,
                'markdown_chunks': markdown_chunks,
                'source_file': str(input_path)
            }
            
            self.logger.info(
                f"Processed HTML file {file_path}: "
                f"{len(html_tables)} HTML tables, {len(markdown_chunks)} markdown chunks"
            )
            
            return ExtractionResult(
                source_file=str(input_path),
                tables_found=len(html_tables),
                extraction_successful=True,
                extracted_data=extracted_data
            )
            
        except Exception as e:
            self.logger.error(f"Failed to extract from HTML file {file_path}: {e}")
            return ExtractionResult(
                source_file=file_path,
                tables_found=0,
                extraction_successful=False,
                error_message=str(e)
            )
    
    def _extract_html_tables(self, html_content: str) -> List[str]:
        """
        Extract all HTML tables from the full HTML page.
        
        Args:
            html_content: Full HTML content as string
            
        Returns:
            List of HTML table strings
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        tables = soup.find_all('table')
        
        table_html_list = [str(table) for table in tables]
        
        self.logger.debug(f"Extracted {len(table_html_list)} HTML tables")
        return table_html_list
    
    def _html_to_markdown(self, file_path: Path) -> str:
        """
        Convert HTML file to markdown using docling.
        
        Args:
            file_path: Path to the HTML file
            
        Returns:
            Markdown content as string
        """
        result = self.converter.convert(file_path)
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
        table_pattern = r'^(\|.*\|)$'
        
        lines = markdown_content.split('\n')
        chunks = []
        current_chunk = []
        in_table = False
        
        for line in lines:
            is_table_line = bool(re.match(table_pattern, line.strip()))
            
            if is_table_line and not in_table:
                if current_chunk:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = []
                in_table = True
                current_chunk.append(line)
            
            elif in_table and not is_table_line:
                separator_pattern = r'^[\|\-\:\s]*$'
                if re.match(separator_pattern, line.strip()) and line.strip():
                    current_chunk.append(line)
                else:
                    if current_chunk:
                        chunks.append('\n'.join(current_chunk))
                        current_chunk = []
                    in_table = False
                    current_chunk.append(line)
            
            else:
                current_chunk.append(line)
        
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
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
            lines = chunk.strip().split('\n')
            table_line_count = sum(1 for line in lines if re.match(table_pattern, line.strip()))
            
            if lines and table_line_count > len(lines) * 0.5:
                table_positions.append(i)
        
        self.logger.debug(f"Identified {len(table_positions)} table chunks at positions: {table_positions}")
        return table_positions