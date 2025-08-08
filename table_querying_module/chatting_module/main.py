#!/usr/bin/env python3
"""
Main CLI interface for the Chatting Module.

This script provides a command-line interface for querying processed table data
using natural language queries.
"""

import argparse
import sys
import logging
import os
from pathlib import Path
from typing import Optional

try:
    from .chat_interface import ChatInterface
except ImportError:
    from chat_interface import ChatInterface


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def interactive_mode(chat_interface: ChatInterface):
    """Run in interactive mode for continuous querying."""
    print("🤖 Table Query Chat Interface")
    print("=" * 50)
    print("Ask questions about your table data. Type 'quit' to exit.")
    print("Examples:")
    print("  - 'Show me all tables from minecraft files'")
    print("  - 'Count how many rows are in the inventory table'")
    print("  - 'What columns does the first table have?'")
    print()
    
    # Show database summary
    summary = chat_interface.get_database_summary()
    print(f"📊 Database Summary:")
    print(f"  • Total Tables: {summary.get('total_tables', 0)}")
    print(f"  • Total Rows: {summary.get('total_data_rows', 0)}")
    print(f"  • Source Files: {summary.get('unique_source_files', 0)}")
    print()
    
    while True:
        try:
            user_input = input("❓ Your question: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            # Process query
            print("🤔 Analyzing your query...")
            result = chat_interface.chat(user_input)
            
            if result == "IMPOSSIBLE":
                print("❌ This query cannot be fulfilled with the available table data.")
                print("   Try asking about table contents, counts, filtering, or aggregations.")
            else:
                print("✅ Generated SQL Query:")
                print(f"   {result}")
                
                # Optionally execute and show results
                execute = input("🔍 Execute this query and show results? (y/n): ").strip().lower()
                if execute in ['y', 'yes']:
                    try:
                        results = chat_interface.execute_sql_query(result)
                        if results:
                            print(f"\n📋 Results ({len(results)} rows):")
                            # Show first few results
                            for i, row in enumerate(results[:5]):
                                print(f"  Row {i+1}: {row}")
                            if len(results) > 5:
                                print(f"  ... and {len(results) - 5} more rows")
                        else:
                            print("📋 No results returned.")
                    except Exception as e:
                        print(f"❌ Error executing query: {e}")
            
            print()
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def single_query_mode(chat_interface: ChatInterface, query: str):
    """Process a single query and return result."""
    result = chat_interface.chat(query)
    
    if result == "IMPOSSIBLE":
        print("IMPOSSIBLE")
        return 1
    else:
        print(result)
        return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Chat with your table data using natural language queries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python -m chatting_module.main --db tables.db
  
  # Single query
  python -m chatting_module.main --db tables.db --query "Count all tables"
  
  # With custom API key
  python -m chatting_module.main --db tables.db --api-key "your-key" --query "Show me data from minecraft tables"
        """
    )
    
    parser.add_argument(
        '--db', '--database',
        required=True,
        help='Path to the SQLite database file with processed tables'
    )
    parser.add_argument(
        '--query', '-q',
        help='Single query to process (if not provided, enters interactive mode)'
    )
    parser.add_argument(
        '--api-key',
        help='BHub API key for LLM processing (can also use YOUR_API_KEY env var)'
    )
    parser.add_argument(
        '--model-id',
        default='mistral-small',
        help='LLM model ID to use (default: mistral-small)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--list-tables',
        action='store_true',
        help='List all available tables and exit'
    )
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Show database summary and exit'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Get API key
    api_key = args.api_key or os.getenv('YOUR_API_KEY')
    if not api_key:
        print("❌ Error: API key is required. Set YOUR_API_KEY environment variable or use --api-key")
        return 1
    
    # Check database exists
    if not Path(args.db).exists():
        print(f"❌ Error: Database file not found: {args.db}")
        return 1
    
    try:
        # Initialize chat interface
        chat_interface = ChatInterface(args.db, api_key, args.model_id)
        
        # Handle special modes
        if args.list_tables:
            tables = chat_interface.list_available_tables()
            print(f"📊 Available Tables ({len(tables)}):")
            for table in tables:
                print(f"  • {table['table_id']} ({table.get('source_file', 'unknown')})")
                print(f"    Rows: {table.get('actual_rows', 0)}, Columns: {table.get('columns', 0)}")
                if table.get('description'):
                    desc = table['description'][:100] + "..." if len(table['description']) > 100 else table['description']
                    print(f"    Description: {desc}")
                print()
            return 0
        
        if args.summary:
            summary = chat_interface.get_database_summary()
            print("📊 Database Summary:")
            for key, value in summary.items():
                if key == 'sample_tables':
                    print(f"  {key}:")
                    for table in value:
                        print(f"    • {table['table_id']}: {table['rows']} rows, {table['columns']} cols")
                else:
                    print(f"  {key}: {value}")
            return 0
        
        # Process query
        if args.query:
            return single_query_mode(chat_interface, args.query)
        else:
            interactive_mode(chat_interface)
            return 0
    
    except Exception as e:
        print(f"❌ Error initializing chat interface: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())