"""
Unit tests for interface implementations.

Tests the concrete implementations of core interfaces that wrap legacy components.
"""

import unittest
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path
import tempfile
import os
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'table_querying_module' / 'src'))

from core.types import (
    Document, Table, Schema, Description, ProcessingResult,
    ValidationResult, DocumentFormat, TableFormat, DataType
)
from core.exceptions import TableQueryingError


class TestTableExtractorImpl(unittest.TestCase):
    """Test TableExtractor implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock the legacy extractor to avoid dependency issues
        self.mock_legacy_extractor = Mock()
        
        with patch('table_querying.interface_implementations.LegacyTableExtractor', return_value=self.mock_legacy_extractor):
            from table_querying.interface_implementations import TableExtractorImpl
            self.extractor = TableExtractorImpl()
    
    def test_extract_tables_from_document(self):
        """Test table extraction from document."""
        # Setup mock response
        mock_html_table = Mock()
        mock_html_table.__str__ = lambda: '<table><tr><td>Test</td></tr></table>'
        
        self.mock_legacy_extractor.extract_from_file.return_value = {
            'html_tables': [mock_html_table, mock_html_table]
        }
        
        # Create test document
        document = Document(
            content='<html><body><table><tr><td>Test</td></tr></table></body></html>',
            format=DocumentFormat.HTML
        )
        
        # Extract tables
        tables = self.extractor.extract_tables(document)
        
        # Verify results
        self.assertEqual(len(tables), 2)
        self.assertIsInstance(tables[0], Table)
        self.assertEqual(tables[0].format, TableFormat.HTML)
        self.assertEqual(tables[0].position, 0)
        self.assertEqual(tables[1].position, 1)
        self.assertEqual(tables[0].source_document, document.filename)
    
    def test_supported_formats(self):
        """Test supported formats method."""
        formats = self.extractor.supported_formats()
        self.assertIsInstance(formats, list)
        self.assertIn('html', formats)
    
    def test_validate_table(self):
        """Test table validation."""
        # Valid table
        valid_table = Table(
            table_id="test_table",
            content="<table><tr><td>Test</td></tr></table>",
            format=TableFormat.HTML
        )
        
        validation = self.extractor.validate_table(valid_table)
        self.assertTrue(validation.valid)
        
        # Invalid table (no ID)
        invalid_table = Table(
            table_id="",
            content="<table><tr><td>Test</td></tr></table>",
            format=TableFormat.HTML
        )
        
        validation = self.extractor.validate_table(invalid_table)
        self.assertFalse(validation.valid)
        self.assertTrue(any("Table ID is required" in error for error in validation.errors))
    
    def test_extraction_error_handling(self):
        """Test error handling during extraction."""
        self.mock_legacy_extractor.extract_from_file.side_effect = Exception("Mock extraction error")
        
        document = Document(
            content='<html><body></body></html>',
            format=DocumentFormat.HTML
        )
        
        with self.assertRaises(TableQueryingError):
            self.extractor.extract_tables(document)


class TestSchemaGeneratorImpl(unittest.TestCase):
    """Test SchemaGenerator implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_legacy_processor = Mock()
        
        with patch('table_querying.interface_implementations.LegacySchemaProcessor', return_value=self.mock_legacy_processor):
            from table_querying.interface_implementations import SchemaGeneratorImpl
            self.generator = SchemaGeneratorImpl()
    
    def test_generate_schema(self):
        """Test schema generation for a single table."""
        # Setup mock response
        mock_schema_data = {
            'success': True,
            'columns': ['name', 'age', 'city'],
            'rows': 10,
            'sample_data': [
                {'name': 'John', 'age': '25', 'city': 'NYC'},
                {'name': 'Jane', 'age': '30', 'city': 'LA'}
            ],
            'dataframe_shape': (10, 3)
        }
        
        self.mock_legacy_processor.extract_schemas_from_tables.return_value = [mock_schema_data]
        
        # Create test table
        table = Table(
            table_id="test_table",
            content='<table><tr><th>name</th><th>age</th><th>city</th></tr><tr><td>John</td><td>25</td><td>NYC</td></tr></table>',
            format=TableFormat.HTML
        )
        
        # Generate schema
        schema = self.generator.generate_schema(table)
        
        # Verify results
        self.assertIsInstance(schema, Schema)
        self.assertEqual(schema.table_id, "test_table")
        self.assertEqual(schema.columns, ['name', 'age', 'city'])
        self.assertEqual(schema.row_count, 10)
        self.assertEqual(len(schema.sample_data), 2)
        self.assertIn('name', schema.column_types)
    
    def test_generate_schemas_multiple(self):
        """Test schema generation for multiple tables."""
        # Setup mock responses
        mock_schemas = [
            {'success': True, 'columns': ['col1'], 'rows': 5, 'sample_data': []},
            {'success': True, 'columns': ['col2'], 'rows': 3, 'sample_data': []}
        ]
        
        self.mock_legacy_processor.extract_schemas_from_tables.side_effect = [
            [mock_schemas[0]], [mock_schemas[1]]
        ]
        
        # Create test tables
        tables = [
            Table(table_id="table1", content='<table><tr><td>data1</td></tr></table>', format=TableFormat.HTML),
            Table(table_id="table2", content='<table><tr><td>data2</td></tr></table>', format=TableFormat.HTML)
        ]
        
        # Generate schemas
        schemas = self.generator.generate_schemas(tables)
        
        # Verify results
        self.assertEqual(len(schemas), 2)
        self.assertEqual(schemas[0].table_id, "table1")
        self.assertEqual(schemas[1].table_id, "table2")
    
    def test_type_inference(self):
        """Test data type inference."""
        sample_data = [
            {'name': 'John', 'age': '25', 'salary': '50000.50', 'active': 'true'},
            {'name': 'Jane', 'age': '30', 'salary': '60000.75', 'active': 'false'}
        ]
        
        type_inference = self.generator.infer_types(sample_data)
        
        self.assertEqual(type_inference['name'], DataType.STRING.value)
        self.assertEqual(type_inference['age'], DataType.INTEGER.value)
        self.assertEqual(type_inference['salary'], DataType.FLOAT.value)
        self.assertEqual(type_inference['active'], DataType.BOOLEAN.value)
    
    def test_schema_generation_failure(self):
        """Test handling of schema generation failures."""
        self.mock_legacy_processor.extract_schemas_from_tables.return_value = [
            {'success': False}
        ]
        
        table = Table(
            table_id="test_table",
            content='<table><tr><td>invalid</td></tr></table>',
            format=TableFormat.HTML
        )
        
        with self.assertRaises(TableQueryingError):
            self.generator.generate_schema(table)


