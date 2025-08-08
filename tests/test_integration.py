"""
Integration tests for the complete table processing system.

Tests end-to-end workflows and system integration.
"""

import unittest
import pytest
from pathlib import Path
import tempfile
import os
import sys
import json
from unittest.mock import Mock, patch

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'table_querying_module' / 'src'))


class TestEndToEndIntegration(unittest.TestCase):
    """Test complete end-to-end workflows."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_html_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Test Document</title></head>
        <body>
            <h1>Employee Data</h1>
            <table border="1">
                <tr><th>Name</th><th>Department</th><th>Salary</th><th>Years</th></tr>
                <tr><td>John Doe</td><td>Engineering</td><td>75000</td><td>3</td></tr>
                <tr><td>Jane Smith</td><td>Marketing</td><td>65000</td><td>2</td></tr>
                <tr><td>Bob Wilson</td><td>Sales</td><td>55000</td><td>1</td></tr>
            </table>
            
            <h2>Product Catalog</h2>
            <table border="1">
                <tr><th>Product</th><th>Price</th><th>Stock</th><th>Category</th></tr>
                <tr><td>Laptop</td><td>999.99</td><td>15</td><td>Electronics</td></tr>
                <tr><td>Mouse</td><td>25.99</td><td>100</td><td>Electronics</td></tr>
            </table>
        </body>
        </html>
        """
    
    def create_test_html_file(self) -> str:
        """Create a temporary HTML file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(self.test_html_content)
            return f.name
    
    def test_architecture_comparison(self):
        """Test that both architectures can process the same document."""
        html_file = self.create_test_html_file()
        
        try:
            from table_querying.table_processor_factory import TableProcessorFactory
            
            # Test configuration (no API key for basic processing)
            config = {
                'api_key': None,
                'db_path': ':memory:',
                'save_outputs': False,
                'debug': True
            }
            
            # Test interface architecture
            try:
                interface_processor = TableProcessorFactory.create_processor(
                    config, architecture='interface'
                )
                self.assertIsNotNone(interface_processor)
                
                # Get component info
                component_info = interface_processor.get_component_info()
                self.assertIn('architecture_version', component_info)
                self.assertIn('Interface-based', component_info['architecture_version'])
                
            except Exception as e:
                self.fail(f"Interface architecture failed to initialize: {e}")
            
            # Test legacy architecture
            try:
                legacy_processor = TableProcessorFactory.create_processor(
                    config, architecture='legacy'
                )
                self.assertIsNotNone(legacy_processor)
                
            except Exception as e:
                self.fail(f"Legacy architecture failed to initialize: {e}")
                
        finally:
            os.unlink(html_file)
    
    def test_factory_auto_selection(self):
        """Test automatic architecture selection."""
        from table_querying.table_processor_factory import TableProcessorFactory
        
        config = {
            'api_key': None,
            'db_path': ':memory:',
            'save_outputs': False
        }
        
        # Test auto selection (should default to interface)
        processor = TableProcessorFactory.create_processor(config, architecture='auto')
        
        self.assertIsNotNone(processor)
        
        # Check if it's the interface version by looking for get_component_info method
        has_component_info = hasattr(processor, 'get_component_info')
        self.assertTrue(has_component_info, "Auto selection should choose interface architecture")
    
    @patch('table_querying.interface_implementations.LegacyTableExtractor')
    @patch('table_querying.interface_implementations.LegacySchemaProcessor')
    def test_interface_implementation_integration(self, mock_schema_processor, mock_extractor):
        """Test integration of interface implementations."""
        from table_querying.interface_implementations import (
            TableExtractorImpl, SchemaGeneratorImpl
        )
        from core.types import Document, DocumentFormat, DataType
        
        # Setup mocks
        mock_html_table = Mock()
        mock_html_table.__str__ = lambda: '<table><tr><td>Test</td></tr></table>'
        
        mock_extractor_instance = Mock()
        mock_extractor_instance.extract_from_file.return_value = {
            'html_tables': [mock_html_table]
        }
        mock_extractor.return_value = mock_extractor_instance
        
        mock_processor_instance = Mock()
        mock_processor_instance.extract_schemas_from_tables.return_value = [{
            'success': True,
            'columns': ['name', 'age'],
            'rows': 5,
            'sample_data': [{'name': 'John', 'age': '25'}]
        }]
        mock_schema_processor.return_value = mock_processor_instance
        
        # Test extraction
        extractor = TableExtractorImpl()
        document = Document(
            content='<html><body><table><tr><td>Test</td></tr></table></body></html>',
            format=DocumentFormat.HTML
        )
        
        tables = extractor.extract_tables(document)
        self.assertEqual(len(tables), 1)
        self.assertEqual(tables[0].position, 0)
        
        # Test schema generation
        schema_generator = SchemaGeneratorImpl()
        schemas = schema_generator.generate_schemas(tables)
        
        self.assertEqual(len(schemas), 1)
        self.assertEqual(schemas[0].table_id, tables[0].table_id)
        self.assertEqual(schemas[0].columns, ['name', 'age'])
        self.assertEqual(schemas[0].row_count, 5)
    
    def test_component_dependency_resolution(self):
        """Test that component dependencies are properly resolved."""
        from core.registry import get_global_registry
        from core.types import ComponentConfig
        
        registry = get_global_registry()
        
        # Clear registry for clean test
        registry._components.clear()
        
        # Mock component classes
        class MockDependency:
            def __init__(self, **config):
                self.config = config
        
        class MockMainComponent:
            def __init__(self, dependency=None, **config):
                self.dependency = dependency
                self.config = config
        
        # Register dependency first
        registry.register_component(
            'test_dependency',
            MockDependency,
            ComponentConfig(
                component_type='test_dependency',
                implementation='MockDependency'
            )
        )
        
        # Register main component with dependency
        registry.register_component(
            'test_main',
            MockMainComponent,
            ComponentConfig(
                component_type='test_main',
                implementation='MockMainComponent'
            ),
            dependencies=['test_dependency']
        )
        
        # Validate dependencies
        validation = registry.validate_dependencies()
        self.assertTrue(validation.valid, f"Dependency validation failed: {validation.errors}")
        
        # Get main component (should resolve dependency)
        main_component = registry.get_component('test_main')
        self.assertIsNotNone(main_component)
    
    def test_error_handling_and_recovery(self):
        """Test system behavior with various error conditions."""
        from table_querying.table_processor_factory import TableProcessorFactory
        
        # Test with invalid configuration
        invalid_config = {
            'api_key': '',  # Empty API key
            'db_path': '/invalid/path/that/does/not/exist.db',
            'model_id': 'non-existent-model'
        }
        
        # Should still create processor (may log warnings)
        try:
            processor = TableProcessorFactory.create_processor(
                invalid_config, architecture='interface'
            )
            self.assertIsNotNone(processor)
        except Exception as e:
            # If it fails, it should fail gracefully
            self.assertIsInstance(e, (ImportError, ValueError, RuntimeError))
    
    def test_configuration_inheritance(self):
        """Test that configuration is properly inherited through components."""
        from table_querying.table_processor_factory import TableProcessorFactory
        
        config = {
            'api_key': 'test-key',
            'model_id': 'test-model',
            'db_path': ':memory:',
            'debug': True,
            'context_hint': 'Test context',
            'save_outputs': False
        }
        
        processor = TableProcessorFactory.create_processor(config, architecture='interface')
        
        # Check that processor has the configuration
        self.assertEqual(processor.config, config)
        self.assertTrue(processor.config['debug'])
        self.assertEqual(processor.config['model_id'], 'test-model')
    
    def test_memory_database_integration(self):
        """Test that in-memory database works correctly."""
        from table_querying.interface_implementations import DatabaseClientImpl
        from core.types import (
            Document, Table, Schema, Description, ProcessingResult,
            DocumentFormat, TableFormat, DataType
        )
        
        # Create database client with in-memory database
        db_client = DatabaseClientImpl(db_path=':memory:')
        
        # Test health check
        health = db_client.health_check()
        self.assertTrue(health)
        
        # Create test processing result
        document = Document(content="<html></html>", format=DocumentFormat.HTML)
        table = Table(table_id="t1", content="<table></table>", format=TableFormat.HTML)
        schema = Schema(
            table_id="t1",
            columns=['col1'],
            column_types={'col1': DataType.STRING},
            row_count=1,
            sample_data=[{'col1': 'value1'}]
        )
        description = Description(
            table_id="t1",
            content="Test description",
            generated_by="test_system"
        )
        
        result = ProcessingResult(
            success=True,
            document=document,
            tables=[table],
            schemas=[schema],
            descriptions=[description],
            session_id="test_session"
        )
        
        # Store result
        stored = db_client.store_processing_result(result)
        self.assertTrue(stored)
        
        # Get summary
        summary = db_client.get_database_summary()
        self.assertIsInstance(summary, dict)


class TestSystemValidation(unittest.TestCase):
    """Test system validation and health checks."""
    
    def test_all_required_modules_importable(self):
        """Test that all required modules can be imported."""
        required_modules = [
            'core.interfaces',
            'core.types',
            'core.registry',
            'core.context',
            'core.exceptions',
            'table_querying.interface_implementations',
            'table_querying.table_processor_v2',
            'table_querying.table_processor_factory',
            'components.adapters',
            'components.factories',
            'services.service_factory'
        ]
        
        for module_name in required_modules:
            try:
                __import__(module_name)
            except ImportError as e:
                self.fail(f"Required module {module_name} could not be imported: {e}")
    
    def test_interface_compliance(self):
        """Test that implementations comply with interface contracts."""
        from table_querying.interface_implementations import (
            TableExtractorImpl, SchemaGeneratorImpl, TableDescriptorImpl,
            DatabaseClientImpl, DocumentProcessorImpl
        )
        from core.interfaces import (
            TableExtractor, SchemaGenerator, TableDescriptor,
            DatabaseClient, DocumentProcessor
        )
        
        # Check that implementations are instances of their interfaces
        implementations = [
            (TableExtractorImpl(), TableExtractor),
            (SchemaGeneratorImpl(), SchemaGenerator),
            (TableDescriptorImpl(), TableDescriptor),
            (DatabaseClientImpl(db_path=':memory:'), DatabaseClient),
            (DocumentProcessorImpl(), DocumentProcessor)
        ]
        
        for impl, interface in implementations:
            self.assertIsInstance(impl, interface,
                f"{impl.__class__.__name__} should be instance of {interface.__name__}")
    
    def test_global_registry_singleton(self):
        """Test that global registry maintains singleton behavior."""
        from core.registry import get_global_registry
        
        registry1 = get_global_registry()
        registry2 = get_global_registry()
        
        self.assertIs(registry1, registry2)
        
        # Test that state is shared
        registry1.register_component(
            'test_singleton',
            str,  # Simple class for testing
            None
        )
        
        components1 = registry1.list_components()
        components2 = registry2.list_components()
        
        self.assertEqual(components1, components2)
    
    def test_type_validation(self):
        """Test type validation across the system."""
        from core.types import ValidationResult, ComponentConfig
        
        # Test ValidationResult
        result = ValidationResult(valid=True)
        self.assertTrue(result.valid)
        
        result.add_error("Test error")
        self.assertFalse(result.valid)
        
        summary = result.get_error_summary()
        self.assertIn("Test error", summary)
        
        # Test ComponentConfig
        config = ComponentConfig(
            component_type="test",
            implementation="TestImpl"
        )
        
        config_dict = config.to_dict()
        self.assertIsInstance(config_dict, dict)
        self.assertEqual(config_dict['component_type'], "test")


class TestPerformanceAndScaling(unittest.TestCase):
    """Test performance characteristics and scaling behavior."""
    
    def test_large_document_handling(self):
        """Test handling of documents with many tables."""
        from table_querying.interface_implementations import TableExtractorImpl
        from core.types import Document, DocumentFormat
        
        # Create document with many tables
        table_html = '<table><tr><th>Col1</th><th>Col2</th></tr><tr><td>Data1</td><td>Data2</td></tr></table>'
        many_tables_html = f"""
        <html>
        <body>
            <h1>Document with Many Tables</h1>
            {''.join(table_html for _ in range(50))}
        </body>
        </html>
        """
        
        document = Document(
            content=many_tables_html,
            format=DocumentFormat.HTML
        )
        
        # This should not crash or take excessive time
        extractor = TableExtractorImpl()
        
        # Mock the legacy extractor to avoid actual HTML parsing
        with patch('table_querying.interface_implementations.LegacyTableExtractor') as mock_extractor_class:
            mock_extractor = Mock()
            mock_table = Mock()
            mock_table.__str__ = lambda: table_html
            mock_extractor.extract_from_file.return_value = {
                'html_tables': [mock_table] * 50
            }
            mock_extractor_class.return_value = mock_extractor
            
            tables = extractor.extract_tables(document)
            
            self.assertEqual(len(tables), 50)
            self.assertTrue(all(table.table_id for table in tables))
    
    def test_concurrent_component_access(self):
        """Test thread safety of component registry."""
        from core.registry import get_global_registry
        from core.types import ComponentConfig
        import threading
        import time
        
        registry = get_global_registry()
        results = []
        
        def register_component(component_id):
            try:
                registry.register_component(
                    f'test_component_{component_id}',
                    str,
                    ComponentConfig(
                        component_type=f'test_{component_id}',
                        implementation='TestImpl'
                    )
                )
                results.append(f'success_{component_id}')
            except Exception as e:
                results.append(f'error_{component_id}: {e}')
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=register_component, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=5.0)  # 5 second timeout
        
        # Check results
        self.assertEqual(len(results), 5)
        success_count = len([r for r in results if r.startswith('success_')])
        self.assertEqual(success_count, 5, f"Some registrations failed: {results}")


if __name__ == '__main__':
    # Run with detailed output
    unittest.main(verbosity=2, buffer=True)