#!/usr/bin/env python3
"""
Test script for the Table Querying Module.

This script tests the module with a sample HTML document to ensure
all components work together correctly.
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path to import the module
sys.path.append(str(Path(__file__).parent.parent))

from table_querying_module import TableProcessor
from table_querying_module.config import create_config_for_minecraft_wiki


def test_table_processor():
    """Test the TableProcessor with a sample HTML file."""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 Testing Table Querying Module")
    print("=" * 50)
    
    # Use a sample HTML file from the data directory
    test_file = Path(__file__).parent.parent / "data" / "mobs" / "Bee – Minecraft Wiki.html"
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        print("Please ensure you have HTML files in the data directory for testing.")
        return False
    
    print(f"📄 Test file: {test_file.name}")
    
    try:
        # Create configuration
        config = create_config_for_minecraft_wiki()
        config.output_dir = "table_querying_test_outputs"
        config.db_path = "test_table_querying.db"
        config.clear_database_on_start = True
        
        print(f"⚙️  Configuration:")
        print(f"  • Model: {config.model_id}")
        print(f"  • Context: {config.context_hint}")
        print(f"  • Database: {config.db_path}")
        print(f"  • Output dir: {config.output_dir}")
        
        # Initialize processor
        processor = TableProcessor(config.to_dict())
        
        # Process the document
        print(f"\n🚀 Starting document processing...")
        results = processor.process_document(str(test_file))
        
        # Print results
        processor.print_processing_summary(results)
        
        # Test database queries
        print(f"\n🔍 Testing database queries...")
        db_summary = processor.get_database_summary()
        print(f"Database contains {db_summary.get('total_tables', 0)} tables from {db_summary.get('unique_sources', 0)} sources")
        
        # Query tables for this source
        table_info = processor.query_tables_by_source(str(test_file))
        print(f"Found {len(table_info)} tables for this document:")
        for table in table_info[:3]:  # Show first 3 tables
            print(f"  • Table {table['table_id']}: {table['rows']}×{table['columns']} - {table['description'][:100]}...")
        
        # Success check
        if results.get('success', False):
            print(f"\n✅ Module test completed successfully!")
            print(f"📊 Processed {results['statistics']['html_tables']} tables")
            print(f"💾 Generated {results['statistics']['successful_descriptions']} descriptions")
            print(f"🔄 Replaced {results['statistics']['table_replacements']} tables in document")
            return True
        else:
            print(f"\n❌ Module test failed: {results.get('error', 'Unknown error')}")
            return False
    
    except Exception as e:
        print(f"\n❌ Module test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_components_individually():
    """Test individual components to isolate any issues."""
    
    print("\n🔧 Testing individual components...")
    
    try:
        # Test TableExtractor
        from table_querying_module.table_extractor import TableExtractor
        extractor = TableExtractor()
        print("✅ TableExtractor imported and initialized")
        
        # Test SchemaProcessor
        from table_querying_module.schema_processor import SchemaProcessor
        schema_proc = SchemaProcessor()
        print("✅ SchemaProcessor imported and initialized")
        
        # Test TableSummarizer (this might fail if API key is invalid)
        try:
            from table_querying_module.table_summarizer import TableSummarizer
            summarizer = TableSummarizer()
            print("✅ TableSummarizer imported and initialized")
        except Exception as e:
            print(f"⚠️  TableSummarizer failed: {e}")
            print("   This is likely due to API key issues - check YOUR_API_KEY environment variable")
        
        # Test TableDatabase
        from table_querying_module.table_database import TableDatabase
        db = TableDatabase("test_components.db")
        print("✅ TableDatabase imported and initialized")
        
        # Test DocumentProcessor
        from table_querying_module.document_processor import DocumentProcessor
        doc_proc = DocumentProcessor()
        print("✅ DocumentProcessor imported and initialized")
        
        print("✅ All components imported successfully")
        return True
        
    except Exception as e:
        print(f"❌ Component test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function."""
    
    print("🚀 Table Querying Module Test Suite")
    print("=" * 60)
    
    # Test 1: Component imports
    print("Test 1: Testing component imports...")
    if not test_components_individually():
        print("❌ Component test failed - stopping here")
        return False
    
    print(f"\n{'='*60}")
    
    # Test 2: Full integration test
    print("Test 2: Testing full integration...")
    success = test_table_processor()
    
    if success:
        print(f"\n🎉 All tests passed! Table Querying Module is working correctly.")
        print(f"\nYou can now use the module with:")
        print(f"python -m table_querying_module.main your_document.html")
    else:
        print(f"\n❌ Integration test failed.")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)