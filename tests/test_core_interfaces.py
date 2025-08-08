"""
Unit tests for core interfaces and types.

Tests the fundamental interface definitions, type system, and validation logic.
"""

import unittest
import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import os
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'table_querying_module' / 'src'))

from core.interfaces import (
    DocumentProcessor, TableExtractor, SchemaGenerator,
    TableDescriptor, DatabaseClient, LLMClient
)
from core.types import (
    Document, Table, Schema, Description, ProcessingResult,
    ValidationResult, Query, QueryResult, ComponentConfig,
    DocumentFormat, TableFormat, DataType, ProcessingStatus
)
from core.exceptions import TableQueryingError, ValidationError
from core.registry import ComponentRegistry, get_global_registry


class TestCoreTypes(unittest.TestCase):
    """Test core type definitions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_content = "<html><body><table><tr><td>Test</td></tr></table></body></html>"
        
    def test_document_creation(self):
        """Test Document type creation and validation."""
        # Test basic document
        doc = Document(
            content=self.sample_content,
            format=DocumentFormat.HTML
        )
        
        self.assertEqual(doc.content, self.sample_content)
        self.assertEqual(doc.format, DocumentFormat.HTML)
        self.assertIsNotNone(doc.filename)
        self.assertIsNotNone(doc.filename)
        
        # Test document with path
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(self.sample_content)
            temp_path = f.name
        
        try:
            doc_with_path = Document(
                content=self.sample_content,
                source_path=Path(temp_path),
                format=DocumentFormat.HTML
            )
            
            self.assertEqual(doc_with_path.source_path, Path(temp_path))
            self.assertIn(Path(temp_path).stem, doc_with_path.filename)
            
        finally:
            os.unlink(temp_path)
    
    def test_table_creation(self):
        """Test Table type creation."""
        table = Table(
            table_id="test_table_1",
            content="<table><tr><td>Test</td></tr></table>",
            format=TableFormat.HTML,
            position=0,
            source_document="test_doc"
        )
        
        self.assertEqual(table.table_id, "test_table_1")
        self.assertEqual(table.format, TableFormat.HTML)
        self.assertEqual(table.position, 0)
        self.assertEqual(table.source_document, "test_doc")
        self.assertIsInstance(table.metadata, dict)
    
    def test_schema_creation(self):
        """Test Schema type creation."""
        schema = Schema(
            table_id="test_table_1",
            columns=["name", "age", "city"],
            column_types={"name": DataType.STRING, "age": DataType.INTEGER, "city": DataType.STRING},
            row_count=10,
            sample_data=[{"name": "John", "age": "25", "city": "NYC"}]
        )
        
        self.assertEqual(schema.table_id, "test_table_1")
        self.assertEqual(len(schema.columns), 3)
        self.assertEqual(schema.column_types["age"], DataType.INTEGER)
        self.assertEqual(schema.row_count, 10)
        self.assertIsInstance(schema.sample_data, list)
    
    def test_description_creation(self):
        """Test Description type creation."""
        desc = Description(
            table_id="test_table_1",
            content="This table contains employee information with names, ages, and cities.",
            generated_by="test_system",
            confidence=0.95
        )
        
        self.assertEqual(desc.table_id, "test_table_1")
        self.assertIn("employee information", desc.content)
        self.assertEqual(desc.generated_by, "test_system")
        self.assertEqual(desc.confidence, 0.95)
        self.assertIsInstance(desc.generated_at, datetime)
    
    def test_processing_result_creation(self):
        """Test ProcessingResult type creation."""
        # Create minimal components
        doc = Document(content="<html></html>", format=DocumentFormat.HTML)
        table = Table(table_id="t1", content="<table></table>", format=TableFormat.HTML)
        schema = Schema(table_id="t1", columns=["col1"], column_types={"col1": DataType.STRING}, row_count=1)
        desc = Description(table_id="t1", content="Test description", generated_by="test")
        
        result = ProcessingResult(
            success=True,
            document=doc,
            tables=[table],
            schemas=[schema],
            descriptions=[desc],
            session_id="test_session"
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.document, doc)
        self.assertEqual(len(result.tables), 1)
        self.assertEqual(len(result.schemas), 1)
        self.assertEqual(len(result.descriptions), 1)
        self.assertEqual(result.session_id, "test_session")
        self.assertEqual(result.table_count, 1)
    
    def test_validation_result(self):
        """Test ValidationResult functionality."""
        result = ValidationResult(valid=True)
        
        self.assertTrue(result.valid)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.warnings), 0)
        
        # Add errors and warnings
        result.add_error("Test error")
        result.add_warning("Test warning")
        
        self.assertFalse(result.valid)  # Should become invalid with errors
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(len(result.warnings), 1)
        
        # Test error summary
        summary = result.get_error_summary()
        self.assertIn("Test error", summary)
        self.assertIn("Test warning", summary)
    
    def test_component_config(self):
        """Test ComponentConfig functionality."""
        config = ComponentConfig(
            component_type="table_extractor",
            implementation="TableExtractorImpl",
            config={"debug": True}
        )
        
        self.assertEqual(config.component_type, "table_extractor")
        self.assertEqual(config.implementation, "TableExtractorImpl")
        self.assertTrue(config.config["debug"])
        
        # Test to_dict method
        config_dict = config.to_dict()
        self.assertIsInstance(config_dict, dict)
        self.assertEqual(config_dict["component_type"], "table_extractor")


class TestCoreExceptions(unittest.TestCase):
    """Test core exception types."""
    
    def test_table_querying_error(self):
        """Test TableQueryingError functionality."""
        original_error = ValueError("Original error")
        
        error = TableQueryingError("Test error message", cause=original_error)
        
        self.assertEqual(str(error), "Test error message")
        self.assertEqual(error.cause, original_error)
    
    def test_validation_error(self):
        """Test ValidationError functionality."""
        error = ValidationError("Validation failed")
        
        self.assertEqual(str(error), "Validation failed")
        self.assertIsInstance(error, TableQueryingError)


class TestComponentRegistry(unittest.TestCase):
    """Test component registry functionality."""
    
    def setUp(self):
        """Set up test registry."""
        self.registry = ComponentRegistry()
        
        # Mock component class
        class MockComponent:
            def __init__(self, **config):
                self.config = config
        
        self.mock_component_class = MockComponent
    
    def test_component_registration(self):
        """Test component registration."""
        config = ComponentConfig(
            component_type="test_component",
            implementation="MockComponent"
        )
        
        # Use skip_validation=True for testing
        self.registry.register_component(
            "test_component",
            self.mock_component_class,
            config,
            skip_validation=True
        )
        
        # Check registration
        components = self.registry.list_components()
        # Components are returned as a dict with interface types as keys
        found = False
        for interface_type, component_list in components.items():
            for component in component_list:
                if component.get('type') == 'test_component':
                    found = True
                    break
            if found:
                break
        self.assertTrue(found, f"Component not found in {components}")
        
        # Get component
        component = self.registry.get_component("test_component")
        self.assertIsInstance(component, self.mock_component_class)
    
    def test_component_with_dependencies(self):
        """Test component registration with dependencies."""
        # Register dependency first
        dep_config = ComponentConfig(
            component_type="dependency",
            implementation="MockDependency"
        )
        self.registry.register_component(
            "dependency",
            self.mock_component_class,
            dep_config,
            skip_validation=True
        )
        
        # Register component with dependency
        main_config = ComponentConfig(
            component_type="main_component",
            implementation="MockMainComponent"
        )
        self.registry.register_component(
            "main_component",
            self.mock_component_class,
            main_config,
            dependencies=["dependency"],
            skip_validation=True
        )
        
        # Validate dependencies
        validation = self.registry.validate_dependencies()
        self.assertTrue(validation.valid)
    
    def test_missing_dependency_validation(self):
        """Test validation with missing dependencies."""
        config = ComponentConfig(
            component_type="test_component",
            implementation="MockComponent"
        )
        
        self.registry.register_component(
            "test_component",
            self.mock_component_class,
            config,
            dependencies=["missing_dependency"],
            skip_validation=True
        )
        
        validation = self.registry.validate_dependencies()
        self.assertFalse(validation.valid)
        self.assertTrue(any("missing_dependency" in error for error in validation.errors))
    
    def test_singleton_components(self):
        """Test singleton component behavior."""
        config = ComponentConfig(
            component_type="singleton_component",
            implementation="MockSingleton"
        )
        
        self.registry.register_component(
            "singleton_component",
            self.mock_component_class,
            config,
            singleton=True,
            skip_validation=True
        )
        
        # Get component twice
        component1 = self.registry.get_component("singleton_component")
        component2 = self.registry.get_component("singleton_component")
        
        # Should be the same instance
        self.assertIs(component1, component2)
    
    def test_global_registry(self):
        """Test global registry functionality."""
        global_registry = get_global_registry()
        
        self.assertIsInstance(global_registry, ComponentRegistry)
        
        # Should return the same instance
        global_registry2 = get_global_registry()
        self.assertIs(global_registry, global_registry2)


class TestInterfaceDefinitions(unittest.TestCase):
    """Test that interface definitions work correctly."""
    
    def test_interface_imports(self):
        """Test that all interfaces can be imported."""
        # This test ensures all interfaces are properly defined
        interfaces = [
            DocumentProcessor,
            TableExtractor,
            SchemaGenerator,
            TableDescriptor,
            DatabaseClient,
            LLMClient
        ]
        
        for interface in interfaces:
            self.assertTrue(hasattr(interface, '__abstractmethods__'))
    
    def test_interface_methods(self):
        """Test that interfaces have expected method signatures."""
        # DocumentProcessor
        self.assertTrue(hasattr(DocumentProcessor, 'process_document'))
        self.assertTrue(hasattr(DocumentProcessor, 'process_file'))
        
        # TableExtractor
        self.assertTrue(hasattr(TableExtractor, 'extract_tables'))
        self.assertTrue(hasattr(TableExtractor, 'supported_formats'))
        
        # SchemaGenerator
        self.assertTrue(hasattr(SchemaGenerator, 'generate_schema'))
        self.assertTrue(hasattr(SchemaGenerator, 'generate_schemas'))
        
        # TableDescriptor
        self.assertTrue(hasattr(TableDescriptor, 'describe_table'))
        self.assertTrue(hasattr(TableDescriptor, 'describe_tables'))
        
        # DatabaseClient
        self.assertTrue(hasattr(DatabaseClient, 'store_processing_result'))
        self.assertTrue(hasattr(DatabaseClient, 'get_table_by_id'))
        
        # LLMClient
        self.assertTrue(hasattr(LLMClient, 'generate_description'))


if __name__ == '__main__':
    unittest.main()