"""
Main entry point for the new interface-based table processing system.

This demonstrates how to use the new architecture with interfaces, 
component registry, and dependency injection.
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import argparse
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Add parent directories to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from .table_processor_v2 import TableProcessorV2
from ..core.exceptions import TableQueryingError, ComponentNotFoundError


def create_config_from_args(args) -> Dict[str, Any]:
    """Create configuration dictionary from command line arguments."""
    config = {}
    
    # Core configuration
    if args.api_key:
        config['api_key'] = args.api_key
    
    if args.model_id:
        config['model_id'] = args.model_id
    
    if args.db_path:
        config['db_path'] = args.db_path
    
    # Processing options
    config['save_outputs'] = not args.no_save
    config['clear_database_on_start'] = args.clear_db
    config['context_hint'] = args.context_hint or ""
    
    # Output configuration
    if args.output_dir:
        config['output_dir'] = args.output_dir
    
    # Service configuration
    config['llm_service_type'] = args.llm_service or 'bhub'
    config['environment'] = args.environment or 'development'
    config['debug'] = args.debug
    
    return config


def load_config_file(config_path: Path) -> Dict[str, Any]:
    """Load configuration from JSON file."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config file {config_path}: {e}")
        return {}


def process_single_file(processor: TableProcessorV2, html_file: str, verbose: bool = False) -> Dict[str, Any]:
    """Process a single HTML file."""
    logger.info(f"Processing file: {html_file}")
    
    try:
        # Process the document
        results = processor.process_document(html_file)
        
        if verbose or results.get('success', False):
            processor.print_processing_summary(results)
        
        if not results.get('success', False):
            logger.error(f"Processing failed: {results.get('error', 'Unknown error')}")
        
        return results
        
    except Exception as e:
        logger.error(f"Processing failed with exception: {e}")
        return {
            'success': False,
            'error': str(e),
            'html_file': html_file
        }


def process_directory(processor: TableProcessorV2, directory: str, recursive: bool = False, pattern: str = "*.html") -> Dict[str, Any]:
    """Process all HTML files in a directory."""
    dir_path = Path(directory)
    
    if not dir_path.exists():
        logger.error(f"Directory not found: {directory}")
        return {'success': False, 'error': f'Directory not found: {directory}'}
    
    # Find HTML files
    if recursive:
        html_files = list(dir_path.rglob(pattern))
    else:
        html_files = list(dir_path.glob(pattern))
    
    if not html_files:
        logger.warning(f"No HTML files found in {directory}")
        return {'success': True, 'processed_files': 0, 'results': []}
    
    logger.info(f"Found {len(html_files)} HTML files to process")
    
    # Process each file
    all_results = []
    successful_count = 0
    
    for html_file in html_files:
        try:
            results = process_single_file(processor, str(html_file))
            all_results.append(results)
            
            if results.get('success', False):
                successful_count += 1
                
        except Exception as e:
            logger.error(f"Failed to process {html_file}: {e}")
            all_results.append({
                'success': False,
                'error': str(e),
                'html_file': str(html_file)
            })
    
    # Summary
    summary = {
        'success': True,
        'total_files': len(html_files),
        'successful_files': successful_count,
        'failed_files': len(html_files) - successful_count,
        'results': all_results
    }
    
    logger.info(f"Batch processing completed: {successful_count}/{len(html_files)} files processed successfully")
    return summary


