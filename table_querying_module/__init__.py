"""
Table Querying Module for CraftGraphRag.

A self-contained application for extracting, processing, and querying tables from documents.
This module extracts tables from HTML documents, creates flattened schemas, generates LLM 
summaries, stores them in a database, and replaces table content with descriptions.

Main Components:
- TableExtractor: Extracts tables from HTML documents
- SchemaProcessor: Creates flattened schemas from HTML tables
- TableSummarizer: Generates LLM descriptions of tables
- TableDatabase: Manages table storage and querying
- DocumentProcessor: Handles document processing with table replacement
"""

try:
    from .table_extractor import TableExtractor
    from .schema_processor import SchemaProcessor  
    from .table_summarizer import TableSummarizer
    from .table_database import TableDatabase
    from .document_processor import DocumentProcessor
    from .table_processor import TableProcessor
except ImportError:
    from table_extractor import TableExtractor
    from schema_processor import SchemaProcessor  
    from table_summarizer import TableSummarizer
    from table_database import TableDatabase
    from document_processor import DocumentProcessor
    from table_processor import TableProcessor

__all__ = [
    'TableExtractor',
    'SchemaProcessor', 
    'TableSummarizer',
    'TableDatabase',
    'DocumentProcessor',
    'TableProcessor'
]

__version__ = "1.0.0"