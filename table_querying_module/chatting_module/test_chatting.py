#!/usr/bin/env python3
"""
Test script for the Chatting Module.

This script tests the chatting module with sample queries to ensure
all components work together correctly.
"""

import os
import sys
import logging
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from chat_interface import ChatInterface


def test_chatting_module():
    """Test the ChatInterface with sample queries."""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 Testing Chatting Module")
    print("=" * 50)
    
    # Get API key
    api_key = os.getenv("YOUR_API_KEY")
    if not api_key:
        print("❌ YOUR_API_KEY environment variable not set")
        return False
    
    # Find a database file to test with
    db_candidates = [
        "table_querying.db",
        "../table_querying.db", 
        "../../table_querying.db",
        "test_table_querying.db"
    ]
    
    db_path = None
    for candidate in db_candidates:
        if Path(candidate).exists():
            db_path = candidate
            break
    
    if not db_path:
        print("❌ No database file found. Please run the table processing module first.")
        print("   Expected files:", db_candidates)
        return False
    
    print(f"📄 Using database: {db_path}")
    
    try:
        # Initialize chat interface
        chat_interface = ChatInterface(db_path, api_key)
        
        # Show database summary
        summary = chat_interface.get_database_summary()
        print(f"\n📊 Database Summary:")
        print(f"  • Total Tables: {summary.get('total_tables', 0)}")
        print(f"  • Total Rows: {summary.get('total_data_rows', 0)}")
        print(f"  • Source Files: {summary.get('unique_source_files', 0)}")
        
        if summary.get('total_tables', 0) == 0:
            print("❌ No tables found in database")
            return False
        
        # Test queries
        test_queries = [
            "Show me all tables",
            "Count how many tables we have",
            "What tables come from sample_table.html?",
            "List all table IDs",
            "Show me the first table's information",
            "What's the weather today?",  # Should be impossible
            "Generate a random table",     # Should be impossible
            "Find tables with more than 2 rows"
        ]
        
        print(f"\n🔍 Testing {len(test_queries)} queries:")
        print("-" * 50)
        
        successful = 0
        impossible = 0
        errors = 0
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{i}. Query: '{query}'")
            
            try:
                result = chat_interface.chat(query)
                
                if result == "IMPOSSIBLE":
                    print("   Result: IMPOSSIBLE")
                    impossible += 1
                else:
                    print(f"   Result: {result}")
                    successful += 1
                    
                    # Try to execute the SQL to validate it
                    try:
                        execution_results = chat_interface.execute_sql_query(result)
                        print(f"   ✅ SQL executed successfully ({len(execution_results)} rows)")
                    except Exception as e:
                        print(f"   ⚠️  SQL generated but execution failed: {e}")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                errors += 1
        
        # Print summary
        print(f"\n{'='*60}")
        print("TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total Queries: {len(test_queries)}")
        print(f"✅ Successful SQL Generation: {successful}")
        print(f"⚠️  Marked as Impossible: {impossible}")
        print(f"❌ Errors: {errors}")
        print(f"Success Rate: {successful/len(test_queries)*100:.1f}%")
        
        # Expected results validation
        if successful >= 4:  # Should generate SQL for at least 4 basic queries
            print("✅ Test PASSED - Basic functionality working")
            return True
        else:
            print("❌ Test FAILED - Too few successful SQL generations")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_chatting_module()
    sys.exit(0 if success else 1)