"""
Chatting Module

A module that analyzes user queries and generates SQL queries to interact with
the processed table database. It uses LLM to determine if a query is fulfillable
and generates appropriate SQL statements.
"""

__version__ = "1.0.0"
__author__ = "CraftGraphRag Project"

from .query_analyzer import QueryAnalyzer
from .sql_generator import SQLGenerator
from .chat_interface import ChatInterface
from .result_exporter import ResultExporter

__all__ = [
    'QueryAnalyzer',
    'SQLGenerator', 
    'ChatInterface',
    'ResultExporter'
]