#!/usr/bin/env python3
"""
Main CLI interface for the Table Querying Module.

This script provides a command-line interface for processing HTML documents
with tables using the complete table processing workflow.
"""

import argparse
import sys
import logging
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
    from .config import TableProcessingConfig, create_default_config, create_config_for_minecraft_wiki, create_config_template
    from .table_processor import TableProcessor
except ImportError:
    # If running directly, adjust imports
    from config import TableProcessingConfig, create_default_config, create_config_for_minecraft_wiki, create_config_template
    from table_processor import TableProcessor


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def process_single_document(html_file: str, config: TableProcessingConfig, verbose: bool = False):
    """Process a single HTML document."""
    if verbose:
        print(f"Processing document: {html_file}")
        print(f"Configuration: {config.to_dict()}")
    
    # Initialize processor
    processor = TableProcessor(config.to_dict())
    
    # Process document
    results = processor.process_document(html_file)
    
    # Print results
    processor.print_processing_summary(results)
    
    return results


def process_multiple_documents(html_files: list, config: TableProcessingConfig, verbose: bool = False):
    """Process multiple HTML documents."""
    print(f"Processing {len(html_files)} documents...")
    
    # Initialize processor (reuse for efficiency)
    processor = TableProcessor(config.to_dict())
    
    all_results = []
    successful = 0
    failed = 0
    
    for i, html_file in enumerate(html_files, 1):
        print(f"\n{'='*20} Processing {i}/{len(html_files)} {'='*20}")
        print(f"File: {Path(html_file).name}")
        
        try:
            results = processor.process_document(html_file)
            all_results.append(results)
            
            if results.get('success', False):
                successful += 1
                print(f"✅ Successfully processed {Path(html_file).name}")
            else:
                failed += 1
                print(f"❌ Failed to process {Path(html_file).name}: {results.get('error', 'Unknown error')}")
        
        except Exception as e:
            failed += 1
            print(f"❌ Error processing {Path(html_file).name}: {e}")
            all_results.append({
                'success': False,
                'error': str(e),
                'html_file': html_file
            })
    
    # Print overall summary
    print(f"\n{'='*60}")
    print("BATCH PROCESSING SUMMARY")
    print(f"{'='*60}")
    print(f"Total Documents: {len(html_files)}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {successful/len(html_files)*100:.1f}%")
    
    # Database summary
    db_summary = processor.get_database_summary()
    print(f"\n📊 Database Summary:")
    print(f"  • Total Tables: {db_summary.get('total_tables', 0)}")
    print(f"  • Unique Sources: {db_summary.get('unique_sources', 0)}")
    print(f"{'='*60}")
    
    return all_results


def discover_html_files(directory: str, recursive: bool = False) -> list:
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
        description="Table Querying Module - Extract, process, and query tables from HTML documents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a single HTML file
  python -m table_querying_module.main document.html
  
  # Process with custom configuration
  python -m table_querying_module.main document.html --config my_config.json
  
  # Process all HTML files in a directory
  python -m table_querying_module.main --directory /path/to/html/files
  
  # Process with Minecraft Wiki optimized settings
  python -m table_querying_module.main document.html --preset minecraft-wiki
  
  # Clear database before processing
  python -m table_querying_module.main document.html --clear-database
  
  # Create configuration template
  python -m table_querying_module.main --create-config-template
        """
    )
    
    # Input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
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
        '--create-config-template',
        action='store_true',
        help='Create a configuration template file'
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
        help='OpenAI API key for LLM processing'
    )
    config_group.add_argument(
        '--model-id',
        default='gpt-3.5-turbo',
        help='LLM model ID to use (default: gpt-3.5-turbo)'
    )
    config_group.add_argument(
        '--context-hint',
        help='Context hint for better table descriptions'
    )
    config_group.add_argument(
        '--output-dir',
        help='Directory for output files'
    )
    config_group.add_argument(
        '--db-path',
        help='Path to SQLite database file'
    )
    
    # Processing options
    proc_group = parser.add_argument_group('Processing Options')
    proc_group.add_argument(
        '--clear-database',
        action='store_true',
        help='Clear database before processing'
    )
    proc_group.add_argument(
        '--no-save',
        action='store_true',
        help='Do not save output files'
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
        version='Table Querying Module 1.0.0'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Handle config template creation
    if args.create_config_template:
        create_config_template("table_processing_config.json")
        return 0
    
    try:
        # Load configuration
        if args.config:
            config = TableProcessingConfig.from_file(args.config)
        elif args.preset == 'minecraft-wiki':
            config = create_config_for_minecraft_wiki()
        else:
            config = create_default_config()
        
        # Override with command line arguments
        if args.api_key:
            config.api_key = args.api_key
        if args.model_id:
            config.model_id = args.model_id
        if args.context_hint:
            config.context_hint = args.context_hint
        if args.output_dir:
            config.output_dir = args.output_dir
        if args.db_path:
            config.db_path = args.db_path
        if args.clear_database:
            config.clear_database_on_start = True
        if args.no_save:
            config.save_outputs = False
        
        # Process files
        if args.html_file:
            # Single file processing
            if not Path(args.html_file).exists():
                print(f"Error: File not found: {args.html_file}")
                return 1
            
            results = process_single_document(args.html_file, config, args.verbose)
            return 0 if results.get('success', False) else 1
        
        elif args.directory:
            # Directory processing
            try:
                html_files = discover_html_files(args.directory, args.recursive)
                
                if not html_files:
                    print(f"No HTML files found in directory: {args.directory}")
                    return 1
                
                print(f"Found {len(html_files)} HTML files")
                if args.verbose:
                    for f in html_files:
                        print(f"  - {f}")
                
                all_results = process_multiple_documents(html_files, config, args.verbose)
                
                # Return success if at least one file was processed successfully
                successful = sum(1 for r in all_results if r.get('success', False))
                return 0 if successful > 0 else 1
                
            except Exception as e:
                print(f"Error processing directory: {e}")
                return 1
    
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())