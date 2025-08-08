"""
Unit tests for TableProcessorV2 and factory patterns.

Tests the new interface-based processor and factory system.
"""

import unittest
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import os
import sys
import json

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'table_querying_module' / 'src'))

from core.types import (
    Document, ProcessingResult, DocumentFormat,
    ProcessingStatus, ComponentConfig
)


class TestTableProcessorFactory(unittest.TestCase):
    """Test TableProcessor factory system."""
    
    def test_get_available_architectures(self):
        """Test getting available architectures."""
        from table_querying.table_processor_factory import TableProcessorFactory
        
        architectures = TableProcessorFactory.get_available_architectures()
        
        self.assertIsInstance(architectures, dict)
        self.assertIn('legacy', architectures)
        self.assertIn('interface', architectures)
    
    @patch('table_querying.table_processor_factory.TableProcessorV2')
    @patch('table_querying.table_processor_factory.TableProcessor')
    def test_create_processor_interface_architecture(self, mock_legacy, mock_v2):
        """Test creating interface architecture processor."""
        from table_querying.table_processor_factory import TableProcessorFactory
        
        config = {'architecture': 'interface', 'api_key': 'test-key'}
        
        processor = TableProcessorFactory.create_processor(config, architecture='interface')
        
        mock_v2.assert_called_once_with(config)
        mock_legacy.assert_not_called()
    
    @patch('table_querying.table_processor_factory.TableProcessorV2')
    @patch('table_querying.table_processor_factory.TableProcessor')
    def test_create_processor_legacy_architecture(self, mock_legacy, mock_v2):
        """Test creating legacy architecture processor."""
        from table_querying.table_processor_factory import TableProcessorFactory
        
        config = {'architecture': 'legacy', 'api_key': 'test-key'}
        
        processor = TableProcessorFactory.create_processor(config, architecture='legacy')
        
        mock_legacy.assert_called_once_with(config)
        mock_v2.assert_not_called()
    
    @patch('table_querying.table_processor_factory.TableProcessorV2')
    @patch('table_querying.table_processor_factory.TableProcessor')
    def test_auto_architecture_selection(self, mock_legacy, mock_v2):
        """Test automatic architecture selection."""
        from table_querying.table_processor_factory import TableProcessorFactory
        
        config = {}  # No architecture specified
        
        processor = TableProcessorFactory.create_processor(config, architecture='auto')
        
        # Should default to interface architecture
        mock_v2.assert_called_once()
        mock_legacy.assert_not_called()
    
    @patch('table_querying.table_processor_factory.TableProcessorV2')
    @patch('table_querying.table_processor_factory.TableProcessor')
    def test_fallback_on_failure(self, mock_legacy, mock_v2):
        """Test fallback to other architecture on failure."""
        from table_querying.table_processor_factory import TableProcessorFactory
        
        # Make interface architecture fail
        mock_v2.side_effect = Exception("Interface creation failed")
        
        config = {'architecture': 'interface'}
        
        processor = TableProcessorFactory.create_processor(config, architecture='interface')
        
        # Should fallback to legacy
        mock_v2.assert_called_once()
        mock_legacy.assert_called_once()
    
    def test_create_config_template(self):
        """Test configuration template creation."""
        from table_querying.table_processor_factory import TableProcessorFactory
        
        # Test interface config template
        interface_config = TableProcessorFactory.create_config_template('interface')
        
        self.assertIsInstance(interface_config, dict)
        self.assertEqual(interface_config['architecture'], 'interface')
        self.assertIn('component_registry_enabled', interface_config)
        self.assertIn('dependency_injection', interface_config)
        
        # Test legacy config template
        legacy_config = TableProcessorFactory.create_config_template('legacy')
        
        self.assertEqual(legacy_config['architecture'], 'legacy')
        self.assertNotIn('component_registry_enabled', legacy_config)
    
    @patch('table_querying.table_processor_factory.TableProcessorV2')
    def test_convenience_create_processor(self, mock_v2):
        """Test convenience create_processor function."""
        from table_querying.table_processor_factory import create_processor
        
        processor = create_processor(
            {'api_key': 'test'}, 
            architecture='interface',
            debug=True
        )
        
        # Should be called with merged config
        expected_config = {'api_key': 'test', 'architecture': 'interface', 'debug': True}
        mock_v2.assert_called_once_with(expected_config)


