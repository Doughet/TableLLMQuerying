"""
Excel Table Extractor.

This module handles extraction of tables from Excel files (.xlsx, .xls) using docling
for advanced table detection and pandas as fallback. Can detect multiple tables per sheet.
"""

from typing import List, Dict, Any
from pathlib import Path
import logging
from docling.document_converter import DocumentConverter

from .base_extractor import BaseTableExtractor, ExtractionResult

logger = logging.getLogger(__name__)


class ExcelTableExtractor(BaseTableExtractor):
    """Extracts tables from Excel documents using docling with pandas fallback."""
    
    def __init__(self):
        """Initialize the Excel table extractor."""
        super().__init__()
        try:
            self.converter = DocumentConverter()
            self.use_docling = True
            self.logger.info("ExcelTableExtractor initialized with docling support")
        except Exception as e:
            self.converter = None
            self.use_docling = False
            self.logger.warning(f"Docling not available, falling back to pandas: {e}")
            self.logger.info("ExcelTableExtractor initialized with pandas fallback")
    
    def supports_file_type(self, file_path: str) -> bool:
        """Check if this is an Excel file."""
        return Path(file_path).suffix.lower() in ['.xlsx', '.xls']
    
    def get_supported_extensions(self) -> List[str]:
        """Get supported Excel file extensions."""
        return ['.xlsx', '.xls']
    
    def extract_from_file(self, file_path: str) -> ExtractionResult:
        """
        Extract tables from an Excel file.
        
        Uses docling for advanced table detection (can find multiple tables per sheet)
        with pandas fallback for compatibility.
        
        Args:
            file_path: Path to the Excel file
            
        Returns:
            ExtractionResult containing extracted tables
        """
        try:
            self.validate_file(file_path)
            
            if self.use_docling and self.converter:
                return self._extract_with_docling(file_path)
            else:
                return self._extract_with_pandas(file_path)
                
        except Exception as e:
            self.logger.error(f"Failed to extract from Excel file {file_path}: {e}")
            return ExtractionResult(
                source_file=file_path,
                tables_found=0,
                extraction_successful=False,
                error_message=str(e)
            )
    
    def _extract_with_docling(self, file_path: str) -> ExtractionResult:
        """
        Extract tables using docling (can detect multiple tables per sheet).
        
        Args:
            file_path: Path to the Excel file
            
        Returns:
            ExtractionResult with tables found by docling
        """
        try:
            input_path = Path(file_path)
            
            self.logger.info(f"Using docling to extract from Excel: {file_path}")
            
            # Convert document using docling
            result = self.converter.convert(input_path)
            doc = result.document
            
            tables = []
            html_tables = []
            markdown_chunks = []
            
            # Extract tables from the document
            if hasattr(doc, 'tables') and doc.tables:
                # docling found tables - process each one
                for i, table in enumerate(doc.tables):
                    table_info = self._process_docling_table(table, i, input_path)
                    if table_info:
                        tables.append(table_info)
                        html_tables.append(table_info['html'])
                        markdown_chunks.append(table_info['markdown'])
                        
                        self.logger.debug(
                            f"Extracted table {i+1}: "
                            f"{table_info['rows']} rows, {len(table_info['columns'])} columns"
                        )
            else:
                # No tables found by docling, try to extract from markdown
                markdown_content = doc.export_to_markdown()
                if markdown_content and ('|' in markdown_content):
                    # Found table-like content in markdown
                    table_info = self._process_markdown_table(markdown_content, input_path)
                    if table_info:
                        tables.append(table_info)
                        html_tables.append(table_info['html'])
                        markdown_chunks.append(table_info['markdown'])
            
            if not tables:
                # Fallback to pandas if docling didn't find tables
                self.logger.info("Docling found no tables, falling back to pandas")
                return self._extract_with_pandas(file_path)
            
            extracted_data = {
                'excel_sheets': tables,
                'html_tables': html_tables,
                'markdown_chunks': markdown_chunks,
                'source_file': str(input_path),
                'extraction_method': 'docling'
            }
            
            self.logger.info(
                f"Processed Excel file with docling {file_path}: "
                f"{len(tables)} tables extracted"
            )
            
            return ExtractionResult(
                source_file=str(input_path),
                tables_found=len(tables),
                extraction_successful=True,
                extracted_data=extracted_data
            )
            
        except Exception as e:
            self.logger.warning(f"Docling extraction failed: {e}, falling back to pandas")
            return self._extract_with_pandas(file_path)
    
    def _extract_with_pandas(self, file_path: str) -> ExtractionResult:
        """
        Extract tables using pandas (treats each sheet as one table).
        
        Args:
            file_path: Path to the Excel file
            
        Returns:
            ExtractionResult with sheet-based tables
        """
        # Import pandas here to avoid dependency issues if not installed
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "pandas is required for Excel extraction. "
                "Install with: pip install pandas openpyxl xlrd"
            )
        
        input_path = Path(file_path)
        
        self.logger.info(f"Using pandas to extract from Excel: {file_path}")
        
        # Read all sheets from Excel file
        excel_data = pd.read_excel(
            file_path, 
            sheet_name=None, 
            engine='openpyxl' if input_path.suffix == '.xlsx' else 'xlrd'
        )
        
        tables = []
        html_tables = []
        markdown_chunks = []
        
        for sheet_name, df in excel_data.items():
            if not df.empty:
                # Clean the dataframe
                df_cleaned = self._clean_dataframe(df)
                
                # Convert to different formats
                html_table = df_cleaned.to_html(index=False, escape=False)
                markdown_table = df_cleaned.to_markdown(index=False)
                
                table_info = {
                    'sheet_name': sheet_name,
                    'table_id': f"{input_path.stem}_{sheet_name}",
                    'data': df_cleaned,
                    'html': html_table,
                    'markdown': markdown_table,
                    'rows': len(df_cleaned),
                    'columns': list(df_cleaned.columns),
                    'extraction_method': 'pandas'
                }
                
                tables.append(table_info)
                html_tables.append(html_table)
                markdown_chunks.append(markdown_table)
                
                self.logger.debug(
                    f"Extracted sheet '{sheet_name}': "
                    f"{len(df_cleaned)} rows, {len(df_cleaned.columns)} columns"
                )
        
        extracted_data = {
            'excel_sheets': tables,
            'html_tables': html_tables,
            'markdown_chunks': markdown_chunks,
            'source_file': str(input_path),
            'extraction_method': 'pandas'
        }
        
        self.logger.info(
            f"Processed Excel file with pandas {file_path}: "
            f"{len(tables)} sheets extracted as tables"
        )
        
        return ExtractionResult(
            source_file=str(input_path),
            tables_found=len(tables),
            extraction_successful=True,
            extracted_data=extracted_data
        )
    
    def _clean_dataframe(self, df) -> Any:
        """
        Clean the dataframe by handling common Excel issues.
        
        Args:
            df: Pandas DataFrame to clean
            
        Returns:
            Cleaned DataFrame
        """
        import pandas as pd
        
        # Make a copy to avoid modifying the original
        df_cleaned = df.copy()
        
        # Drop rows that are completely empty
        df_cleaned = df_cleaned.dropna(how='all')
        
        # Drop columns that are completely empty
        df_cleaned = df_cleaned.dropna(axis=1, how='all')
        
        # Reset index after dropping rows
        df_cleaned = df_cleaned.reset_index(drop=True)
        
        # Handle unnamed columns
        columns = []
        for i, col in enumerate(df_cleaned.columns):
            if pd.isna(col) or str(col).startswith('Unnamed:'):
                columns.append(f'Column_{i+1}')
            else:
                columns.append(str(col))
        
        df_cleaned.columns = columns
        
        # Fill NaN values with empty strings for better display
        df_cleaned = df_cleaned.fillna('')
        
        return df_cleaned
    
    def get_sheet_names(self, file_path: str) -> List[str]:
        """
        Get list of sheet names from Excel file without reading full data.
        
        Args:
            file_path: Path to the Excel file
            
        Returns:
            List of sheet names
        """
        try:
            import pandas as pd
            excel_file = pd.ExcelFile(file_path)
            return excel_file.sheet_names
        except Exception as e:
            self.logger.error(f"Failed to get sheet names from {file_path}: {e}")
            return []
    
    def extract_specific_sheet(self, file_path: str, sheet_name: str) -> Dict[str, Any]:
        """
        Extract data from a specific sheet only.
        
        Args:
            file_path: Path to the Excel file
            sheet_name: Name of the sheet to extract
            
        Returns:
            Dictionary with extracted sheet data
        """
        try:
            import pandas as pd
            
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            df_cleaned = self._clean_dataframe(df)
            
            return {
                'sheet_name': sheet_name,
                'data': df_cleaned,
                'html': df_cleaned.to_html(index=False, escape=False),
                'markdown': df_cleaned.to_markdown(index=False),
                'rows': len(df_cleaned),
                'columns': list(df_cleaned.columns)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to extract sheet '{sheet_name}' from {file_path}: {e}")
            return {}
    
    def _process_docling_table(self, table, table_index: int, input_path: Path) -> Dict[str, Any]:
        """
        Process a table detected by docling.
        
        Args:
            table: Docling table object
            table_index: Index of the table
            input_path: Path to the input file
            
        Returns:
            Dictionary with processed table information
        """
        try:
            # Try to extract table data in different ways
            table_data = None
            
            # Method 1: Try to get structured data if available
            if hasattr(table, 'data') and table.data:
                table_data = self._convert_docling_data_to_dataframe(table.data)
            
            # Method 2: Try to export to markdown and parse
            elif hasattr(table, 'export_to_markdown'):
                markdown_content = table.export_to_markdown()
                table_data = self._parse_markdown_table_to_dataframe(markdown_content)
            
            # Method 3: Try to get HTML representation
            elif hasattr(table, 'export_to_html') or hasattr(table, 'to_html'):
                html_content = getattr(table, 'export_to_html', getattr(table, 'to_html', lambda: None))()
                if html_content:
                    table_data = self._parse_html_table_to_dataframe(html_content)
            
            if table_data is not None and not table_data.empty:
                # Clean the dataframe
                df_cleaned = self._clean_dataframe(table_data)
                
                # Generate formats
                html_table = df_cleaned.to_html(index=False, escape=False)
                markdown_table = df_cleaned.to_markdown(index=False)
                
                return {
                    'table_id': f"{input_path.stem}_table_{table_index + 1}",
                    'sheet_name': f"Table_{table_index + 1}",
                    'data': df_cleaned,
                    'html': html_table,
                    'markdown': markdown_table,
                    'rows': len(df_cleaned),
                    'columns': list(df_cleaned.columns),
                    'extraction_method': 'docling'
                }
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Failed to process docling table {table_index}: {e}")
            return None
    
    def _process_markdown_table(self, markdown_content: str, input_path: Path) -> Dict[str, Any]:
        """
        Process markdown content that contains tables.
        
        Args:
            markdown_content: Markdown content with tables
            input_path: Path to the input file
            
        Returns:
            Dictionary with processed table information
        """
        try:
            # Parse markdown tables
            table_data = self._parse_markdown_table_to_dataframe(markdown_content)
            
            if table_data is not None and not table_data.empty:
                df_cleaned = self._clean_dataframe(table_data)
                html_table = df_cleaned.to_html(index=False, escape=False)
                
                return {
                    'table_id': f"{input_path.stem}_markdown_table",
                    'sheet_name': "Markdown_Table",
                    'data': df_cleaned,
                    'html': html_table,
                    'markdown': markdown_content,
                    'rows': len(df_cleaned),
                    'columns': list(df_cleaned.columns),
                    'extraction_method': 'docling_markdown'
                }
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Failed to process markdown table: {e}")
            return None
    
    def _convert_docling_data_to_dataframe(self, table_data) -> Any:
        """
        Convert docling table data to pandas DataFrame.
        
        Args:
            table_data: Docling table data structure
            
        Returns:
            Pandas DataFrame or None if conversion fails
        """
        try:
            import pandas as pd
            
            # Try different ways to extract data based on docling's structure
            if isinstance(table_data, list):
                # If it's a list of rows
                return pd.DataFrame(table_data)
            elif hasattr(table_data, 'to_dict'):
                # If it has a to_dict method
                return pd.DataFrame(table_data.to_dict())
            elif hasattr(table_data, 'rows') and hasattr(table_data, 'columns'):
                # If it has rows and columns attributes
                data = []
                for row in table_data.rows:
                    row_data = []
                    for cell in row:
                        row_data.append(str(cell) if cell is not None else '')
                    data.append(row_data)
                
                columns = [str(col) for col in table_data.columns] if table_data.columns else None
                return pd.DataFrame(data, columns=columns)
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Could not convert docling data to DataFrame: {e}")
            return None
    
    def _parse_markdown_table_to_dataframe(self, markdown_content: str) -> Any:
        """
        Parse markdown table content to pandas DataFrame.
        
        Args:
            markdown_content: Markdown content containing tables
            
        Returns:
            Pandas DataFrame or None if parsing fails
        """
        try:
            import pandas as pd
            import io
            
            # Find table in markdown (lines starting with |)
            lines = markdown_content.split('\n')
            table_lines = []
            in_table = False
            
            for line in lines:
                line = line.strip()
                if line.startswith('|') and line.endswith('|'):
                    # This looks like a table row
                    in_table = True
                    # Skip separator lines (contain only |, -, :, and spaces)
                    if not all(c in '|-: ' for c in line):
                        table_lines.append(line)
                elif in_table and line and not line.startswith('|'):
                    # End of table
                    break
            
            if len(table_lines) < 2:  # Need at least header and one row
                return None
            
            # Parse table rows
            rows = []
            for line in table_lines:
                # Remove leading/trailing |
                line = line.strip('|').strip()
                # Split by | and clean up
                row = [cell.strip() for cell in line.split('|')]
                rows.append(row)
            
            # First row is header
            if rows:
                headers = rows[0]
                data_rows = rows[1:]
                
                # Create DataFrame
                df = pd.DataFrame(data_rows, columns=headers)
                return df
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Could not parse markdown table: {e}")
            return None
    
    def _parse_html_table_to_dataframe(self, html_content: str) -> Any:
        """
        Parse HTML table content to pandas DataFrame.
        
        Args:
            html_content: HTML content containing tables
            
        Returns:
            Pandas DataFrame or None if parsing fails
        """
        try:
            import pandas as pd
            
            # Use pandas to read HTML tables
            dfs = pd.read_html(html_content)
            if dfs and len(dfs) > 0:
                return dfs[0]  # Return first table
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Could not parse HTML table: {e}")
            return None