class TestTableDescriptorImpl(unittest.TestCase):
    """Test TableDescriptor implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_legacy_summarizer = Mock()
        
        with patch('table_querying.interface_implementations.LegacyTableSummarizer', return_value=self.mock_legacy_summarizer):
            from table_querying.interface_implementations import TableDescriptorImpl
            self.descriptor = TableDescriptorImpl(api_key="test_key")
    
    def test_describe_table(self):
        """Test table description generation."""
        # Setup mock response
        mock_description_data = {
            'status': 'success',
            'description': 'This table contains employee information including names, ages, and cities.',
            'confidence': 0.95
        }
        
        self.mock_legacy_summarizer.describe_multiple_tables.return_value = [mock_description_data]
        
        # Create test schema
        schema = Schema(
            table_id="test_table",
            columns=['name', 'age', 'city'],
            column_types={'name': DataType.STRING, 'age': DataType.INTEGER, 'city': DataType.STRING},
            row_count=10,
            sample_data=[{'name': 'John', 'age': '25', 'city': 'NYC'}]
        )
        
        # Generate description
        description = self.descriptor.describe_table(schema, context="Employee database")
        
        # Verify results
        self.assertIsInstance(description, Description)
        self.assertEqual(description.table_id, "test_table")
        self.assertIn("employee information", description.content.lower())
        self.assertEqual(description.generated_by, "legacy_summarizer")
        self.assertIsInstance(description.generated_at, datetime)
    
    def test_describe_tables_multiple(self):
        """Test description generation for multiple tables."""
        mock_descriptions = [
            {'status': 'success', 'description': 'Table 1 description'},
            {'status': 'success', 'description': 'Table 2 description'}
        ]
        
        self.mock_legacy_summarizer.describe_multiple_tables.side_effect = [
            [mock_descriptions[0]], [mock_descriptions[1]]
        ]
        
        schemas = [
            Schema(table_id="table1", columns=['col1'], column_types={'col1': DataType.STRING}, row_count=5),
            Schema(table_id="table2", columns=['col2'], column_types={'col2': DataType.STRING}, row_count=3)
        ]
        
        descriptions = self.descriptor.describe_tables(schemas)
        
        self.assertEqual(len(descriptions), 2)
        self.assertEqual(descriptions[0].table_id, "table1")
        self.assertEqual(descriptions[1].table_id, "table2")
    
    def test_validate_description(self):
        """Test description validation."""
        # Valid description
        valid_desc = Description(
            table_id="test_table",
            content="This is a detailed description of the table with sufficient length.",
            generated_by="test_system",
            confidence=0.8
        )
        
        validation = self.descriptor.validate_description(valid_desc)
        self.assertTrue(validation.valid)
        
        # Invalid description (too short)
        invalid_desc = Description(
            table_id="test_table",
            content="Short",
            generated_by="test_system",
            confidence=0.8
        )
        
        validation = self.descriptor.validate_description(invalid_desc)
        self.assertFalse(validation.valid)
    
    def test_description_without_api_key(self):
        """Test descriptor behavior without API key."""
        with patch('table_querying.interface_implementations.LegacyTableSummarizer') as MockSummarizer:
            from table_querying.interface_implementations import TableDescriptorImpl
            descriptor = TableDescriptorImpl()  # No API key
            
            schema = Schema(
                table_id="test_table",
                columns=['col1'],
                column_types={'col1': DataType.STRING},
                row_count=5
            )
            
            with self.assertRaises(TableQueryingError):
                descriptor.describe_table(schema)


class TestDatabaseClientImpl(unittest.TestCase):
    """Test DatabaseClient implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_legacy_database = Mock()
        
        with patch('table_querying.interface_implementations.LegacyTableDatabase', return_value=self.mock_legacy_database):
            from table_querying.interface_implementations import DatabaseClientImpl
            self.client = DatabaseClientImpl(db_path=":memory:")
    
    def test_store_processing_result(self):
        """Test storing processing results."""
        self.mock_legacy_database.store_multiple_tables.return_value = 2
        
        # Create test processing result
        document = Document(content="<html></html>", format=DocumentFormat.HTML)
        tables = [
            Table(table_id="t1", content="<table></table>", format=TableFormat.HTML),
            Table(table_id="t2", content="<table></table>", format=TableFormat.HTML)
        ]
        schemas = [
            Schema(table_id="t1", columns=['col1'], column_types={'col1': DataType.STRING}, row_count=5),
            Schema(table_id="t2", columns=['col2'], column_types={'col2': DataType.INTEGER}, row_count=3)
        ]
        descriptions = [
            Description(table_id="t1", content="Description 1", generated_by="test"),
            Description(table_id="t2", content="Description 2", generated_by="test")
        ]
        
        result = ProcessingResult(
            success=True,
            document=document,
            tables=tables,
            schemas=schemas,
            descriptions=descriptions,
            session_id="test_session"
        )
        
        # Store result
        stored = self.client.store_processing_result(result)
        
        # Verify
        self.assertTrue(stored)
        self.mock_legacy_database.store_multiple_tables.assert_called_once()
    
    def test_get_database_summary(self):
        """Test getting database summary."""
        mock_summary = {
            'total_tables': 10,
            'total_sessions': 3,
            'database_size': '2.5MB'
        }
        
        self.mock_legacy_database.get_database_summary.return_value = mock_summary
        
        summary = self.client.get_database_summary()
        
        self.assertEqual(summary, mock_summary)
    
    def test_health_check(self):
        """Test database health check."""
        self.mock_legacy_database.get_database_summary.return_value = {'status': 'healthy'}
        
        health = self.client.health_check()
        
        self.assertTrue(health)
        
        # Test unhealthy database
        self.mock_legacy_database.get_database_summary.side_effect = Exception("Database error")
        
        health = self.client.health_check()
        
        self.assertFalse(health)