class TestTableProcessorV2(unittest.TestCase):
    """Test TableProcessorV2 functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_config = {
            'api_key': 'test-key',
            'db_path': ':memory:',
            'save_outputs': False,
            'environment': 'testing',
            'debug': True
        }
    
    @patch('table_querying.table_processor_v2.get_global_registry')
    @patch('table_querying.interface_implementations.TableExtractorImpl')
    @patch('table_querying.interface_implementations.SchemaGeneratorImpl')
    @patch('table_querying.interface_implementations.TableDescriptorImpl')
    @patch('table_querying.interface_implementations.DatabaseClientImpl')
    @patch('table_querying.interface_implementations.DocumentProcessorImpl')
    def test_processor_initialization(self, mock_doc_proc, mock_db, mock_desc, 
                                    mock_schema, mock_extractor, mock_registry):
        """Test TableProcessorV2 initialization."""
        mock_registry_instance = Mock()
        mock_registry.return_value = mock_registry_instance
        mock_registry_instance.get_component.return_value = Mock()
        
        from table_querying.table_processor_v2 import TableProcessorV2
        
        processor = TableProcessorV2(self.test_config)
        
        self.assertIsNotNone(processor.registry)
        self.assertIsNotNone(processor.context)
        self.assertIsNotNone(processor.document_processor)
        self.assertEqual(processor.save_outputs, False)
        self.assertEqual(processor.clear_database_on_start, False)
    
    @patch('table_querying.table_processor_v2.get_global_registry')
    def test_component_registration(self, mock_registry):
        """Test component registration during initialization."""
        mock_registry_instance = Mock()
        mock_registry.return_value = mock_registry_instance
        mock_registry_instance.get_component.return_value = Mock()
        
        from table_querying.table_processor_v2 import TableProcessorV2
        
        with patch('table_querying.interface_implementations.TableExtractorImpl'), \
             patch('table_querying.interface_implementations.SchemaGeneratorImpl'), \
             patch('table_querying.interface_implementations.TableDescriptorImpl'), \
             patch('table_querying.interface_implementations.DatabaseClientImpl'), \
             patch('table_querying.interface_implementations.DocumentProcessorImpl'):
            
            processor = TableProcessorV2(self.test_config)
            
            # Verify components were registered
            register_calls = mock_registry_instance.register_component.call_args_list
            
            # Should register at least: extractor, schema_generator, descriptor, database, document_processor
            self.assertGreaterEqual(len(register_calls), 5)
            
            # Check that specific components were registered
            registered_names = [call[0][0] for call in register_calls]
            expected_components = [
                'table_extractor', 'schema_generator', 'table_descriptor', 
                'database_client', 'document_processor'
            ]
            
            for component in expected_components:
                self.assertIn(component, registered_names)
    
    @patch('table_querying.table_processor_v2.get_global_registry')
    def test_process_document(self, mock_registry):
        """Test document processing."""
        # Setup mocks
        mock_registry_instance = Mock()
        mock_registry.return_value = mock_registry_instance
        
        mock_document_processor = Mock()
        mock_processing_result = ProcessingResult(
            success=True,
            document=Document(content="<html></html>", format=DocumentFormat.HTML),
            session_id="test_session"
        )
        mock_processing_result.tables = []
        mock_processing_result.schemas = []
        mock_processing_result.descriptions = []
        mock_processing_result.processing_time = 1.5
        mock_processing_result.table_count = 0
        mock_processing_result.status = ProcessingStatus.COMPLETED
        mock_processing_result.error_message = None
        
        mock_document_processor.process_document.return_value = mock_processing_result
        mock_registry_instance.get_component.return_value = mock_document_processor
        
        from table_querying.table_processor_v2 import TableProcessorV2
        
        # Create temporary HTML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write('<html><body><table><tr><td>Test</td></tr></table></body></html>')
            temp_path = f.name
        
        try:
            with patch('table_querying.interface_implementations.TableExtractorImpl'), \
                 patch('table_querying.interface_implementations.SchemaGeneratorImpl'), \
                 patch('table_querying.interface_implementations.TableDescriptorImpl'), \
                 patch('table_querying.interface_implementations.DatabaseClientImpl'), \
                 patch('table_querying.interface_implementations.DocumentProcessorImpl'):
                
                processor = TableProcessorV2(self.test_config)
                
                # Process document
                results = processor.process_document(temp_path)
                
                # Verify results
                self.assertIsInstance(results, dict)
                self.assertTrue(results.get('success', False))
                self.assertEqual(results.get('session_id'), 'test_session')
                self.assertIn('statistics', results)
                self.assertIn('processing_time', results)
                
        finally:
            os.unlink(temp_path)
    
    @patch('table_querying.table_processor_v2.get_global_registry')
    def test_get_component_info(self, mock_registry):
        """Test getting component information."""
        mock_registry_instance = Mock()
        mock_registry.return_value = mock_registry_instance
        mock_registry_instance.get_component.return_value = Mock()
        
        # Mock registry methods
        mock_components = {
            'table_extractor': [{'type': 'TableExtractorImpl', 'class': 'TableExtractorImpl'}],
            'schema_generator': [{'type': 'SchemaGeneratorImpl', 'class': 'SchemaGeneratorImpl'}]
        }
        mock_dependency_graph = {'table_extractor': [], 'schema_generator': ['table_extractor']}
        mock_validation = Mock()
        mock_validation.valid = True
        mock_validation.errors = []
        mock_validation.warnings = []
        
        mock_registry_instance.list_components.return_value = mock_components
        mock_registry_instance.get_dependency_graph.return_value = mock_dependency_graph
        mock_registry_instance.validate_dependencies.return_value = mock_validation
        
        from table_querying.table_processor_v2 import TableProcessorV2
        
        with patch('table_querying.interface_implementations.TableExtractorImpl'), \
             patch('table_querying.interface_implementations.SchemaGeneratorImpl'), \
             patch('table_querying.interface_implementations.TableDescriptorImpl'), \
             patch('table_querying.interface_implementations.DatabaseClientImpl'), \
             patch('table_querying.interface_implementations.DocumentProcessorImpl'):
            
            processor = TableProcessorV2(self.test_config)
            
            component_info = processor.get_component_info()
            
            self.assertIsInstance(component_info, dict)
            self.assertIn('registered_components', component_info)
            self.assertIn('dependency_graph', component_info)
            self.assertIn('dependency_validation', component_info)
            self.assertIn('architecture_version', component_info)
            self.assertEqual(component_info['architecture_version'], '2.0 (Interface-based)')
    
    @patch('table_querying.table_processor_v2.get_global_registry')
    def test_save_processing_outputs(self, mock_registry):
        """Test saving processing outputs to files."""
        mock_registry_instance = Mock()
        mock_registry.return_value = mock_registry_instance
        mock_registry_instance.get_component.return_value = Mock()
        
        from table_querying.table_processor_v2 import TableProcessorV2
        
        # Create temporary output directory
        with tempfile.TemporaryDirectory() as temp_dir:
            config = dict(self.test_config)
            config['save_outputs'] = True
            config['output_dir'] = temp_dir
            
            with patch('table_querying.interface_implementations.TableExtractorImpl'), \
                 patch('table_querying.interface_implementations.SchemaGeneratorImpl'), \
                 patch('table_querying.interface_implementations.TableDescriptorImpl'), \
                 patch('table_querying.interface_implementations.DatabaseClientImpl'), \
                 patch('table_querying.interface_implementations.DocumentProcessorImpl'):
                
                processor = TableProcessorV2(config)
                
                # Create mock processing result
                result = ProcessingResult(
                    success=True,
                    document=Document(content="<html></html>", format=DocumentFormat.HTML),
                    session_id="test_session"
                )
                result.tables = []
                result.schemas = []
                result.descriptions = []
                result.processing_time = 1.5
                result.table_count = 0
                result.status = ProcessingStatus.COMPLETED
                
                # Save outputs
                processor._save_processing_outputs(result, "/test/file.html")
                
                # Check that summary file was created
                summary_file = Path(temp_dir) / "file_processing_summary.json"
                self.assertTrue(summary_file.exists())
                
                # Check summary content
                with open(summary_file) as f:
                    summary_data = json.load(f)
                    self.assertEqual(summary_data['session_id'], 'test_session')
                    self.assertTrue(summary_data['success'])
    
    @patch('table_querying.table_processor_v2.get_global_registry')
    def test_print_processing_summary(self, mock_registry):
        """Test printing processing summary."""
        mock_registry_instance = Mock()
        mock_registry.return_value = mock_registry_instance
        mock_registry_instance.get_component.return_value = Mock()
        
        from table_querying.table_processor_v2 import TableProcessorV2
        
        with patch('table_querying.interface_implementations.TableExtractorImpl'), \
             patch('table_querying.interface_implementations.SchemaGeneratorImpl'), \
             patch('table_querying.interface_implementations.TableDescriptorImpl'), \
             patch('table_querying.interface_implementations.DatabaseClientImpl'), \
             patch('table_querying.interface_implementations.DocumentProcessorImpl'):
            
            processor = TableProcessorV2(self.test_config)
            
            # Test successful results
            success_results = {
                'success': True,
                'html_file': '/test/file.html',
                'session_id': 'test_session',
                'statistics': {
                    'html_tables': 2,
                    'successful_schemas': 2,
                    'successful_descriptions': 2,
                    'processing_time': 1.5,
                    'status': 'completed'
                },
                'database_results': {
                    'stored_tables': 2
                }
            }
            
            # This should not raise an exception
            try:
                processor.print_processing_summary(success_results)
            except Exception as e:
                self.fail(f"print_processing_summary raised an exception: {e}")
            
            # Test failed results
            failed_results = {
                'success': False,
                'error': 'Test error message'
            }
            
            try:
                processor.print_processing_summary(failed_results)
            except Exception as e:
                self.fail(f"print_processing_summary raised an exception: {e}")
    
    @patch('table_querying.table_processor_v2.get_global_registry')
    def test_get_database_summary(self, mock_registry):
        """Test getting database summary."""
        mock_registry_instance = Mock()
        mock_registry.return_value = mock_registry_instance
        
        mock_db_client = Mock()
        mock_db_summary = {
            'total_tables': 5,
            'total_sessions': 2,
            'database_size': '1.2MB'
        }
        mock_db_client.get_database_summary.return_value = mock_db_summary
        mock_registry_instance.get_component.return_value = mock_db_client
        
        from table_querying.table_processor_v2 import TableProcessorV2
        
        with patch('table_querying.interface_implementations.TableExtractorImpl'), \
             patch('table_querying.interface_implementations.SchemaGeneratorImpl'), \
             patch('table_querying.interface_implementations.TableDescriptorImpl'), \
             patch('table_querying.interface_implementations.DatabaseClientImpl'), \
             patch('table_querying.interface_implementations.DocumentProcessorImpl'):
            
            processor = TableProcessorV2(self.test_config)
            
            summary = processor.get_database_summary()
            
            self.assertEqual(summary, mock_db_summary)
            mock_db_client.get_database_summary.assert_called_once()
    
    @patch('table_querying.table_processor_v2.get_global_registry')
    def test_llm_client_registration_with_api_key(self, mock_registry):
        """Test LLM client registration with API key."""
        mock_registry_instance = Mock()
        mock_registry.return_value = mock_registry_instance
        mock_registry_instance.get_component.return_value = Mock()
        
        config_with_api_key = dict(self.test_config)
        config_with_api_key['api_key'] = 'valid-api-key'
        
        from table_querying.table_processor_v2 import TableProcessorV2
        
        with patch('table_querying.interface_implementations.TableExtractorImpl'), \
             patch('table_querying.interface_implementations.SchemaGeneratorImpl'), \
             patch('table_querying.interface_implementations.TableDescriptorImpl'), \
             patch('table_querying.interface_implementations.DatabaseClientImpl'), \
             patch('table_querying.interface_implementations.DocumentProcessorImpl'), \
             patch('services.service_factory.ServiceFactory') as mock_service_factory, \
             patch('components.adapters.create_llm_adapter') as mock_adapter:
            
            mock_llm_service = Mock()
            mock_service_factory.create_llm_service.return_value = mock_llm_service
            mock_llm_adapter = Mock()
            mock_adapter.return_value = mock_llm_adapter
            
            processor = TableProcessorV2(config_with_api_key)
            
            # Verify LLM service was created
            mock_service_factory.create_llm_service.assert_called_once()
            mock_adapter.assert_called_once_with(mock_llm_service)
    
    @patch('table_querying.table_processor_v2.get_global_registry')
    def test_llm_client_registration_without_api_key(self, mock_registry):
        """Test LLM client registration without API key."""
        mock_registry_instance = Mock()
        mock_registry.return_value = mock_registry_instance
        mock_registry_instance.get_component.return_value = Mock()
        
        config_no_api_key = dict(self.test_config)
        config_no_api_key.pop('api_key', None)  # Remove API key
        
        from table_querying.table_processor_v2 import TableProcessorV2
        
        with patch('table_querying.interface_implementations.TableExtractorImpl'), \
             patch('table_querying.interface_implementations.SchemaGeneratorImpl'), \
             patch('table_querying.interface_implementations.TableDescriptorImpl'), \
             patch('table_querying.interface_implementations.DatabaseClientImpl'), \
             patch('table_querying.interface_implementations.DocumentProcessorImpl'):
            
            # This should not raise an exception, just log a warning
            processor = TableProcessorV2(config_no_api_key)
            
            # Should still create processor successfully
            self.assertIsNotNone(processor)


if __name__ == '__main__':
    unittest.main(verbosity=2)