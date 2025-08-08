#!/usr/bin/env python3
"""
Full Pipeline Script for Table Processing and Interactive Chatting.

This script provides a complete workflow that:
1. Checks if tables have already been processed from the input file
2. If not processed, runs the complete table processing pipeline
3. Enters an interactive chatting phase where users can ask questions about the database

Usage:
    python full_pipeline.py document.html
    python full_pipeline.py --directory /path/to/html/files
    python full_pipeline.py --interactive-only  # Skip processing, go straight to chat
"""

import argparse
import sys
import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import sqlite3

# Import table processing modules
try:
    from src.table_querying.config import TableProcessingConfig, create_default_config, create_config_for_minecraft_wiki
    from src.table_querying.table_processor import TableProcessor
    from src.chatting_module.chat_interface import ChatInterface
except ImportError:
    try:
        from table_querying.config import TableProcessingConfig, create_default_config, create_config_for_minecraft_wiki
        from table_querying.table_processor import TableProcessor
        from chatting_module.chat_interface import ChatInterface
    except ImportError:
        print("❌ Error: Could not import required modules.")
        print("   Make sure you're running from the table_querying_module directory")
        print("   or install the module with: pip install -e .")
        sys.exit(1)


class FullPipeline:
    """Complete pipeline for table processing and interactive chatting."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, verbose: bool = False):
        """
        Initialize the full pipeline.
        
        Args:
            config: Configuration dictionary for table processing
            verbose: Enable verbose logging
        """
        self.verbose = verbose
        self.setup_logging()
        
        # Configuration
        if config:
            self.config = TableProcessingConfig.from_dict(config)
        else:
            self.config = create_default_config()
        
        # Database path
        self.db_path = self.config.db_path or "table_querying.db"
        
        # Initialize table processor
        self.table_processor = None
        self.chat_interface = None
        
        self.logger.info("FullPipeline initialized")
    
    def setup_logging(self):
        """Setup logging configuration."""
        level = logging.DEBUG if self.verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)
    
    def check_file_already_processed(self, html_file: str) -> tuple[bool, int]:
        """
        Check if a file has already been processed.
        
        Args:
            html_file: Path to HTML file
            
        Returns:
            Tuple of (is_processed, table_count)
        """
        if not Path(self.db_path).exists():
            return False, 0
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Try multiple path formats since the database might store relative or absolute paths
                input_path = Path(html_file)
                possible_paths = [
                    str(input_path),                    # As provided
                    str(input_path.resolve()),          # Absolute path
                    str(input_path.name),               # Just filename  
                    str(input_path.relative_to(Path.cwd()) if input_path.is_absolute() else input_path)  # Relative to cwd
                ]
                
                # Remove duplicates while preserving order
                seen = set()
                unique_paths = []
                for path in possible_paths:
                    if path not in seen:
                        seen.add(path)
                        unique_paths.append(path)
                
                self.logger.debug(f"Checking for paths: {unique_paths}")
                
                # Check each possible path format
                for check_path in unique_paths:
                    cursor.execute('''
                        SELECT COUNT(*) FROM tables WHERE source_file = ?
                    ''', (check_path,))
                    
                    count = cursor.fetchone()[0]
                    if count > 0:
                        self.logger.debug(f"Found match with path: {check_path}")
                        return True, count
                
                return False, 0
                
        except sqlite3.Error as e:
            self.logger.warning(f"Database error while checking processed files: {e}")
            return False, 0
    
    def initialize_table_processor(self):
        """Initialize the table processor if not already initialized."""
        if self.table_processor is None:
            self.table_processor = TableProcessor(self.config.to_dict())
    
    def initialize_chat_interface(self):
        """Initialize the chat interface if not already initialized."""
        if self.chat_interface is None:
            api_key = self.config.api_key or os.getenv("YOUR_API_KEY")
            if not api_key:
                raise ValueError("API key is required for chatting. Set YOUR_API_KEY environment variable or provide --api-key")
            
            self.chat_interface = ChatInterface(
                db_path=self.db_path,
                api_key=api_key,
                model_id=self.config.model_id or "mistral-small"
            )
    
    def process_single_file(self, html_file: str, force_reprocess: bool = False) -> Dict[str, Any]:
        """
        Process a single HTML file through the complete pipeline.
        
        Args:
            html_file: Path to HTML file
            force_reprocess: Force reprocessing even if already processed
            
        Returns:
            Processing results dictionary
        """
        html_path = Path(html_file)
        if not html_path.exists():
            raise FileNotFoundError(f"HTML file not found: {html_file}")
        
        print(f"🔍 Checking if {html_path.name} has already been processed...")
        
        # Check if already processed
        is_processed, table_count = self.check_file_already_processed(html_file)
        
        if is_processed and not force_reprocess:
            print(f"✅ File already processed ({table_count} tables found in database)")
            print("   Skipping table processing step...")
            return {
                'success': True,
                'skipped': True,
                'html_file': html_file,
                'existing_tables': table_count,
                'message': 'File already processed, skipped processing step'
            }
        
        elif is_processed and force_reprocess:
            print(f"⚠️  File already processed ({table_count} tables found)")
            print("   Force reprocess enabled, processing anyway...")
        
        else:
            print(f"📄 File not yet processed, starting table processing...")
        
        # Initialize and run table processing
        self.initialize_table_processor()
        
        print(f"\n{'='*20} PROCESSING PHASE {'='*20}")
        results = self.table_processor.process_document(html_file)
        
        if results.get('success', False):
            stats = results.get('statistics', {})
            print(f"✅ Processing completed successfully!")
            print(f"   • {stats.get('stored_tables', 0)} tables stored in database")
            print(f"   • {stats.get('successful_descriptions', 0)} table descriptions generated")
        else:
            print(f"❌ Processing failed: {results.get('error', 'Unknown error')}")
        
        return results
    
    def process_multiple_files(self, html_files: List[str], force_reprocess: bool = False) -> List[Dict[str, Any]]:
        """
        Process multiple HTML files.
        
        Args:
            html_files: List of HTML file paths
            force_reprocess: Force reprocessing even if already processed
            
        Returns:
            List of processing results
        """
        print(f"📁 Processing {len(html_files)} HTML files...")
        
        all_results = []
        skipped = 0
        processed = 0
        failed = 0
        
        for i, html_file in enumerate(html_files, 1):
            print(f"\n{'='*15} FILE {i}/{len(html_files)} {'='*15}")
            print(f"File: {Path(html_file).name}")
            
            try:
                result = self.process_single_file(html_file, force_reprocess)
                all_results.append(result)
                
                if result.get('skipped', False):
                    skipped += 1
                elif result.get('success', False):
                    processed += 1
                else:
                    failed += 1
                    
            except Exception as e:
                self.logger.error(f"Error processing {html_file}: {e}")
                all_results.append({
                    'success': False,
                    'html_file': html_file,
                    'error': str(e)
                })
                failed += 1
        
        # Print batch summary
        print(f"\n{'='*50}")
        print("BATCH PROCESSING SUMMARY")
        print(f"{'='*50}")
        print(f"Total Files: {len(html_files)}")
        print(f"✅ Successfully Processed: {processed}")
        print(f"⏭️  Skipped (Already Processed): {skipped}")
        print(f"❌ Failed: {failed}")
        
        return all_results
    
    def start_interactive_chat(self):
        """Start the interactive chatting phase."""
        print(f"\n{'='*20} CHATTING PHASE {'='*20}")
        
        # Initialize chat interface
        try:
            self.initialize_chat_interface()
        except Exception as e:
            print(f"❌ Failed to initialize chat interface: {e}")
            return
        
        # Get database summary
        try:
            summary = self.chat_interface.get_database_summary()
            print(f"\n📊 Database Summary:")
            print(f"  • Total Tables: {summary.get('total_tables', 0)}")
            print(f"  • Total Rows: {summary.get('total_data_rows', 0)}")
            print(f"  • Source Files: {summary.get('unique_source_files', 0)}")
            
            if summary.get('total_tables', 0) == 0:
                print("\n❌ No tables found in database. Please process some HTML files first.")
                return
            
        except Exception as e:
            print(f"⚠️  Warning: Could not get database summary: {e}")
        
        print(f"\n🤖 Interactive Chat Mode Started!")
        print("=" * 50)
        print("Ask questions about your table data in natural language.")
        print("The system will generate SQL queries to answer your questions.")
        print("Type 'help' for examples, 'summary' for database info, or 'quit' to exit.")
        print("=" * 50)
        
        # Interactive chat loop
        while True:
            try:
                user_input = input("\n💬 Your question: ").strip()
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                elif user_input.lower() == 'help':
                    self._show_help()
                    continue
                
                elif user_input.lower() == 'summary':
                    try:
                        summary = self.chat_interface.get_database_summary()
                        self._print_database_summary(summary)
                    except Exception as e:
                        print(f"❌ Error getting summary: {e}")
                    continue
                
                elif user_input.lower() == 'tables':
                    try:
                        tables = self.chat_interface.list_available_tables()
                        self._print_available_tables(tables)
                    except Exception as e:
                        print(f"❌ Error listing tables: {e}")
                    continue
                
                elif user_input.lower() == 'dump':
                    try:
                        self._dump_database_content()
                    except Exception as e:
                        print(f"❌ Error dumping database: {e}")
                    continue
                
                # Process the question
                print("🔍 Analyzing your question...")
                
                try:
                    result = self.chat_interface.chat(user_input)
                    
                    if result == "IMPOSSIBLE":
                        print("❌ Query Result: IMPOSSIBLE")
                        print("   Your question cannot be answered with the available table data.")
                    else:
                        print(f"✅ Generated SQL Query:")
                        print(f"   {result}")
                        
                        # Optionally execute the query to show results
                        if input("\n🔍 Execute this query to see results? (y/N): ").lower().startswith('y'):
                            try:
                                query_results = self.chat_interface.execute_sql_query(result)
                                self._print_query_results(query_results)
                            except Exception as e:
                                print(f"❌ Error executing query: {e}")
                
                except Exception as e:
                    print(f"❌ Error processing question: {e}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted by user. Goodbye!")
                break
            except EOFError:
                print("\n\n👋 End of input. Goodbye!")
                break
    
    def _show_help(self):
        """Show help information for the interactive chat."""
        print("\n" + "="*50)
        print("HELP - Example Questions You Can Ask:")
        print("="*50)
        print("• 'Show me all tables'")
        print("• 'Count how many tables we have'") 
        print("• 'List all table IDs'")
        print("• 'What tables come from sample.html?'")
        print("• 'Show me tables with more than 5 rows'")
        print("• 'Find tables that contain the word \"price\"'")
        print("\nSpecial Commands:")
        print("• 'help' - Show this help")
        print("• 'summary' - Show database summary")
        print("• 'tables' - List all available tables")
        print("• 'dump' - Show all database content")
        print("• 'quit' or 'exit' - Exit the chat")
        print("="*50)
    
    def _print_database_summary(self, summary: Dict[str, Any]):
        """Print formatted database summary."""
        print("\n" + "="*40)
        print("DATABASE SUMMARY")
        print("="*40)
        print(f"📊 Total Tables: {summary.get('total_tables', 0)}")
        print(f"📄 Total Data Rows: {summary.get('total_data_rows', 0)}")
        print(f"📁 Source Files: {summary.get('unique_source_files', 0)}")
        
        if summary.get('source_files'):
            print(f"\n📁 Source Files:")
            for i, source in enumerate(summary['source_files'][:5], 1):  # Show first 5
                print(f"   {i}. {Path(source).name}")
            if len(summary['source_files']) > 5:
                print(f"   ... and {len(summary['source_files']) - 5} more")
        
        if summary.get('sample_tables'):
            print(f"\n📋 Sample Tables:")
            for i, table in enumerate(summary['sample_tables'], 1):
                desc = table.get('description', 'No description')
                print(f"   {i}. {table.get('table_id', 'Unknown')} ({table.get('rows', 0)} rows)")
                print(f"      {desc[:60]}{'...' if len(desc) > 60 else ''}")
        
        print("="*40)
    
    def _print_available_tables(self, tables: List[Dict[str, Any]]):
        """Print list of available tables."""
        print(f"\n📋 Available Tables ({len(tables)} total):")
        print("-" * 60)
        
        for i, table in enumerate(tables, 1):
            source = Path(table.get('source_file', 'Unknown')).name
            rows = table.get('actual_rows', table.get('rows', 0))
            cols = table.get('columns', 0)
            desc = table.get('description', 'No description available')
            
            print(f"{i:2d}. {table.get('table_id', 'Unknown ID')}")
            print(f"    Source: {source}")
            print(f"    Size: {rows} rows × {cols} columns")
            print(f"    Description: {desc[:80]}{'...' if len(desc) > 80 else ''}")
            print()
    
    def _print_query_results(self, results: List[Dict[str, Any]]):
        """Print SQL query results in a formatted table."""
        if not results:
            print("📄 No results returned from query.")
            return
        
        print(f"\n📊 Query Results ({len(results)} rows):")
        print("-" * 60)
        
        # Show first few results
        max_results = 10
        for i, row in enumerate(results[:max_results], 1):
            print(f"Row {i}:")
            for key, value in row.items():
                # Truncate long values
                str_value = str(value)
                if len(str_value) > 100:
                    str_value = str_value[:100] + "..."
                print(f"  {key}: {str_value}")
            print()
        
        if len(results) > max_results:
            print(f"... and {len(results) - max_results} more rows")
        
        print(f"Total: {len(results)} rows")
    
    def _dump_database_content(self):
        """Dump all database content in a readable format."""
        print("\n" + "="*70)
        print("DATABASE CONTENT DUMP")
        print("="*70)
        
        try:
            import sqlite3
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row  # Enable column access by name
                cursor = conn.cursor()
                
                # 1. Processing Sessions
                print("\n📅 PROCESSING SESSIONS:")
                print("-" * 50)
                cursor.execute("""
                    SELECT session_id, source_file, total_tables, successful_tables, created_at, metadata
                    FROM processing_sessions 
                    ORDER BY created_at DESC
                """)
                sessions = cursor.fetchall()
                
                if sessions:
                    for session in sessions:
                        print(f"Session: {session['session_id']}")
                        print(f"  Source: {session['source_file']}")
                        print(f"  Tables: {session['successful_tables']}/{session['total_tables']}")
                        print(f"  Created: {session['created_at']}")
                        if session['metadata']:
                            print(f"  Metadata: {session['metadata']}")
                        print()
                else:
                    print("  No processing sessions found.")
                
                # 2. Tables Metadata
                print("\n📋 TABLES METADATA:")
                print("-" * 50)
                cursor.execute("""
                    SELECT table_id, source_file, rows, columns, column_names, column_types, 
                           created_at, description, processing_session
                    FROM tables 
                    ORDER BY created_at DESC
                """)
                tables = cursor.fetchall()
                
                if tables:
                    for table in tables:
                        print(f"Table: {table['table_id']}")
                        print(f"  Source: {table['source_file']}")
                        print(f"  Dimensions: {table['rows']} rows × {table['columns']} columns")
                        print(f"  Columns: {table['column_names']}")
                        print(f"  Types: {table['column_types']}")
                        print(f"  Session: {table['processing_session']}")
                        print(f"  Created: {table['created_at']}")
                        if table['description']:
                            print(f"  Description: {table['description']}")
                        print()
                else:
                    print("  No table metadata found.")
                
                # 3. Complete Table Data
                print("\n📊 COMPLETE TABLE DATA:")
                print("-" * 50)
                
                # Get unique table IDs
                cursor.execute("SELECT DISTINCT table_id FROM table_data ORDER BY table_id")
                table_ids = [row[0] for row in cursor.fetchall()]
                
                if table_ids:
                    for table_id in table_ids:
                        print(f"\nTable: {table_id}")
                        cursor.execute("""
                            SELECT row_index, row_data 
                            FROM table_data 
                            WHERE table_id = ? 
                            ORDER BY row_index
                        """, (table_id,))
                        
                        rows = cursor.fetchall()
                        if rows:
                            print("  All rows:")
                            for row in rows:
                                try:
                                    import json
                                    row_data = json.loads(row['row_data'])
                                    print(f"    Row {row['row_index']}: {row_data}")
                                except Exception as e:
                                    print(f"    Row {row['row_index']}: {row['row_data']} (JSON parse error: {e})")
                        
                        print(f"  Total rows: {len(rows)}")
                else:
                    print("  No table data found.")
                
                # 4. Database Statistics
                print("\n📈 DATABASE STATISTICS:")
                print("-" * 50)
                cursor.execute("SELECT COUNT(*) FROM processing_sessions")
                session_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM tables")
                table_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM table_data")
                data_row_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(DISTINCT source_file) FROM tables")
                unique_sources = cursor.fetchone()[0]
                
                print(f"Processing Sessions: {session_count}")
                print(f"Tables: {table_count}")
                print(f"Data Rows: {data_row_count}")
                print(f"Unique Sources: {unique_sources}")
                
                # Database file size
                db_path = Path(self.db_path)
                if db_path.exists():
                    db_size = db_path.stat().st_size
                    print(f"Database Size: {db_size:,} bytes ({db_size/1024:.1f} KB)")
                
                print("="*70)
                print("END OF DATABASE DUMP")
                print("="*70)
                
        except Exception as e:
            print(f"❌ Error dumping database: {e}")


def discover_html_files(directory: str, recursive: bool = False) -> List[str]:
    """Discover HTML files in a directory."""
    path = Path(directory)
    
    if not path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    if not path.is_dir():
        raise ValueError(f"Path is not a directory: {directory}")
    
    pattern = "**/*.html" if recursive else "*.html"
    html_files = list(path.glob(pattern))
    
    # Also check for .htm files
    htm_pattern = "**/*.htm" if recursive else "*.htm"
    html_files.extend(path.glob(htm_pattern))
    
    return [str(f) for f in html_files]


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Full Pipeline - Table Processing and Interactive Chatting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single file and start chat
  python full_pipeline.py document.html
  
  # Process directory and start chat
  python full_pipeline.py --directory /path/to/html/files
  
  # Skip processing, go straight to interactive chat
  python full_pipeline.py --interactive-only
  
  # Force reprocess files even if already processed
  python full_pipeline.py document.html --force-reprocess
  
  # Use custom configuration
  python full_pipeline.py document.html --config my_config.json
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=False)
    input_group.add_argument(
        'html_file',
        nargs='?',
        help='HTML file to process'
    )
    input_group.add_argument(
        '--directory', '-d',
        help='Directory containing HTML files to process'
    )
    input_group.add_argument(
        '--interactive-only', '-i',
        action='store_true',
        help='Skip processing phase, go directly to interactive chat'
    )
    
    # Configuration options
    config_group = parser.add_argument_group('Configuration')
    config_group.add_argument(
        '--config', '-c',
        help='Path to JSON configuration file'
    )
    config_group.add_argument(
        '--preset', '-p',
        choices=['default', 'minecraft-wiki'],
        default='default',
        help='Use a predefined configuration preset'
    )
    config_group.add_argument(
        '--api-key',
        help='BHub API key for LLM processing'
    )
    config_group.add_argument(
        '--model-id',
        default='mistral-small',
        help='LLM model ID to use'
    )
    config_group.add_argument(
        '--context-hint',
        help='Context hint for better table descriptions'
    )
    config_group.add_argument(
        '--db-path',
        default='table_querying.db',
        help='Path to SQLite database file'
    )
    
    # Processing options
    proc_group = parser.add_argument_group('Processing Options')
    proc_group.add_argument(
        '--force-reprocess', '-f',
        action='store_true',
        help='Force reprocessing even if files have already been processed'
    )
    proc_group.add_argument(
        '--clear-database',
        action='store_true',
        help='Clear database before processing'
    )
    proc_group.add_argument(
        '--no-chat',
        action='store_true',
        help='Skip interactive chat after processing'
    )
    proc_group.add_argument(
        '--recursive', '-r',
        action='store_true',
        help='Search for HTML files recursively in subdirectories'
    )
    
    # Other options
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--version',
        action='version',
        version='Full Pipeline 1.0.0'
    )
    
    args = parser.parse_args()
    
    # Check if we need input for processing
    if not args.interactive_only and not args.html_file and not args.directory:
        parser.error("Must provide either html_file, --directory, or --interactive-only")
    
    try:
        # Load configuration
        config = None
        if args.config:
            config = TableProcessingConfig.from_file(args.config)
        elif args.preset == 'minecraft-wiki':
            config = create_config_for_minecraft_wiki()
        else:
            config = create_default_config()
        
        # Override with command line arguments
        config_dict = config.to_dict()
        if args.api_key:
            config_dict['api_key'] = args.api_key
        if args.model_id:
            config_dict['model_id'] = args.model_id
        if args.context_hint:
            config_dict['context_hint'] = args.context_hint
        if args.db_path:
            config_dict['db_path'] = args.db_path
        if args.clear_database:
            config_dict['clear_database_on_start'] = True
        
        # Initialize pipeline
        pipeline = FullPipeline(config_dict, args.verbose)
        
        # Processing phase (unless skipped)
        if not args.interactive_only:
            print("🚀 Starting Full Pipeline...")
            
            if args.html_file:
                # Single file processing
                result = pipeline.process_single_file(args.html_file, args.force_reprocess)
                if not result.get('success', False) and not result.get('skipped', False):
                    print(f"❌ Processing failed, but continuing to chat phase...")
            
            elif args.directory:
                # Directory processing
                html_files = discover_html_files(args.directory, args.recursive)
                
                if not html_files:
                    print(f"❌ No HTML files found in directory: {args.directory}")
                    return 1
                
                results = pipeline.process_multiple_files(html_files, args.force_reprocess)
        
        else:
            print("⏭️  Skipping processing phase...")
        
        # Interactive chat phase (unless disabled)
        if not args.no_chat:
            pipeline.start_interactive_chat()
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())