class TestDocumentProcessorImpl(unittest.TestCase):
    """Test DocumentProcessor implementation."""
    
    def setUp(self):
        """Set up test fixtures with mocked dependencies."""
        self.mock_extractor = Mock()
        self.mock_schema_generator = Mock()
        self.mock_descriptor = Mock()
        self.mock_database = Mock()
        
        with patch('table_querying.interface_implementations.LegacyDocumentProcessor'):
            from table_querying.interface_implementations import DocumentProcessorImpl
            
            self.processor = DocumentProcessorImpl(
                table_extractor=self.mock_extractor,
                schema_generator=self.mock_schema_generator,
                table_descriptor=self.mock_descriptor,
                database_client=self.mock_database
            )
    
    def test_process_document(self):
        """Test complete document processing pipeline."""
        # Setup mocks
        mock_tables = [
            Table(table_id="t1", content="<table></table>", format=TableFormat.HTML)
        ]
        mock_schemas = [
            Schema(table_id="t1", columns=['col1'], column_types={'col1': DataType.STRING}, row_count=5)
        ]
        mock_descriptions = [
            Description(table_id="t1", content="Test description", generated_by="test")
        ]
        
        self.mock_extractor.extract_tables.return_value = mock_tables
        self.mock_schema_generator.generate_schemas.return_value = mock_schemas
        self.mock_descriptor.describe_tables.return_value = mock_descriptions
        self.mock_database.store_processing_result.return_value = True
        
        # Create test document
        document = Document(
            content='<html><body><table><tr><td>Test</td></tr></table></body></html>',
            format=DocumentFormat.HTML
        )
        
        # Process document
        result = self.processor.process_document(document)
        
        # Verify results
        self.assertIsInstance(result, ProcessingResult)
        self.assertTrue(result.success)
        self.assertEqual(len(result.tables), 1)
        self.assertEqual(len(result.schemas), 1)
        self.assertEqual(len(result.descriptions), 1)
        self.assertIsNotNone(result.session_id)
        
        # Verify all components were called
        self.mock_extractor.extract_tables.assert_called_once_with(document)
        self.mock_schema_generator.generate_schemas.assert_called_once_with(mock_tables)
        self.mock_descriptor.describe_tables.assert_called_once_with(mock_schemas)
        self.mock_database.store_processing_result.assert_called_once()
    
    def test_process_file(self):
        """Test processing a file through the pipeline."""
        # Create temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write('<html><body><table><tr><td>Test</td></tr></table></body></html>')
            temp_path = f.name
        
        try:
            # Setup mocks for successful processing
            self.mock_extractor.extract_tables.return_value = []
            self.mock_schema_generator.generate_schemas.return_value = []
            self.mock_descriptor.describe_tables.return_value = []
            self.mock_database.store_processing_result.return_value = True
            
            # Process file
            result = self.processor.process_file(Path(temp_path))
            
            # Verify
            self.assertIsInstance(result, ProcessingResult)
            self.assertTrue(result.success)
            self.assertEqual(result.document.format, DocumentFormat.HTML)
            
        finally:
            os.unlink(temp_path)
    
    def test_process_document_with_error(self):
        """Test document processing with errors."""
        self.mock_extractor.extract_tables.side_effect = Exception("Extraction failed")
        
        document = Document(
            content='<html><body></body></html>',
            format=DocumentFormat.HTML
        )
        
        result = self.processor.process_document(document)
        
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error_message)
        self.assertIn("Extraction failed", result.error_message)
    
    def test_validate_document(self):
        """Test document validation."""
        # Valid HTML document
        valid_doc = Document(
            content='<html><body><table><tr><td>Test</td></tr></table></body></html>',
            format=DocumentFormat.HTML
        )
        
        validation = self.processor.validate_document(valid_doc)
        self.assertTrue(validation.valid)
        
        # Invalid document (empty content)
        invalid_doc = Document(
            content='',
            format=DocumentFormat.HTML
        )
        
        validation = self.processor.validate_document(invalid_doc)
        self.assertFalse(validation.valid)
        
        # HTML document without tables
        no_tables_doc = Document(
            content='<html><body><p>No tables here</p></body></html>',
            format=DocumentFormat.HTML
        )
        
        validation = self.processor.validate_document(no_tables_doc)
        self.assertTrue(validation.valid)  # Valid but with warning
        self.assertTrue(len(validation.warnings) > 0)


if __name__ == '__main__':
    # Run tests with more verbose output
    unittest.main(verbosity=2)