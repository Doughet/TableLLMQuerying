"""
Table Querying Module

A self-contained application for extracting, processing, and querying tables from HTML documents.
This module extracts tables from documents, creates flattened schemas, generates LLM summaries,
stores them in a database, and replaces table content with descriptions.
"""

__version__ = "1.0.0"
__author__ = "CraftGraphRag Project"

# Import main classes for easy access
from .extractors import ExtractorFactory, ExtractorRouter
from .schema_processor import SchemaProcessor  
from .table_summarizer import TableSummarizer
from .table_database import TableDatabase
from .document_processor import DocumentProcessor
from .table_processor import TableProcessor
from .config import TableProcessingConfig, create_default_config, create_config_for_minecraft_wiki

# Define what gets imported with "from table_querying import *"
__all__ = [
    'ExtractorFactory',
    'ExtractorRouter',
    'SchemaProcessor', 
    'TableSummarizer',
    'TableDatabase',
    'DocumentProcessor',
    'TableProcessor',
    'TableProcessingConfig',
    'create_default_config',
    'create_config_for_minecraft_wiki'
]