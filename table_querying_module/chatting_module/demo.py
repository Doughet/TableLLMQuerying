#!/usr/bin/env python3
"""
Demo script for the Chatting Module.

This script demonstrates how to use the chatting module programmatically.
"""

import os
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from chat_interface import ChatInterface


def demo_chatting():
    """Demonstrate the chatting module functionality."""
    
    print("🤖 Chatting Module Demo")
    print("=" * 40)
    
    # Get API key
    api_key = os.getenv("YOUR_API_KEY")
    if not api_key:
        print("❌ Error: YOUR_API_KEY environment variable not set")
        print("   Please set it with: export YOUR_API_KEY='your-key-here'")
        return
    
    # Check for database
    db_path = "table_querying.db"
    if not Path(db_path).exists():
        print(f"❌ Error: Database not found: {db_path}")
        print("   Please run the table processing module first to create sample data:")
        print("   python -m src.table_querying.main config/sample_table.html")
        return
    
    try:
        # Initialize chat interface
        print("🔌 Initializing chat interface...")
        chat = ChatInterface(db_path, api_key)
        
        # Show database summary
        summary = chat.get_database_summary()
        print(f"\n📊 Database contains:")
        print(f"   • {summary.get('total_tables', 0)} tables")
        print(f"   • {summary.get('total_data_rows', 0)} total rows")
        print(f"   • {summary.get('unique_source_files', 0)} source files")
        
        # Demo queries
        demo_queries = [
            "Show me all available tables",
            "Count how many tables we have in total",
            "What tables come from sample_table.html?",
            "Show me tables that have more than 2 rows"
        ]
        
        print(f"\n💬 Demo Queries:")
        print("-" * 40)
        
        for i, query in enumerate(demo_queries, 1):
            print(f"\n{i}. 🗣️  User: \"{query}\"")
            
            # Get SQL result
            result = chat.chat(query)
            
            if result == "IMPOSSIBLE":
                print("   🤖 Bot: This query cannot be fulfilled with the available data.")
            else:
                print("   🤖 Bot: Here's the SQL query:")
                print(f"        {result}")
                
                # Execute and show sample results
                try:
                    results = chat.execute_sql_query(result)
                    if results:
                        print(f"   📊 Results ({len(results)} rows):")
                        # Show first 2 results
                        for j, row in enumerate(results[:2]):
                            print(f"        Row {j+1}: {dict(row)}")
                        if len(results) > 2:
                            print(f"        ... and {len(results) - 2} more rows")
                    else:
                        print("   📊 No results returned")
                except Exception as e:
                    print(f"   ❌ Error executing query: {e}")
        
        print(f"\n✨ Demo completed!")
        print("   💡 Try the interactive mode:")
        print("   python -m src.chatting_module.main --db table_querying.db")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    demo_chatting()