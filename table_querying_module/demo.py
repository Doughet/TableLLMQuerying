#!/usr/bin/env python3
"""
Standalone demo script for the Table Querying Module.

This script demonstrates the basic functionality using the included sample HTML file.
"""

import sys
from pathlib import Path

# Import the table querying module
try:
    from config import create_default_config
    from table_processor import TableProcessor
except ImportError:
    print("❌ Could not import table_querying_module components")
    print("Make sure you're running this from the table_querying_module directory")
    sys.exit(1)


def run_demo():
    """Run a demonstration of the Table Querying Module."""
    
    print("🚀 Table Querying Module - Standalone Demo")
    print("=" * 55)
    
    # Use the sample HTML file
    sample_file = "examples/sample_table.html"
    
    if not Path(sample_file).exists():
        print(f"❌ Sample file not found: {sample_file}")
        print("Make sure you're running this from the table_querying_module directory")
        return False
    
    print(f"📄 Processing sample file: {Path(sample_file).name}")
    
    # Create configuration
    config = create_default_config()
    config.output_dir = "demo_outputs"
    config.db_path = "demo.db"
    config.clear_database_on_start = True
    config.context_hint = "Gaming/Minecraft"
    
    print(f"⚙️  Configuration:")
    print(f"  • Model: {config.model_id}")
    print(f"  • Context: {config.context_hint}")
    print(f"  • Output: {config.output_dir}")
    print(f"  • Database: {config.db_path}")
    
    try:
        # Initialize processor
        processor = TableProcessor(config.to_dict())
        
        # Process the document
        print(f"\n🔄 Processing document...")
        results = processor.process_document(sample_file)
        
        # Display results
        processor.print_processing_summary(results)
        
        if results.get('success', False):
            print(f"\n🎉 Demo completed successfully!")
            
            # Show what was accomplished
            stats = results.get('statistics', {})
            print(f"\n📊 What the module accomplished:")
            print(f"  ✅ Extracted {stats.get('html_tables', 0)} HTML tables")
            print(f"  ✅ Generated {stats.get('successful_schemas', 0)} table schemas")
            print(f"  ✅ Created {stats.get('successful_descriptions', 0)} AI descriptions")
            print(f"  ✅ Stored {stats.get('stored_tables', 0)} tables in database")
            print(f"  ✅ Replaced {stats.get('table_replacements', 0)} tables with descriptions")
            print(f"  ✅ Reduced document size by {abs(stats.get('content_size_change', 0)):,} characters")
            
            print(f"\n📁 Check the '{config.output_dir}' directory for:")
            print(f"  • 📄 Processed document with table descriptions")
            print(f"  • 📊 Table schemas and metadata")
            print(f"  • 🤖 AI-generated descriptions")
            print(f"  • 📋 Detailed processing report")
            
            print(f"\n💡 The sample document demonstrates how complex tables")
            print(f"   are replaced with clear, natural language summaries!")
            
        else:
            print(f"\n❌ Demo failed: {results.get('error', 'Unknown error')}")
            return False
    
    except Exception as e:
        print(f"\n❌ Demo failed with exception: {e}")
        print(f"\n🔧 Troubleshooting tips:")
        print(f"  • Make sure you have set YOUR_API_KEY environment variable")
        print(f"  • Check that all dependencies are installed: pip install -r requirements.txt")
        print(f"  • Ensure you're running from the table_querying_module directory")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def main():
    """Main demo function."""
    success = run_demo()
    
    if success:
        print(f"\n✅ Table Querying Module is working perfectly!")
        print(f"\nNext steps:")
        print(f"  1. Try processing your own HTML files")
        print(f"  2. Explore the configuration options")
        print(f"  3. Query the database for stored tables")
        print(f"  4. Use the CLI: python main.py your_document.html")
        
    else:
        print(f"\n❌ Demo encountered issues. Check the error messages above.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())