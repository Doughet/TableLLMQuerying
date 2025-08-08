"""
Main Table Processor module that orchestrates the complete table processing workflow.

This is the main interface for the table querying module that coordinates all components:
extraction, schema processing, LLM summarization, database storage, and document processing.
"""

import os
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

try:
    from .table_extractor import TableExtractor
    from .schema_processor import SchemaProcessor
    from .table_summarizer import TableSummarizer
    from .table_database import TableDatabase
    from .document_processor import DocumentProcessor
except ImportError:
    from table_extractor import TableExtractor
    from schema_processor import SchemaProcessor
    from table_summarizer import TableSummarizer
    from table_database import TableDatabase
    from document_processor import DocumentProcessor

logger = logging.getLogger(__name__)


class TableProcessor:
    """
    Main class that orchestrates the complete table processing workflow.
    
    This class provides a high-level interface for processing HTML documents containing tables:
    1. Extract tables from HTML document
    2. Generate flattened schemas for each table
    3. Create LLM descriptions of tables
    4. Store everything in a database
    5. Replace tables in document with descriptions
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the TableProcessor with all required components.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        # Initialize all components
        self.extractor = TableExtractor()
        self.schema_processor = SchemaProcessor()
        self.summarizer = TableSummarizer(
            api_key=self.config.get('api_key'),
            model_id=self.config.get('model_id', 'mistral-small')
        )
        self.database = TableDatabase(
            db_path=self.config.get('db_path', 'table_querying.db')
        )
        self.document_processor = DocumentProcessor()
        
        # Configuration options
        self.save_outputs = self.config.get('save_outputs', True)
        self.output_dir = Path(self.config.get('output_dir', 'table_querying_outputs'))
        self.clear_database_on_start = self.config.get('clear_database_on_start', False)
        self.context_hint = self.config.get('context_hint', None)
        
        # Create output directory if it doesn't exist
        if self.save_outputs:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Clear database if requested
        if self.clear_database_on_start:
            self.database.clear_database()
            logger.info("Database cleared on startup")
        
        logger.info("TableProcessor initialized successfully")
    
    def process_document(self, html_file_path: str) -> Dict[str, Any]:
        """
        Process a complete HTML document with tables.
        
        This is the main entry point that performs the complete workflow:
        1. Extract tables and convert to markdown
        2. Generate schemas for all tables
        3. Create LLM descriptions
        4. Store in database
        5. Create processed document with table replacements
        
        Args:
            html_file_path: Path to the HTML file to process
            
        Returns:
            Dictionary containing all processing results and outputs
        """
        logger.info(f"Starting document processing for: {html_file_path}")
        
        # Initialize results structure
        results = {
            'success': False,
            'html_file': html_file_path,
            'source_file': str(Path(html_file_path)),
            'session_id': None,
            'extraction_results': {},
            'schema_results': {},
            'description_results': {},
            'database_results': {},
            'document_processing_results': {},
            'output_files': {},
            'error': None,
            'statistics': {}
        }
        
        try:
            # Step 1: Start processing session
            session_id = self.database.start_processing_session(html_file_path)
            results['session_id'] = session_id
            
            # Step 2: Extract tables and markdown
            logger.info("Step 1/5: Extracting tables and markdown content")
            extraction_data = self.extractor.extract_from_file(html_file_path)
            results['extraction_results'] = {
                'html_tables_count': len(extraction_data['html_tables']),
                'markdown_chunks_count': len(extraction_data['markdown_chunks']),
                'markdown_length': len(extraction_data['markdown_content'])
            }
            
            # Step 3: Generate schemas for all tables
            logger.info("Step 2/5: Generating flattened schemas for tables")
            schemas = self.schema_processor.extract_schemas_from_tables(extraction_data['html_tables'])
            successful_schemas = sum(1 for schema in schemas if schema.get("success", False))
            results['schema_results'] = {
                'total_schemas': len(schemas),
                'successful_schemas': successful_schemas,
                'failed_schemas': len(schemas) - successful_schemas
            }
            
            # Step 4: Generate LLM descriptions
            logger.info("Step 3/5: Generating LLM descriptions for tables")
            descriptions = self.summarizer.describe_multiple_tables(schemas, self.context_hint)
            successful_descriptions = sum(1 for desc in descriptions if desc.get("status") == "success")
            results['description_results'] = {
                'total_descriptions': len(descriptions),
                'successful_descriptions': successful_descriptions,
                'failed_descriptions': len(descriptions) - successful_descriptions
            }
            
            # Step 5: Store in database
            logger.info("Step 4/5: Storing tables and metadata in database")
            stored_count = self.database.store_multiple_tables(
                schemas, descriptions, session_id, html_file_path, extraction_data['html_tables']
            )
            results['database_results'] = {
                'stored_tables': stored_count,
                'session_id': session_id
            }
            
            # Step 6: Process document with table replacements
            logger.info("Step 5/5: Creating processed document with table replacements")
            table_positions = self.extractor.identify_table_chunks(extraction_data['markdown_chunks'])
            modified_chunks, replacement_info = self.document_processor.replace_tables_with_descriptions(
                extraction_data['markdown_chunks'], table_positions, descriptions
            )
            
            # Create processed document
            processed_content = self.document_processor.create_processed_document(
                extraction_data['markdown_content'], modified_chunks
            )
            
            results['document_processing_results'] = {
                'table_positions': table_positions,
                'replacement_info': replacement_info,
                'processed_content_length': len(processed_content),
                'original_content_length': len(extraction_data['markdown_content'])
            }
            
            # Step 7: Save outputs if requested
            if self.save_outputs:
                output_files = self._save_all_outputs(
                    extraction_data, schemas, descriptions, processed_content, 
                    replacement_info, html_file_path
                )
                results['output_files'] = output_files
            
            # Calculate final statistics
            results['statistics'] = self._calculate_statistics(results)
            results['success'] = True
            
            logger.info(f"Document processing completed successfully for {html_file_path}")
            logger.info(f"Processed {successful_schemas} tables with {successful_descriptions} descriptions")
            
            return results
            
        except Exception as e:
            error_msg = f"Document processing failed: {str(e)}"
            logger.error(error_msg)
            results['error'] = error_msg
            results['success'] = False
            return results
    
    def _save_all_outputs(self, extraction_data: Dict, schemas: List, descriptions: List, 
                         processed_content: str, replacement_info: Dict, html_file_path: str) -> Dict[str, str]:
        """Save all outputs to files."""
        base_name = Path(html_file_path).stem
        output_files = {}
        
        try:
            # Save processed document
            processed_doc_path = self.output_dir / f"{base_name}_processed.md"
            if self.document_processor.save_processed_document(processed_content, str(processed_doc_path)):
                output_files['processed_document'] = str(processed_doc_path)
            
            # Save original markdown
            markdown_path = self.output_dir / f"{base_name}_original.md"
            with open(markdown_path, 'w', encoding='utf-8') as f:
                f.write(extraction_data['markdown_content'])
            output_files['original_markdown'] = str(markdown_path)
            
            # Save schemas
            import json
            schemas_path = self.output_dir / f"{base_name}_schemas.json"
            with open(schemas_path, 'w', encoding='utf-8') as f:
                # Remove dataframe from schemas for JSON serialization
                serializable_schemas = []
                for schema in schemas:
                    schema_copy = schema.copy()
                    if 'dataframe' in schema_copy:
                        del schema_copy['dataframe']
                    serializable_schemas.append(schema_copy)
                json.dump(serializable_schemas, f, indent=2, ensure_ascii=False)
            output_files['schemas'] = str(schemas_path)
            
            # Save descriptions
            descriptions_path = self.output_dir / f"{base_name}_descriptions.json"
            with open(descriptions_path, 'w', encoding='utf-8') as f:
                # Remove schema data for JSON serialization
                serializable_descriptions = []
                for desc in descriptions:
                    desc_copy = desc.copy()
                    if 'schema' in desc_copy and 'dataframe' in desc_copy['schema']:
                        desc_copy['schema'] = {k: v for k, v in desc_copy['schema'].items() if k != 'dataframe'}
                    serializable_descriptions.append(desc_copy)
                json.dump(serializable_descriptions, f, indent=2, ensure_ascii=False)
            output_files['descriptions'] = str(descriptions_path)
            
            # Save replacement report
            report_path = self.output_dir / f"{base_name}_replacement_report.txt"
            report = self.document_processor.create_replacement_report(replacement_info)
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            output_files['replacement_report'] = str(report_path)
            
            logger.info(f"Saved all outputs to {self.output_dir}")
            
        except Exception as e:
            logger.error(f"Failed to save some outputs: {e}")
        
        return output_files
    
    def _calculate_statistics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate processing statistics."""
        stats = {}
        
        # Extraction stats
        extraction = results.get('extraction_results', {})
        stats['html_tables'] = extraction.get('html_tables_count', 0)
        stats['markdown_chunks'] = extraction.get('markdown_chunks_count', 0)
        stats['markdown_length'] = extraction.get('markdown_length', 0)
        
        # Schema processing stats
        schema_results = results.get('schema_results', {})
        stats['successful_schemas'] = schema_results.get('successful_schemas', 0)
        stats['total_schemas'] = schema_results.get('total_schemas', 0)
        stats['schema_success_rate'] = (
            stats['successful_schemas'] / stats['total_schemas'] * 100 
            if stats['total_schemas'] > 0 else 0
        )
        
        # Description stats
        desc_results = results.get('description_results', {})
        stats['successful_descriptions'] = desc_results.get('successful_descriptions', 0)
        stats['total_descriptions'] = desc_results.get('total_descriptions', 0)
        stats['description_success_rate'] = (
            stats['successful_descriptions'] / stats['total_descriptions'] * 100
            if stats['total_descriptions'] > 0 else 0
        )
        
        # Database stats
        db_results = results.get('database_results', {})
        stats['stored_tables'] = db_results.get('stored_tables', 0)
        
        # Document processing stats
        doc_results = results.get('document_processing_results', {})
        replacement_info = doc_results.get('replacement_info', {})
        stats['table_replacements'] = replacement_info.get('successful_replacements', 0)
        stats['original_content_length'] = doc_results.get('original_content_length', 0)
        stats['processed_content_length'] = doc_results.get('processed_content_length', 0)
        stats['content_size_change'] = stats['processed_content_length'] - stats['original_content_length']
        
        return stats
    
    def get_database_summary(self) -> Dict[str, Any]:
        """Get a summary of the current database contents."""
        return self.database.get_database_summary()
    
    def query_tables_by_source(self, source_file: str) -> List[Dict[str, Any]]:
        """Query all tables from a specific source file."""
        return self.database.query_tables_by_source(source_file)
    
    def clear_database(self):
        """Clear all data from the database."""
        self.database.clear_database()
        logger.info("Database cleared")
    
    def print_processing_summary(self, results: Dict[str, Any]):
        """Print a formatted summary of processing results."""
        if not results.get('success', False):
            print(f"❌ Processing failed: {results.get('error', 'Unknown error')}")
            return
        
        stats = results.get('statistics', {})
        
        print("\n" + "="*60)
        print("TABLE PROCESSING SUMMARY")
        print("="*60)
        print(f"📄 Source File: {Path(results['html_file']).name}")
        print(f"🆔 Session ID: {results['session_id']}")
        print(f"\n📊 EXTRACTION RESULTS:")
        print(f"  • HTML Tables Found: {stats.get('html_tables', 0)}")
        print(f"  • Markdown Chunks: {stats.get('markdown_chunks', 0)}")
        print(f"  • Content Length: {stats.get('markdown_length', 0):,} characters")
        
        print(f"\n🔍 SCHEMA PROCESSING:")
        print(f"  • Successful Schemas: {stats.get('successful_schemas', 0)}/{stats.get('total_schemas', 0)}")
        print(f"  • Success Rate: {stats.get('schema_success_rate', 0):.1f}%")
        
        print(f"\n🤖 LLM DESCRIPTIONS:")
        print(f"  • Successful Descriptions: {stats.get('successful_descriptions', 0)}/{stats.get('total_descriptions', 0)}")
        print(f"  • Success Rate: {stats.get('description_success_rate', 0):.1f}%")
        
        print(f"\n💾 DATABASE STORAGE:")
        print(f"  • Tables Stored: {stats.get('stored_tables', 0)}")
        
        print(f"\n📝 DOCUMENT PROCESSING:")
        print(f"  • Table Replacements: {stats.get('table_replacements', 0)}")
        print(f"  • Content Size Change: {stats.get('content_size_change', 0):+,} characters")
        print(f"  • Final Size: {stats.get('processed_content_length', 0):,} characters")
        
        if results.get('output_files'):
            print(f"\n📁 OUTPUT FILES:")
            for file_type, file_path in results['output_files'].items():
                print(f"  • {file_type}: {file_path}")
        
        print("="*60)
        print("✅ Processing completed successfully!")
        print("="*60)