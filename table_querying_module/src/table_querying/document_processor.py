"""
Document Processor module for handling document processing with table replacement.

This module handles the replacement of tables in documents with their generated descriptions,
creating modified versions of the original documents.
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Handles document processing and table replacement."""
    
    def __init__(self):
        """Initialize the DocumentProcessor."""
        logger.info("DocumentProcessor initialized")
    
    def replace_tables_with_descriptions(self, markdown_chunks: List[str], table_positions: List[int], 
                                       descriptions: List[Dict[str, Any]]) -> Tuple[List[str], Dict[str, Any]]:
        """
        Replace table chunks with their LLM-generated descriptions.
        
        Args:
            markdown_chunks: Original markdown chunks
            table_positions: Positions of tables in chunks
            descriptions: List of table description dictionaries
            
        Returns:
            Tuple of (modified_chunks, replacement_info)
        """
        modified_chunks = markdown_chunks.copy()
        replacement_info = {
            'total_replacements': 0,
            'successful_replacements': 0,
            'failed_replacements': 0,
            'replacement_details': []
        }
        
        # Create a mapping from table position to description
        position_to_description = {}
        for i, description_data in enumerate(descriptions):
            if i < len(table_positions) and description_data.get("status") == "success":
                table_pos = table_positions[i]
                table_id = description_data.get("table_id", i + 1)
                description = description_data.get("description", "No description available")
                
                position_to_description[table_pos] = {
                    "table_id": table_id,
                    "description": description,
                    "original_length": len(markdown_chunks[table_pos]) if table_pos < len(markdown_chunks) else 0
                }
        
        # Replace table chunks with their descriptions
        for table_pos, desc_data in position_to_description.items():
            if table_pos < len(modified_chunks):
                original_content = modified_chunks[table_pos]
                replacement_description = self._format_table_description(desc_data['description'], desc_data['table_id'])
                
                modified_chunks[table_pos] = replacement_description
                
                replacement_info['replacement_details'].append({
                    'position': table_pos,
                    'table_id': desc_data['table_id'],
                    'original_length': desc_data['original_length'],
                    'new_length': len(replacement_description),
                    'status': 'success'
                })
                
                replacement_info['successful_replacements'] += 1
                
                logger.info(f"Replaced table at position {table_pos} (Table ID {desc_data['table_id']}) "
                          f"with description ({desc_data['original_length']} -> {len(replacement_description)} chars)")
        
        replacement_info['total_replacements'] = len(position_to_description)
        replacement_info['failed_replacements'] = len(table_positions) - replacement_info['successful_replacements']
        
        logger.info(f"Completed table replacement: {replacement_info['successful_replacements']} successful, "
                   f"{replacement_info['failed_replacements']} failed")
        
        return modified_chunks, replacement_info
    
    def _format_table_description(self, description: str, table_id: int) -> str:
        """
        Format a table description for insertion into the document.
        
        Args:
            description: The LLM-generated description
            table_id: Table identifier
            
        Returns:
            Formatted description text
        """
        # Clean up the description and ensure it's well-formatted
        description = description.strip()
        
        # Add a header to identify this as a table description
        formatted_description = f"**Table {table_id} Summary:** {description}"
        
        return formatted_description
    
    def create_processed_document(self, original_markdown: str, modified_chunks: List[str]) -> str:
        """
        Create a processed document by joining the modified chunks.
        
        Args:
            original_markdown: Original markdown content
            modified_chunks: Modified chunks with table replacements
            
        Returns:
            Processed document content
        """
        # Join chunks with appropriate spacing
        processed_content = '\n\n'.join(modified_chunks)
        
        # Add a header indicating this is a processed version
        header = "<!-- This document has been processed with table descriptions -->\n\n"
        processed_content = header + processed_content
        
        logger.info(f"Created processed document: {len(original_markdown)} -> {len(processed_content)} characters")
        
        return processed_content
    
    def save_processed_document(self, content: str, output_path: str) -> bool:
        """
        Save the processed document to a file.
        
        Args:
            content: Processed document content
            output_path: Path to save the processed document
            
        Returns:
            True if successful, False otherwise
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Saved processed document to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save processed document to {output_path}: {e}")
            return False
    
    def create_replacement_report(self, replacement_info: Dict[str, Any]) -> str:
        """
        Create a detailed report of table replacements.
        
        Args:
            replacement_info: Information about table replacements
            
        Returns:
            Formatted report string
        """
        report = "TABLE REPLACEMENT REPORT\n"
        report += "=" * 40 + "\n\n"
        
        report += f"Total Replacements Attempted: {replacement_info['total_replacements']}\n"
        report += f"Successful Replacements: {replacement_info['successful_replacements']}\n"
        report += f"Failed Replacements: {replacement_info['failed_replacements']}\n\n"
        
        if replacement_info['replacement_details']:
            report += "REPLACEMENT DETAILS:\n"
            report += "-" * 20 + "\n"
            
            for detail in replacement_info['replacement_details']:
                report += f"Position {detail['position']} (Table {detail['table_id']}):\n"
                report += f"  Status: {detail['status']}\n"
                report += f"  Size change: {detail['original_length']} -> {detail['new_length']} characters\n"
                report += f"  Reduction: {detail['original_length'] - detail['new_length']} characters\n\n"
        
        return report
    
    def extract_table_references(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract references to table descriptions in the processed content.
        
        Args:
            content: Processed document content
            
        Returns:
            List of table reference information
        """
        # Pattern to match table description headers
        table_pattern = r'\*\*Table (\d+) Summary:\*\* (.+?)(?=\n\n|\*\*Table|\Z)'
        
        matches = re.finditer(table_pattern, content, re.DOTALL)
        
        references = []
        for match in matches:
            table_id = int(match.group(1))
            description = match.group(2).strip()
            start_pos = match.start()
            end_pos = match.end()
            
            references.append({
                'table_id': table_id,
                'description': description,
                'start_position': start_pos,
                'end_position': end_pos,
                'length': len(description)
            })
        
        logger.info(f"Found {len(references)} table references in processed content")
        return references