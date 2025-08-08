"""
Interface implementations for existing table processing components.

This module wraps the existing table processing components to implement
the new core interfaces, enabling migration to the new architecture.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    from ..core.interfaces import (
        DocumentProcessor as IDocumentProcessor,
        TableExtractor as ITableExtractor,
        SchemaGenerator as ISchemaGenerator, 
        TableDescriptor as ITableDescriptor,
        DatabaseClient as IDatabaseClient
    )
    from ..core.types import (
        Document, Table, Schema, Description, ProcessingResult, 
        ValidationResult, Query, QueryResult,
        DocumentFormat, TableFormat, DataType, ProcessingStatus
    )
    from ..core.exceptions import TableQueryingError, ValidationError
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from core.interfaces import (
        DocumentProcessor as IDocumentProcessor,
        TableExtractor as ITableExtractor,
        SchemaGenerator as ISchemaGenerator, 
        TableDescriptor as ITableDescriptor,
        DatabaseClient as IDatabaseClient
    )
    from core.types import (
        Document, Table, Schema, Description, ProcessingResult, 
        ValidationResult, Query, QueryResult,
        DocumentFormat, TableFormat, DataType, ProcessingStatus
    )
    from core.exceptions import TableQueryingError, ValidationError

# Import existing implementations
from .table_extractor import TableExtractor as LegacyTableExtractor
from .schema_processor import SchemaProcessor as LegacySchemaProcessor
from .table_summarizer import TableSummarizer as LegacyTableSummarizer
from .table_database import TableDatabase as LegacyTableDatabase
from .document_processor import DocumentProcessor as LegacyDocumentProcessor

logger = logging.getLogger(__name__)


class TableExtractorImpl(ITableExtractor):
    """TableExtractor implementation wrapping the legacy extractor."""
    
    def __init__(self, **config):
        self.extractor = LegacyTableExtractor()
        self.config = config
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def extract_tables(self, document: Document) -> List[Table]:
        """Extract tables from a document."""
        try:
            # Write document content to temp file if it's just content
            if document.source_path and document.source_path.exists():
                file_path = str(document.source_path)
            else:
                # Create temporary file
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                    f.write(document.content)
                    file_path = f.name
            
            # Extract using legacy extractor
            extraction_data = self.extractor.extract_from_file(file_path)
            html_tables = extraction_data.get('html_tables', [])
            
            # Convert to new Table format
            tables = []
            for i, html_table in enumerate(html_tables):
                table_id = f"{document.filename}_{i}"
                table = Table(
                    table_id=table_id,
                    content=str(html_table),
                    format=TableFormat.HTML,
                    position=i,
                    source_document=document.filename,
                    metadata={'extraction_method': 'legacy_extractor'}
                )
                tables.append(table)
            
            self._logger.info(f"Extracted {len(tables)} tables from {document.filename}")
            return tables
            
        except Exception as e:
            self._logger.error(f"Error extracting tables: {e}")
            raise TableQueryingError(f"Table extraction failed: {str(e)}", cause=e)
    
    def supported_formats(self) -> List[str]:
        """Get list of supported document formats."""
        return ['html']
    
    def validate_table(self, table: Table) -> ValidationResult:
        """Validate extracted table."""
        result = ValidationResult(valid=True)
        
        if not table.table_id:
            result.add_error("Table ID is required")
        
        if not table.content:
            result.add_error("Table content is empty")
        
        if table.format != TableFormat.HTML:
            result.add_warning("Only HTML format is fully supported")
        
        return result


class SchemaGeneratorImpl(ISchemaGenerator):
    """SchemaGenerator implementation wrapping the legacy schema processor."""
    
    def __init__(self, **config):
        self.schema_processor = LegacySchemaProcessor()
        self.config = config
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def generate_schema(self, table: Table) -> Schema:
        """Generate schema for a table."""
        try:
            # Convert Table to format expected by legacy processor
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(table.content, 'html.parser')
            html_table = soup.find('table')
            
            if not html_table:
                raise TableQueryingError("Invalid table content - no HTML table found")
            
            # Extract schema using legacy processor
            schemas = self.schema_processor.extract_schemas_from_tables([html_table])
            
            if not schemas or not schemas[0].get('success', False):
                raise TableQueryingError("Schema extraction failed")
            
            legacy_schema = schemas[0]
            
            # Convert to new Schema format
            columns = legacy_schema.get('columns', [])
            column_types = {}
            
            for col_name in columns:
                # Try to infer type from sample data
                col_type = self._infer_column_type(legacy_schema.get('sample_data', []), col_name)
                column_types[col_name] = col_type
            
            schema = Schema(
                table_id=table.table_id,
                columns=columns,
                column_types=column_types,
                row_count=legacy_schema.get('rows', 0),
                sample_data=legacy_schema.get('sample_data', []),
                metadata={
                    'extraction_method': 'legacy_processor',
                    'success': legacy_schema.get('success', False),
                    'dataframe_shape': legacy_schema.get('dataframe_shape')
                }
            )
            
            self._logger.info(f"Generated schema for table {table.table_id}")
            return schema
            
        except Exception as e:
            self._logger.error(f"Error generating schema: {e}")
            raise TableQueryingError(f"Schema generation failed: {str(e)}", cause=e)
    
    def generate_schemas(self, tables: List[Table]) -> List[Schema]:
        """Generate schemas for multiple tables."""
        schemas = []
        for table in tables:
            try:
                schema = self.generate_schema(table)
                schemas.append(schema)
            except Exception as e:
                self._logger.warning(f"Failed to generate schema for {table.table_id}: {e}")
                continue
        return schemas
    
    def infer_types(self, data: List[Dict[str, Any]]) -> Dict[str, str]:
        """Infer data types from sample data."""
        type_inference = {}
        
        if not data:
            return type_inference
        
        for column in data[0].keys():
            inferred_type = self._infer_column_type(data, column)
            type_inference[column] = inferred_type.value
        
        return type_inference
    
    def _infer_column_type(self, sample_data: List[Dict[str, Any]], column: str) -> DataType:
        """Infer data type for a column from sample data."""
        if not sample_data:
            return DataType.UNKNOWN
        
        values = [row.get(column) for row in sample_data if row.get(column) is not None]
        if not values:
            return DataType.UNKNOWN
        
        # Simple type inference logic
        for value in values[:5]:  # Check first 5 values
            str_value = str(value).strip()
            
            # Check for integers
            try:
                int(str_value)
                return DataType.INTEGER
            except ValueError:
                pass
            
            # Check for floats
            try:
                float(str_value)
                return DataType.FLOAT
            except ValueError:
                pass
            
            # Check for booleans
            if str_value.lower() in ['true', 'false', '1', '0']:
                return DataType.BOOLEAN
        
        return DataType.STRING


class TableDescriptorImpl(ITableDescriptor):
    """TableDescriptor implementation wrapping the legacy summarizer."""
    
    def __init__(self, llm_client=None, **config):
        self.llm_client = llm_client
        # Initialize legacy summarizer with config
        api_key = config.get('api_key')
        model_id = config.get('model_id', 'mistral-small')
        
        if not self.llm_client and api_key:
            self.summarizer = LegacyTableSummarizer(api_key=api_key, model_id=model_id)
        else:
            self.summarizer = None
        
        self.config = config
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def describe_table(self, schema: Schema, context: Optional[str] = None) -> Description:
        """Generate description for a table based on its schema."""
        try:
            if self.llm_client:
                # Use new LLM client interface
                return self.llm_client.generate_description(schema, context)
            elif self.summarizer:
                # Use legacy summarizer
                schema_dict = {
                    'table_id': schema.table_id,
                    'columns': schema.columns,
                    'rows': schema.row_count,
                    'sample_data': schema.sample_data,
                    'success': True
                }
                
                descriptions = self.summarizer.describe_multiple_tables([schema_dict], context)
                
                if descriptions and descriptions[0].get('status') == 'success':
                    desc_data = descriptions[0]
                    return Description(
                        table_id=schema.table_id,
                        content=desc_data.get('description', ''),
                        generated_by='legacy_summarizer',
                        generated_at=datetime.now(),
                        confidence=1.0,
                        metadata=desc_data
                    )
                else:
                    raise TableQueryingError("Description generation failed")
            else:
                raise TableQueryingError("No LLM client or summarizer configured")
                
        except Exception as e:
            self._logger.error(f"Error generating description: {e}")
            raise TableQueryingError(f"Description generation failed: {str(e)}", cause=e)
    
    def describe_tables(self, schemas: List[Schema], context: Optional[str] = None) -> List[Description]:
        """Generate descriptions for multiple tables."""
        descriptions = []
        for schema in schemas:
            try:
                description = self.describe_table(schema, context)
                descriptions.append(description)
            except Exception as e:
                self._logger.warning(f"Failed to generate description for {schema.table_id}: {e}")
                continue
        return descriptions
    
    def validate_description(self, description: Description) -> ValidationResult:
        """Validate generated description."""
        result = ValidationResult(valid=True)
        
        if not description.content or len(description.content.strip()) < 10:
            result.add_error("Description content is too short or empty")
        
        if not description.table_id:
            result.add_error("Description must have a table_id")
        
        if description.confidence < 0 or description.confidence > 1:
            result.add_warning("Confidence should be between 0 and 1")
        
        return result


class DatabaseClientImpl(IDatabaseClient):
    """DatabaseClient implementation wrapping the legacy database."""
    
    def __init__(self, **config):
        db_path = config.get('db_path', 'table_querying.db')
        self.database = LegacyTableDatabase(db_path=db_path)
        self.config = config
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def store_processing_result(self, result: ProcessingResult) -> bool:
        """Store complete processing result in database."""
        try:
            session_id = result.session_id or "default"
            
            # Convert ProcessingResult data to legacy format
            schemas_data = []
            descriptions_data = []
            html_tables = []
            
            for i, (table, schema, description) in enumerate(zip(result.tables, result.schemas, result.descriptions)):
                # Convert schema to legacy format
                schema_dict = {
                    'table_id': schema.table_id,
                    'columns': schema.columns,
                    'rows': schema.row_count,
                    'sample_data': schema.sample_data,
                    'success': True,
                    'dataframe': None  # Legacy field
                }
                schemas_data.append(schema_dict)
                
                # Convert description to legacy format
                desc_dict = {
                    'table_index': i,
                    'description': description.content,
                    'status': 'success'
                }
                descriptions_data.append(desc_dict)
                
                # Create mock HTML table object
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(table.content, 'html.parser')
                html_table = soup.find('table')
                html_tables.append(html_table)
            
            # Store using legacy method
            stored_count = self.database.store_multiple_tables(
                schemas_data, descriptions_data, session_id, 
                result.document.filename, html_tables
            )
            
            return stored_count > 0
            
        except Exception as e:
            self._logger.error(f"Error storing processing result: {e}")
            return False
    
    def get_table_by_id(self, table_id: str) -> Optional[Schema]:
        """Retrieve table schema by ID."""
        try:
            # Query legacy database - this might need custom SQL
            summary = self.database.get_database_summary()
            # This is a simplified implementation - you might need to add a method to legacy database
            return None  # Placeholder - implement based on your legacy database structure
            
        except Exception as e:
            self._logger.error(f"Error getting table {table_id}: {e}")
            return None
    
    def search_tables(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[Schema]:
        """Search for tables matching criteria."""
        try:
            # Use legacy search if available
            source_file = filters.get('source_file') if filters else None
            if source_file:
                tables = self.database.query_tables_by_source(source_file)
                # Convert to Schema objects - simplified implementation
                return []  # Placeholder
            return []
            
        except Exception as e:
            self._logger.error(f"Error searching tables: {e}")
            return []
    
    def execute_query(self, query: Query) -> QueryResult:
        """Execute a structured query against the database."""
        try:
            # This would need integration with your chat module
            return QueryResult(
                success=False,
                data=[],
                query=query,
                error_message="Query execution not implemented in legacy adapter"
            )
            
        except Exception as e:
            self._logger.error(f"Error executing query: {e}")
            return QueryResult(
                success=False,
                data=[],
                query=query,
                error_message=str(e)
            )
    
    def get_database_summary(self) -> Dict[str, Any]:
        """Get database statistics and summary."""
        try:
            return self.database.get_database_summary()
        except Exception as e:
            self._logger.error(f"Error getting database summary: {e}")
            return {"error": str(e)}
    
    def health_check(self) -> bool:
        """Check database health and connectivity."""
        try:
            # Simple health check - try to get summary
            summary = self.database.get_database_summary()
            return isinstance(summary, dict)
        except Exception:
            return False


class DocumentProcessorImpl(IDocumentProcessor):
    """DocumentProcessor implementation that orchestrates the complete pipeline."""
    
    def __init__(self, table_extractor=None, schema_generator=None, table_descriptor=None, database_client=None, **config):
        self.table_extractor = table_extractor or TableExtractorImpl(**config)
        self.schema_generator = schema_generator or SchemaGeneratorImpl(**config)
        self.table_descriptor = table_descriptor or TableDescriptorImpl(**config)
        self.database_client = database_client or DatabaseClientImpl(**config)
        
        # Legacy document processor for final document processing
        self.document_processor = LegacyDocumentProcessor()
        
        self.config = config
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def process_document(self, document: Document) -> ProcessingResult:
        """Process a complete document through the entire pipeline."""
        start_time = datetime.now()
        session_id = f"session_{int(start_time.timestamp())}"
        
        result = ProcessingResult(
            success=False,
            document=document,
            session_id=session_id,
            status=ProcessingStatus.IN_PROGRESS
        )
        
        try:
            self._logger.info(f"Starting document processing for {document.filename}")
            
            # Step 1: Extract tables
            tables = self.table_extractor.extract_tables(document)
            result.tables = tables
            self._logger.info(f"Extracted {len(tables)} tables")
            
            # Step 2: Generate schemas
            schemas = self.schema_generator.generate_schemas(tables)
            result.schemas = schemas
            self._logger.info(f"Generated {len(schemas)} schemas")
            
            # Step 3: Generate descriptions
            descriptions = self.table_descriptor.describe_tables(schemas)
            result.descriptions = descriptions
            self._logger.info(f"Generated {len(descriptions)} descriptions")
            
            # Step 4: Store in database
            stored = self.database_client.store_processing_result(result)
            if not stored:
                self._logger.warning("Failed to store processing result in database")
            
            # Calculate processing time
            end_time = datetime.now()
            result.processing_time = (end_time - start_time).total_seconds()
            result.success = True
            result.status = ProcessingStatus.COMPLETED
            
            self._logger.info(f"Document processing completed successfully in {result.processing_time:.2f}s")
            
        except Exception as e:
            self._logger.error(f"Document processing failed: {e}")
            result.error_message = str(e)
            result.status = ProcessingStatus.FAILED
            result.success = False
        
        return result
    
    def process_file(self, file_path: Path) -> ProcessingResult:
        """Process a file through the entire pipeline."""
        try:
            # Read file content
            content = file_path.read_text(encoding='utf-8')
            
            # Create document object
            document = Document(
                content=content,
                source_path=file_path,
                format=DocumentFormat.HTML if file_path.suffix.lower() == '.html' else DocumentFormat.MARKDOWN
            )
            
            return self.process_document(document)
            
        except Exception as e:
            self._logger.error(f"Error processing file {file_path}: {e}")
            # Return failed result
            document = Document(content="", source_path=file_path)
            return ProcessingResult(
                success=False,
                document=document,
                error_message=str(e),
                status=ProcessingStatus.FAILED
            )
    
    def validate_document(self, document: Document) -> ValidationResult:
        """Validate document format and content."""
        result = ValidationResult(valid=True)
        
        if not document.content or len(document.content.strip()) < 10:
            result.add_error("Document content is empty or too short")
        
        if document.format == DocumentFormat.HTML:
            # Basic HTML validation
            if '<table' not in document.content.lower():
                result.add_warning("No HTML tables found in document")
        
        return result