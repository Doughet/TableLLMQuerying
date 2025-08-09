"""
Abstract Base Table Extractor.

This module defines the interface that all table extractors must implement,
providing a consistent API for extracting tables from different document formats.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Standard result format for table extraction operations."""
    source_file: str
    tables_found: int
    extraction_successful: bool
    error_message: Optional[str] = None
    extracted_data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.extracted_data is None:
            self.extracted_data = {}


class BaseTableExtractor(ABC):
    """Abstract base class for all table extractors."""
    
    def __init__(self):
        """Initialize the base extractor."""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def extract_from_file(self, file_path: str) -> ExtractionResult:
        """
        Extract tables and content from a file.
        
        Args:
            file_path: Path to the file to extract from
            
        Returns:
            ExtractionResult containing extracted data and metadata
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is not supported by this extractor
        """
        pass
    
    @abstractmethod
    def supports_file_type(self, file_path: str) -> bool:
        """
        Check if this extractor supports the given file type.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if this extractor can handle the file type, False otherwise
        """
        pass
    
    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """
        Get list of file extensions supported by this extractor.
        
        Returns:
            List of file extensions (including the dot, e.g., ['.html', '.htm'])
        """
        pass
    
    def validate_file(self, file_path: str) -> None:
        """
        Validate that the file exists and is supported.
        
        Args:
            file_path: Path to the file to validate
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is not supported
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not self.supports_file_type(file_path):
            supported_exts = ', '.join(self.get_supported_extensions())
            raise ValueError(
                f"Unsupported file format: {path.suffix}. "
                f"This extractor supports: {supported_exts}"
            )
    
    def get_extractor_name(self) -> str:
        """
        Get a human-readable name for this extractor.
        
        Returns:
            Name of the extractor
        """
        return self.__class__.__name__