def show_architecture_info(processor: TableProcessorV2):
    """Display information about the component architecture."""
    print("\n" + "="*80)
    print("COMPONENT ARCHITECTURE INFORMATION")
    print("="*80)
    
    try:
        component_info = processor.get_component_info()
        
        print(f"Architecture Version: {component_info.get('architecture_version', 'Unknown')}")
        print(f"\nRegistered Components:")
        
        components = component_info.get('registered_components', {})
        for interface_name, component_list in components.items():
            print(f"\n  {interface_name}:")
            for component in component_list:
                print(f"    - Type: {component.get('type')}")
                print(f"      Implementation: {component.get('class')}")
                print(f"      Singleton: {component.get('singleton')}")
        
        print(f"\nDependency Graph:")
        deps = component_info.get('dependency_graph', {})
        for component, dependencies in deps.items():
            if dependencies:
                print(f"  {component} → {', '.join(dependencies)}")
        
        validation = component_info.get('dependency_validation', {})
        print(f"\nDependency Validation: {'✅ Valid' if validation.get('valid') else '❌ Invalid'}")
        
        if validation.get('errors'):
            print("  Errors:")
            for error in validation['errors']:
                print(f"    - {error}")
        
        if validation.get('warnings'):
            print("  Warnings:")
            for warning in validation['warnings']:
                print(f"    - {warning}")
        
    except Exception as e:
        print(f"Error getting component information: {e}")
    
    print("="*80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Table Processing System - Interface Architecture (V2)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single file
  python main_v2.py document.html --api-key YOUR_API_KEY
  
  # Process directory
  python main_v2.py --directory /path/to/html/files --recursive
  
  # Use configuration file
  python main_v2.py document.html --config config.json
  
  # Show architecture information
  python main_v2.py --show-architecture
        """
    )
    
    # Input options
    parser.add_argument('html_file', nargs='?', help='HTML file to process')
    parser.add_argument('--directory', '-d', help='Directory containing HTML files to process')
    parser.add_argument('--recursive', '-r', action='store_true', help='Process directory recursively')
    parser.add_argument('--pattern', default='*.html', help='File pattern to match (default: *.html)')
    
    # Configuration options
    parser.add_argument('--config', '-c', help='JSON configuration file')
    parser.add_argument('--api-key', help='LLM API key')
    parser.add_argument('--model-id', default='mistral-small', help='LLM model ID')
    parser.add_argument('--db-path', default='table_querying_v2.db', help='Database file path')
    parser.add_argument('--llm-service', choices=['bhub', 'openai'], default='bhub', help='LLM service type')
    
    # Processing options
    parser.add_argument('--context-hint', help='Context hint for better table descriptions')
    parser.add_argument('--clear-db', action='store_true', help='Clear database before processing')
    parser.add_argument('--no-save', action='store_true', help='Don\'t save output files')
    parser.add_argument('--output-dir', help='Output directory for generated files')
    
    # System options
    parser.add_argument('--environment', choices=['development', 'production'], default='development', help='Environment mode')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    # Architecture options
    parser.add_argument('--show-architecture', action='store_true', help='Show component architecture information')
    
    args = parser.parse_args()
    
    # Load configuration
    config = {}
    if args.config:
        config_path = Path(args.config)
        if config_path.exists():
            config = load_config_file(config_path)
        else:
            logger.error(f"Config file not found: {args.config}")
            sys.exit(1)
    
    # Override with command line arguments
    config.update(create_config_from_args(args))
    
    # Set logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.verbose:
        logging.getLogger().setLevel(logging.INFO)
    
    try:
        # Initialize processor
        logger.info("Initializing TableProcessorV2 with interface architecture")
        processor = TableProcessorV2(config)
        
        # Show architecture information if requested
        if args.show_architecture:
            show_architecture_info(processor)
            return
        
        # Validate inputs
        if not args.html_file and not args.directory:
            logger.error("Either html_file or --directory must be specified")
            parser.print_help()
            sys.exit(1)
        
        # Process files
        if args.directory:
            results = process_directory(processor, args.directory, args.recursive, args.pattern)
        else:
            results = process_single_file(processor, args.html_file, args.verbose)
        
        # Print final summary
        if args.verbose:
            print(f"\n{'='*60}")
            print("FINAL PROCESSING SUMMARY")
            print(f"{'='*60}")
            
            if 'total_files' in results:
                # Batch processing
                print(f"Total Files: {results['total_files']}")
                print(f"Successful: {results['successful_files']}")
                print(f"Failed: {results['failed_files']}")
            else:
                # Single file processing
                print(f"File: {results.get('html_file', 'Unknown')}")
                print(f"Success: {results.get('success', False)}")
                
            print(f"Architecture: Interface-based (V2)")
            
            # Show database summary
            try:
                db_summary = processor.get_database_summary()
                if db_summary and not db_summary.get('error'):
                    print(f"\nDatabase Summary:")
                    for key, value in db_summary.items():
                        if key != 'error':
                            print(f"  {key}: {value}")
            except Exception as e:
                logger.warning(f"Could not get database summary: {e}")
        
        # Exit with appropriate code
        if isinstance(results, dict):
            sys.exit(0 if results.get('success', False) else 1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        sys.exit(130)
        
    except TableQueryingError as e:
        logger.error(f"Table processing error: {e}")
        sys.exit(1)
        
    except ComponentNotFoundError as e:
        logger.error(f"Component system error: {e}")
        logger.error("This likely means the interface architecture is not properly configured")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()