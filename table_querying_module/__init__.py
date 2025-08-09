"""
Table Querying Module for CraftGraphRag.

A self-contained application for extracting, processing, and querying tables from documents.
This module extracts tables from HTML and Excel documents, creates flattened schemas, generates LLM 
summaries, stores them in a database, and replaces table content with descriptions.

Main Components:
- ExtractorFactory: Factory for creating table extractors (HTML, Excel)
- ExtractorRouter: Routes files to appropriate extractors
- SchemaProcessor: Creates flattened schemas from tables
- TableSummarizer: Generates LLM descriptions of tables
- TableDatabase: Manages table storage and querying
- DocumentProcessor: Handles document processing with table replacement
- TableProcessor: Main orchestrator for the complete workflow
"""

try:
    from .src.table_querying.extractors import ExtractorFactory, ExtractorRouter
    from .src.table_querying.schema_processor import SchemaProcessor  
    from .src.table_querying.table_summarizer import TableSummarizer
    from .src.table_querying.table_database import TableDatabase
    from .src.table_querying.document_processor import DocumentProcessor
    from .src.table_querying.table_processor import TableProcessor
except ImportError:
    from src.table_querying.extractors import ExtractorFactory, ExtractorRouter
    from src.table_querying.schema_processor import SchemaProcessor  
    from src.table_querying.table_summarizer import TableSummarizer
    from src.table_querying.table_database import TableDatabase
    from src.table_querying.document_processor import DocumentProcessor
    from src.table_querying.table_processor import TableProcessor

__all__ = [
    'ExtractorFactory',
    'ExtractorRouter',
    'SchemaProcessor', 
    'TableSummarizer',
    'TableDatabase',
    'DocumentProcessor',
    'TableProcessor'
]

__version__ = "1.0.0"