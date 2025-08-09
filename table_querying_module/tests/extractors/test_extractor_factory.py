"""Tests for extractor factory."""

import unittest
from src.table_querying.extractors.extractor_factory import ExtractorFactory
from src.table_querying.extractors.html_extractor import HTMLTableExtractor
from src.table_querying.extractors.excel_extractor import ExcelTableExtractor
from src.table_querying.extractors.extractor_router import ExtractorRouter
from src.table_querying.extractors.base_extractor import BaseTableExtractor


class MockExtractor(BaseTableExtractor):
    """Mock extractor for testing."""
    
    def extract_from_file(self, file_path: str):
        pass
    
    def supports_file_type(self, file_path: str) -> bool:
        return file_path.endswith('.mock')
    
    def get_supported_extensions(self) -> list:
        return ['.mock']


class TestExtractorFactory(unittest.TestCase):
    """Test cases for ExtractorFactory."""
    
    def test_create_router_default(self):
        """Test creating router with default extractors."""
        router = ExtractorFactory.create_router()
        
        self.assertIsInstance(router, ExtractorRouter)
        
        # Check that both HTML and Excel extractors are present
        extractor_names = [ext.get_extractor_name() for ext in router.extractors]
        self.assertIn('HTMLTableExtractor', extractor_names)
        self.assertIn('ExcelTableExtractor', extractor_names)
        
        # Check supported extensions
        extensions = router.get_supported_extensions()
        self.assertIn('.html', extensions)
        self.assertIn('.htm', extensions)
        self.assertIn('.xlsx', extensions)
        self.assertIn('.xls', extensions)
    
    def test_create_router_with_specific_extractors(self):
        """Test creating router with specific extractors."""
        router = ExtractorFactory.create_router(['html'])
        
        self.assertIsInstance(router, ExtractorRouter)
        self.assertEqual(len(router.extractors), 1)
        
        extractor_names = [ext.get_extractor_name() for ext in router.extractors]
        self.assertIn('HTMLTableExtractor', extractor_names)
        self.assertNotIn('ExcelTableExtractor', extractor_names)
        
        # Check supported extensions
        extensions = router.get_supported_extensions()
        self.assertIn('.html', extensions)
        self.assertIn('.htm', extensions)
        self.assertNotIn('.xlsx', extensions)
        self.assertNotIn('.xls', extensions)
    
    def test_create_router_with_unknown_extractor(self):
        """Test creating router with unknown extractor."""
        with self.assertRaises(ValueError) as context:
            ExtractorFactory.create_router(['unknown'])
        
        self.assertIn('Unknown extractor: unknown', str(context.exception))
        self.assertIn('Available:', str(context.exception))
    
    def test_create_extractor_html(self):
        """Test creating HTML extractor."""
        extractor = ExtractorFactory.create_extractor('html')
        
        self.assertIsInstance(extractor, HTMLTableExtractor)
        self.assertTrue(extractor.supports_file_type('test.html'))
    
    def test_create_extractor_excel(self):
        """Test creating Excel extractor."""
        extractor = ExtractorFactory.create_extractor('excel')
        
        self.assertIsInstance(extractor, ExcelTableExtractor)
        self.assertTrue(extractor.supports_file_type('test.xlsx'))
    
    def test_create_extractor_unknown(self):
        """Test creating unknown extractor."""
        with self.assertRaises(ValueError) as context:
            ExtractorFactory.create_extractor('unknown')
        
        self.assertIn('Unknown extractor type: unknown', str(context.exception))
    
    def test_get_extractor_for_file(self):
        """Test getting extractor for specific file."""
        html_extractor = ExtractorFactory.get_extractor_for_file('test.html')
        excel_extractor = ExtractorFactory.get_extractor_for_file('test.xlsx')
        
        self.assertIsInstance(html_extractor, HTMLTableExtractor)
        self.assertIsInstance(excel_extractor, ExcelTableExtractor)
    
    def test_get_extractor_for_file_with_custom_router(self):
        """Test getting extractor with custom router."""
        custom_router = ExtractorFactory.create_router(['html'])
        extractor = ExtractorFactory.get_extractor_for_file('test.html', custom_router)
        
        self.assertIsInstance(extractor, HTMLTableExtractor)
    
    def test_get_extractor_for_unsupported_file(self):
        """Test getting extractor for unsupported file."""
        with self.assertRaises(ValueError):
            ExtractorFactory.get_extractor_for_file('test.unsupported')
    
    def test_get_available_extractors(self):
        """Test getting available extractors info."""
        info = ExtractorFactory.get_available_extractors()
        
        self.assertIn('total_available', info)
        self.assertIn('extractors', info)
        
        # Check that we have at least HTML and Excel extractors
        self.assertGreaterEqual(info['total_available'], 2)
        self.assertIn('html', info['extractors'])
        self.assertIn('excel', info['extractors'])
        
        # Check extractor details
        html_info = info['extractors']['html']
        self.assertEqual(html_info['class_name'], 'HTMLTableExtractor')
        self.assertIn('.html', html_info['supported_extensions'])
        
        excel_info = info['extractors']['excel']
        self.assertEqual(excel_info['class_name'], 'ExcelTableExtractor')
        self.assertIn('.xlsx', excel_info['supported_extensions'])
    
    def test_register_extractor(self):
        """Test registering a new extractor."""
        # Register mock extractor
        ExtractorFactory.register_extractor('mock', MockExtractor)
        
        # Test it was registered
        info = ExtractorFactory.get_available_extractors()
        self.assertIn('mock', info['extractors'])
        
        # Test it can be created
        extractor = ExtractorFactory.create_extractor('mock')
        self.assertIsInstance(extractor, MockExtractor)
        
        # Clean up
        ExtractorFactory.unregister_extractor('mock')
    
    def test_register_invalid_extractor(self):
        """Test registering invalid extractor."""
        class NotAnExtractor:
            pass
        
        with self.assertRaises(ValueError) as context:
            ExtractorFactory.register_extractor('invalid', NotAnExtractor)
        
        self.assertIn('must inherit from BaseTableExtractor', str(context.exception))
    
    def test_unregister_extractor(self):
        """Test unregistering an extractor."""
        # Register and then unregister
        ExtractorFactory.register_extractor('mock', MockExtractor)
        removed = ExtractorFactory.unregister_extractor('mock')
        
        self.assertTrue(removed)
        
        # Test it's no longer available
        with self.assertRaises(ValueError):
            ExtractorFactory.create_extractor('mock')
    
    def test_unregister_nonexistent_extractor(self):
        """Test unregistering non-existent extractor."""
        removed = ExtractorFactory.unregister_extractor('nonexistent')
        self.assertFalse(removed)
    
    def test_create_custom_router(self):
        """Test creating router with custom extractors."""
        custom_extractors = [MockExtractor(), HTMLTableExtractor()]
        router = ExtractorFactory.create_custom_router(custom_extractors)
        
        self.assertIsInstance(router, ExtractorRouter)
        self.assertEqual(len(router.extractors), 2)
        
        extractor_names = [ext.get_extractor_name() for ext in router.extractors]
        self.assertIn('MockExtractor', extractor_names)
        self.assertIn('HTMLTableExtractor', extractor_names)
        
        # Test it works
        html_extractor = router.get_extractor('test.html')
        self.assertIsInstance(html_extractor, HTMLTableExtractor)


if __name__ == '__main__':
    unittest.main()