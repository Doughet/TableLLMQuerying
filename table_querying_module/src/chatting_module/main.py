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

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Look for .env file in current dir, parent dirs, and project root
    current_dir = Path(__file__).parent
    for i in range(5):  # Check up to 5 levels up
        env_path = current_dir / '.env'
        if env_path.exists():
            load_dotenv(env_path)
            break
        current_dir = current_dir.parent
except ImportError:
    # python-dotenv not installed, skip
    pass

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


def interactive_mode(chat_interface: ChatInterface, enable_save: bool = False):
    """Run in interactive mode for continuous querying."""
    print("🤖 Table Query Chat Interface")
    print("=" * 50)
    print("Ask questions about your table data. Type 'quit' to exit.")
    print("Special commands:")
    print("  - 'help' - Show this help message")
    print("  - 'tables' - List all available tables")
    print("  - 'summary' - Show database summary")
    if enable_save:
        print("  - 'save <format>' - Save last results (csv, json, txt)")
    print("\nExamples:")
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
    
    # Store last results for saving
    last_results = []
    last_sql = ""
    
    while True:
        try:
            user_input = input("❓ Your question: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            # Handle special commands
            if user_input.lower() == 'help':
                print("Special commands:")
                print("  - 'tables' - List all available tables")
                print("  - 'summary' - Show database summary")
                if enable_save:
                    print("  - 'save <format>' - Save last results (csv, json, txt)")
                continue
            
            elif user_input.lower() == 'tables':
                tables = chat_interface.list_available_tables()
                print(f"📊 Available Tables ({len(tables)}):")
                for table in tables:
                    print(f"  • {table['table_id']} ({table.get('source_file', 'unknown')})")
                    print(f"    Rows: {table.get('actual_rows', 0)}, Columns: {table.get('columns', 0)}")
                    if table.get('description'):
                        print(f"    Description: {table['description']}")
                    print()
                continue
            
            elif user_input.lower() == 'summary':
                print("📊 Database Summary:")
                for key, value in summary.items():
                    if key == 'sample_tables':
                        print(f"  {key}:")
                        for table in value:
                            print(f"    • {table['table_id']}: {table['rows']} rows, {table['columns']} cols")
                    else:
                        print(f"  {key}: {value}")
                continue
            
            elif user_input.lower().startswith('save ') and enable_save:
                if not last_results:
                    print("❌ No previous results to save. Execute a query first.")
                    continue
                
                format_part = user_input[5:].strip().lower()
                if format_part not in ['csv', 'json', 'txt']:
                    print("❌ Invalid format. Use: csv, json, or txt")
                    continue
                
                try:
                    filepath = chat_interface.save_last_results(last_results, last_sql, format_part)
                    print(f"✅ Results saved to: {filepath}")
                except Exception as e:
                    print(f"❌ Save failed: {e}")
                continue
            
            # Process regular query
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
                        last_results = results  # Store for potential saving
                        last_sql = result
                        
                        if results:
                            print(f"\n📋 Results ({len(results)} rows):")
                            # Show all results (removed limit)
                            for i, row in enumerate(results, 1):
                                print(f"  Row {i}: {row}")
                            
                            # Offer to save if enabled
                            if enable_save and len(results) > 0:
                                save_option = input(f"\n💾 Save these {len(results)} results to file? (y/n): ").strip().lower()
                                if save_option in ['y', 'yes']:
                                    format_choice = input("📄 Format (csv/json/txt): ").strip().lower() or 'csv'
                                    if format_choice in ['csv', 'json', 'txt']:
                                        try:
                                            filepath = chat_interface.save_last_results(results, result, format_choice)
                                            print(f"✅ Results saved to: {filepath}")
                                        except Exception as e:
                                            print(f"❌ Save failed: {e}")
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


def single_query_mode(chat_interface: ChatInterface, 
                     query: str,
                     save_results: bool = False,
                     export_format: str = "csv",
                     export_filename: Optional[str] = None) -> int:
    """Process a single query and optionally save results."""
    if save_results:
        # Use execute_and_save for automatic saving
        result = chat_interface.execute_and_save(
            user_query=query,
            format=export_format,
            filename=export_filename
        )
        
        if result['success']:
            print(f"✅ Query executed successfully!")
            print(f"📊 Found {result['result_count']} results")
            print(f"💾 Saved to: {result['export_path']}")
            print(f"🔍 SQL Query: {result['sql_query']}")
            return 0
        else:
            print(f"❌ Query failed: {result['error']}")
            if 'sql_query' in result:
                print(f"🔍 Generated SQL: {result['sql_query']}")
            return 1
    else:
        # Original behavior - just return SQL
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
  
  # Interactive mode with result saving enabled
  python -m chatting_module.main --db tables.db --save-results --output-dir results/
  
  # Single query (just get SQL)
  python -m chatting_module.main --db tables.db --query "Count all tables"
  
  # Single query with automatic result saving
  python -m chatting_module.main --db tables.db --query "Show me all minecraft tables" --save-results --export-format json
  
  # Custom output directory and filename
  python -m chatting_module.main --db tables.db --query "Count rows per table" --save-results --output-dir exports/ --export-filename table_counts
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
        help='OpenAI API key for LLM processing (can also use OPENAI_API_KEY env var)'
    )
    parser.add_argument(
        '--model-id',
        default='gpt-3.5-turbo',
        help='LLM model ID to use (default: gpt-3.5-turbo)'
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
    parser.add_argument(
        '--save-results',
        action='store_true',
        help='Save query results to file after execution'
    )
    parser.add_argument(
        '--output-dir',
        help='Directory to save query results (default: current directory)'
    )
    parser.add_argument(
        '--export-format',
        choices=['csv', 'json', 'txt'],
        default='csv',
        help='Export format for saved results (default: csv)'
    )
    parser.add_argument(
        '--export-filename',
        help='Custom filename for exported results (without extension)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Get API key
    api_key = args.api_key or os.getenv('OPENAI_API_KEY') or os.getenv('API_KEY')
    if not api_key:
        print("❌ Error: API key is required. Set OPENAI_API_KEY environment variable or use --api-key")
        return 1
    
    # Check database exists
    if not Path(args.db).exists():
        print(f"❌ Error: Database file not found: {args.db}")
        return 1
    
    try:
        # Initialize chat interface with output directory if provided
        chat_interface = ChatInterface(args.db, api_key, args.model_id, args.output_dir)
        
        # Handle special modes
        if args.list_tables:
            tables = chat_interface.list_available_tables()
            print(f"📊 Available Tables ({len(tables)}):")
            for table in tables:
                print(f"  • {table['table_id']} ({table.get('source_file', 'unknown')})")
                print(f"    Rows: {table.get('actual_rows', 0)}, Columns: {table.get('columns', 0)}")
                if table.get('description'):
                    print(f"    Description: {table['description']}")
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
            return single_query_mode(
                chat_interface, 
                args.query,
                save_results=args.save_results,
                export_format=args.export_format,
                export_filename=args.export_filename
            )
        else:
            interactive_mode(chat_interface, enable_save=args.save_results)
            return 0
    
    except Exception as e:
        print(f"❌ Error initializing chat interface: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())