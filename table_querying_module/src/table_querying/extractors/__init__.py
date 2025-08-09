"""
Table Extractor Package.

This package provides a pluggable architecture for extracting tables from different
document formats. Each document type has its own specialized extractor that implements
the BaseTableExtractor interface.
"""

from .base_extractor import BaseTableExtractor, ExtractionResult
from .html_extractor import HTMLTableExtractor
from .excel_extractor import ExcelTableExtractor
from .extractor_router import ExtractorRouter
from .extractor_factory import ExtractorFactory

__all__ = [
    'BaseTableExtractor', 'ExtractionResult',
    'HTMLTableExtractor', 'ExcelTableExtractor',
    'ExtractorRouter', 'ExtractorFactory'
]