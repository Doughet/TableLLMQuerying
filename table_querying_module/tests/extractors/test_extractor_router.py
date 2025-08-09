"""Tests for extractor router."""

import unittest
from pathlib import Path
import tempfile

from src.table_querying.extractors.extractor_router import ExtractorRouter
from src.table_querying.extractors.base_extractor import BaseTableExtractor, ExtractionResult


class TestExtractor1(BaseTableExtractor):
    """Mock extractor for .test1 files."""
    
    def extract_from_file(self, file_path: str) -> ExtractionResult:
        return ExtractionResult(
            source_file=file_path,
            tables_found=1,
            extraction_successful=True,
            extracted_data={'type': 'test1'}
        )
    
    def supports_file_type(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() == '.test1'
    
    def get_supported_extensions(self) -> list:
        return ['.test1']


class TestExtractor2(BaseTableExtractor):
    """Mock extractor for .test2 files."""
    
    def extract_from_file(self, file_path: str) -> ExtractionResult:
        return ExtractionResult(
            source_file=file_path,
            tables_found=2,
            extraction_successful=True,
            extracted_data={'type': 'test2'}
        )
    
    def supports_file_type(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() == '.test2'
    
    def get_supported_extensions(self) -> list:
        return ['.test2']


class TestExtractorRouter(unittest.TestCase):
    """Test cases for ExtractorRouter."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create router without calling __init__ to avoid default extractors
        self.router = ExtractorRouter.__new__(ExtractorRouter)
        self.router.extractors = [TestExtractor1(), TestExtractor2()]
        self.router._extension_mapping = self.router._build_extension_mapping()
        
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_get_supported_extensions(self):
        """Test getting all supported extensions."""
        extensions = self.router.get_supported_extensions()
        self.assertIn('.test1', extensions)
        self.assertIn('.test2', extensions)
        self.assertEqual(len(extensions), 2)
    
    def test_get_extractor_by_extension(self):
        """Test getting extractor by file extension."""
        extractor1 = self.router.get_extractor('file.test1')
        extractor2 = self.router.get_extractor('file.test2')
        
        self.assertIsInstance(extractor1, TestExtractor1)
        self.assertIsInstance(extractor2, TestExtractor2)
    
    def test_get_extractor_unsupported_extension(self):
        """Test error for unsupported file extension."""
        with self.assertRaises(ValueError) as context:
            self.router.get_extractor('file.unsupported')
        
        self.assertIn('No extractor found', str(context.exception))
        self.assertIn('.test1', str(context.exception))
        self.assertIn('.test2', str(context.exception))
    
    def test_is_supported_file(self):
        """Test checking if file is supported."""
        self.assertTrue(self.router.is_supported_file('file.test1'))
        self.assertTrue(self.router.is_supported_file('file.test2'))
        self.assertFalse(self.router.is_supported_file('file.unsupported'))
    
    def test_extract_from_file(self):
        """Test extracting from file using router."""
        # Create temporary files
        test1_file = Path(self.temp_dir) / 'test.test1'
        test1_file.write_text('test1 content')
        
        test2_file = Path(self.temp_dir) / 'test.test2'
        test2_file.write_text('test2 content')
        
        # Extract from both files
        result1 = self.router.extract_from_file(str(test1_file))
        result2 = self.router.extract_from_file(str(test2_file))
        
        self.assertTrue(result1.extraction_successful)
        self.assertEqual(result1.tables_found, 1)
        self.assertEqual(result1.extracted_data['type'], 'test1')
        
        self.assertTrue(result2.extraction_successful)
        self.assertEqual(result2.tables_found, 2)
        self.assertEqual(result2.extracted_data['type'], 'test2')
    
    def test_extract_from_unsupported_file(self):
        """Test extracting from unsupported file."""
        result = self.router.extract_from_file('file.unsupported')
        
        self.assertFalse(result.extraction_successful)
        self.assertEqual(result.tables_found, 0)
        self.assertIsNotNone(result.error_message)
        self.assertIn('No extractor found', result.error_message)
    
    def test_get_extractor_info(self):
        """Test getting extractor information."""
        info = self.router.get_extractor_info()
        
        self.assertEqual(info['total_extractors'], 2)
        self.assertIn('.test1', info['supported_extensions'])
        self.assertIn('.test2', info['supported_extensions'])
        
        extractor_names = [ext['name'] for ext in info['extractors']]
        self.assertIn('TestExtractor1', extractor_names)
        self.assertIn('TestExtractor2', extractor_names)
    
    def test_add_extractor(self):
        """Test adding a new extractor."""
        class TestExtractor3(BaseTableExtractor):
            def extract_from_file(self, file_path: str) -> ExtractionResult:
                return ExtractionResult(
                    source_file=file_path,
                    tables_found=3,
                    extraction_successful=True
                )
            
            def supports_file_type(self, file_path: str) -> bool:
                return Path(file_path).suffix.lower() == '.test3'
            
            def get_supported_extensions(self) -> list:
                return ['.test3']
        
        # Add new extractor
        new_extractor = TestExtractor3()
        self.router.add_extractor(new_extractor)
        
        # Test it was added
        self.assertEqual(len(self.router.extractors), 3)
        self.assertIn('.test3', self.router.get_supported_extensions())
        
        # Test it can be used
        extractor = self.router.get_extractor('file.test3')
        self.assertIsInstance(extractor, TestExtractor3)
    
    def test_remove_extractor(self):
        """Test removing an extractor."""
        # Remove TestExtractor1
        removed = self.router.remove_extractor('TestExtractor1')
        
        self.assertTrue(removed)
        self.assertEqual(len(self.router.extractors), 1)
        self.assertNotIn('.test1', self.router.get_supported_extensions())
        
        # Test it can't be found anymore
        with self.assertRaises(ValueError):
            self.router.get_extractor('file.test1')
    
    def test_remove_nonexistent_extractor(self):
        """Test removing a non-existent extractor."""
        removed = self.router.remove_extractor('NonExistentExtractor')
        self.assertFalse(removed)
        self.assertEqual(len(self.router.extractors), 2)
    
    def test_build_extension_mapping(self):
        """Test building extension mapping."""
        mapping = self.router._build_extension_mapping()
        
        self.assertEqual(len(mapping), 2)
        self.assertIsInstance(mapping['.test1'], TestExtractor1)
        self.assertIsInstance(mapping['.test2'], TestExtractor2)


if __name__ == '__main__':
    unittest.main()