"""Tests for base table extractor interface."""

import unittest
from pathlib import Path
import tempfile
import os

from src.table_querying.extractors.base_extractor import BaseTableExtractor, ExtractionResult


class MockExtractor(BaseTableExtractor):
    """Mock extractor for testing."""
    
    def extract_from_file(self, file_path: str) -> ExtractionResult:
        return ExtractionResult(
            source_file=file_path,
            tables_found=1,
            extraction_successful=True,
            extracted_data={'test': 'data'}
        )
    
    def supports_file_type(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() == '.test'
    
    def get_supported_extensions(self) -> list:
        return ['.test']


class TestBaseExtractor(unittest.TestCase):
    """Test cases for BaseTableExtractor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.extractor = MockExtractor()
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_extractor_name(self):
        """Test get_extractor_name method."""
        self.assertEqual(self.extractor.get_extractor_name(), 'MockExtractor')
    
    def test_supported_extensions(self):
        """Test get_supported_extensions method."""
        extensions = self.extractor.get_supported_extensions()
        self.assertEqual(extensions, ['.test'])
    
    def test_supports_file_type(self):
        """Test supports_file_type method."""
        self.assertTrue(self.extractor.supports_file_type('test.test'))
        self.assertFalse(self.extractor.supports_file_type('test.html'))
    
    def test_validate_file_exists(self):
        """Test file validation for existing file."""
        # Create a temporary file
        test_file = Path(self.temp_dir) / 'test.test'
        test_file.write_text('test content')
        
        # Should not raise exception
        self.extractor.validate_file(str(test_file))
    
    def test_validate_file_not_exists(self):
        """Test file validation for non-existing file."""
        with self.assertRaises(FileNotFoundError):
            self.extractor.validate_file('nonexistent.test')
    
    def test_validate_unsupported_file_type(self):
        """Test file validation for unsupported file type."""
        # Create a temporary file with unsupported extension
        test_file = Path(self.temp_dir) / 'test.unsupported'
        test_file.write_text('test content')
        
        with self.assertRaises(ValueError) as context:
            self.extractor.validate_file(str(test_file))
        
        self.assertIn('Unsupported file format', str(context.exception))
        self.assertIn('.test', str(context.exception))
    
    def test_extract_from_file(self):
        """Test extract_from_file method."""
        result = self.extractor.extract_from_file('test.test')
        
        self.assertIsInstance(result, ExtractionResult)
        self.assertEqual(result.source_file, 'test.test')
        self.assertEqual(result.tables_found, 1)
        self.assertTrue(result.extraction_successful)
        self.assertEqual(result.extracted_data, {'test': 'data'})


class TestExtractionResult(unittest.TestCase):
    """Test cases for ExtractionResult."""
    
    def test_creation_with_defaults(self):
        """Test ExtractionResult creation with default values."""
        result = ExtractionResult(
            source_file='test.html',
            tables_found=2,
            extraction_successful=True
        )
        
        self.assertEqual(result.source_file, 'test.html')
        self.assertEqual(result.tables_found, 2)
        self.assertTrue(result.extraction_successful)
        self.assertIsNone(result.error_message)
        self.assertEqual(result.extracted_data, {})
    
    def test_creation_with_error(self):
        """Test ExtractionResult creation with error."""
        result = ExtractionResult(
            source_file='test.html',
            tables_found=0,
            extraction_successful=False,
            error_message='Test error',
            extracted_data={'error': 'details'}
        )
        
        self.assertEqual(result.source_file, 'test.html')
        self.assertEqual(result.tables_found, 0)
        self.assertFalse(result.extraction_successful)
        self.assertEqual(result.error_message, 'Test error')
        self.assertEqual(result.extracted_data, {'error': 'details'})


if __name__ == '__main__':
    unittest.main()