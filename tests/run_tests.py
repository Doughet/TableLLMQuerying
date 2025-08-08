#!/usr/bin/env python3
"""
Test runner for the TableLLM Querying system.

Runs all tests with proper configuration and reporting.
"""

import sys
import unittest
import logging
from pathlib import Path
import argparse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'table_querying_module' / 'src'))

def setup_test_logging():
    """Setup logging for tests."""
    logging.basicConfig(
        level=logging.WARNING,  # Reduce noise during tests
        format='%(levelname)s: %(name)s: %(message)s'
    )

def discover_and_run_tests(test_pattern='test_*.py', verbosity=2):
    """Discover and run all tests."""
    # Setup logging
    setup_test_logging()
    
    # Discover tests
    test_dir = Path(__file__).parent
    loader = unittest.TestLoader()
    suite = loader.discover(str(test_dir), pattern=test_pattern)
    
    # Run tests
    runner = unittest.TextTestRunner(
        verbosity=verbosity,
        buffer=True,  # Capture stdout/stderr
        failfast=False
    )
    
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped) if hasattr(result, 'skipped') else 0
    
    print(f"Tests run: {total_tests}")
    print(f"Failures: {failures}")
    print(f"Errors: {errors}")
    print(f"Skipped: {skipped}")
    
    if failures > 0:
        print(f"\nFAILURES ({failures}):")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if errors > 0:
        print(f"\nERRORS ({errors}):")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    success_rate = ((total_tests - failures - errors) / total_tests * 100) if total_tests > 0 else 0
    print(f"\nSuccess rate: {success_rate:.1f}%")
    
    if failures == 0 and errors == 0:
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

def run_specific_test_module(module_name, verbosity=2):
    """Run tests from a specific module."""
    setup_test_logging()
    
    try:
        # Import the test module
        test_module = __import__(module_name)
        
        # Create test suite
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(test_module)
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=verbosity, buffer=True)
        result = runner.run(suite)
        
        return 0 if result.wasSuccessful() else 1
        
    except ImportError as e:
        print(f"Could not import test module '{module_name}': {e}")
        return 1

def run_test_categories():
    """Run tests by category."""
    categories = {
        'core': 'test_core_interfaces.py',
        'implementations': 'test_interface_implementations.py',
        'processor': 'test_table_processor_v2.py',
        'integration': 'test_integration.py'
    }
    
    print("Available test categories:")
    for category, filename in categories.items():
        print(f"  {category}: {filename}")
    
    return categories

def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description='Run TableLLM Querying tests')
    parser.add_argument(
        '--module', '-m',
        help='Run specific test module (e.g., test_core_interfaces)'
    )
    parser.add_argument(
        '--category', '-c',
        choices=['core', 'implementations', 'processor', 'integration'],
        help='Run tests from specific category'
    )
    parser.add_argument(
        '--pattern', '-p',
        default='test_*.py',
        help='Pattern for test discovery (default: test_*.py)'
    )
    parser.add_argument(
        '--verbosity', '-v',
        type=int,
        default=2,
        choices=[0, 1, 2],
        help='Test output verbosity (0=quiet, 1=normal, 2=verbose)'
    )
    parser.add_argument(
        '--list-categories',
        action='store_true',
        help='List available test categories'
    )
    
    args = parser.parse_args()
    
    if args.list_categories:
        run_test_categories()
        return 0
    
    if args.category:
        categories = run_test_categories()
        pattern = categories[args.category]
        return discover_and_run_tests(pattern, args.verbosity)
    
    if args.module:
        return run_specific_test_module(args.module, args.verbosity)
    
    # Run all tests
    return discover_and_run_tests(args.pattern, args.verbosity)

if __name__ == '__main__':
    sys.exit(main())