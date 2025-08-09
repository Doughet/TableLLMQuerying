"""
Extractor Router.

This module provides routing functionality to automatically select the appropriate
table extractor based on file type. It acts as a central dispatcher for all
table extraction operations.
"""

from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

from .base_extractor import BaseTableExtractor, ExtractionResult
from .html_extractor import HTMLTableExtractor
from .excel_extractor import ExcelTableExtractor

logger = logging.getLogger(__name__)


class ExtractorRouter:
    """Routes files to appropriate extractors based on file type."""
    
    def __init__(self):
        """Initialize the router with all available extractors."""
        self.extractors: List[BaseTableExtractor] = [
            HTMLTableExtractor(),
            ExcelTableExtractor(),
        ]
        
        # Build extension to extractor mapping for fast lookup
        self._extension_mapping = self._build_extension_mapping()
        
        logger.info(f"ExtractorRouter initialized with {len(self.extractors)} extractors")
        logger.debug(f"Supported extensions: {list(self._extension_mapping.keys())}")
    
    def get_extractor(self, file_path: str) -> BaseTableExtractor:
        """
        Get the appropriate extractor for a given file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            BaseTableExtractor instance capable of handling the file
            
        Raises:
            ValueError: If no extractor is found for the file type
        """
        file_extension = Path(file_path).suffix.lower()
        
        # Try fast lookup first
        if file_extension in self._extension_mapping:
            extractor = self._extension_mapping[file_extension]
            logger.debug(f"Found extractor {extractor.get_extractor_name()} for {file_extension}")
            return extractor
        
        # Fallback to checking each extractor (in case mapping is incomplete)
        for extractor in self.extractors:
            if extractor.supports_file_type(file_path):
                logger.debug(f"Found extractor {extractor.get_extractor_name()} via fallback check")
                return extractor
        
        # No extractor found
        supported_extensions = self.get_supported_extensions()
        raise ValueError(
            f"No extractor found for file: {file_path} (extension: {file_extension}). "
            f"Supported extensions: {', '.join(supported_extensions)}"
        )
    
    def extract_from_file(self, file_path: str) -> ExtractionResult:
        """
        Extract tables from a file using the appropriate extractor.
        
        This is a convenience method that combines routing and extraction.
        
        Args:
            file_path: Path to the file to extract from
            
        Returns:
            ExtractionResult from the appropriate extractor
        """
        try:
            extractor = self.get_extractor(file_path)
            logger.info(f"Routing {file_path} to {extractor.get_extractor_name()}")
            return extractor.extract_from_file(file_path)
        
        except Exception as e:
            logger.error(f"Failed to extract from {file_path}: {e}")
            return ExtractionResult(
                source_file=file_path,
                tables_found=0,
                extraction_successful=False,
                error_message=str(e)
            )
    
    def get_supported_extensions(self) -> List[str]:
        """
        Get all supported file extensions from all extractors.
        
        Returns:
            Sorted list of all supported file extensions
        """
        extensions = set()
        for extractor in self.extractors:
            extensions.update(extractor.get_supported_extensions())
        
        return sorted(list(extensions))
    
    def is_supported_file(self, file_path: str) -> bool:
        """
        Check if a file is supported by any extractor.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if the file type is supported, False otherwise
        """
        try:
            self.get_extractor(file_path)
            return True
        except ValueError:
            return False
    
    def get_extractor_info(self) -> Dict[str, Any]:
        """
        Get information about all registered extractors.
        
        Returns:
            Dictionary with extractor information
        """
        info = {
            'total_extractors': len(self.extractors),
            'supported_extensions': self.get_supported_extensions(),
            'extractors': []
        }
        
        for extractor in self.extractors:
            extractor_info = {
                'name': extractor.get_extractor_name(),
                'supported_extensions': extractor.get_supported_extensions()
            }
            info['extractors'].append(extractor_info)
        
        return info
    
    def add_extractor(self, extractor: BaseTableExtractor) -> None:
        """
        Add a new extractor to the router.
        
        This allows for dynamic registration of new extractors.
        
        Args:
            extractor: New extractor to add
        """
        self.extractors.append(extractor)
        self._extension_mapping = self._build_extension_mapping()
        
        logger.info(f"Added extractor: {extractor.get_extractor_name()}")
        logger.debug(f"New supported extensions: {list(self._extension_mapping.keys())}")
    
    def remove_extractor(self, extractor_name: str) -> bool:
        """
        Remove an extractor by name.
        
        Args:
            extractor_name: Name of the extractor to remove
            
        Returns:
            True if extractor was found and removed, False otherwise
        """
        initial_count = len(self.extractors)
        self.extractors = [
            ext for ext in self.extractors 
            if ext.get_extractor_name() != extractor_name
        ]
        
        removed = len(self.extractors) < initial_count
        
        if removed:
            self._extension_mapping = self._build_extension_mapping()
            logger.info(f"Removed extractor: {extractor_name}")
        else:
            logger.warning(f"Extractor not found: {extractor_name}")
        
        return removed
    
    def _build_extension_mapping(self) -> Dict[str, BaseTableExtractor]:
        """
        Build a mapping from file extensions to extractors for fast lookup.
        
        Returns:
            Dictionary mapping extensions to extractors
        """
        mapping = {}
        
        for extractor in self.extractors:
            for extension in extractor.get_supported_extensions():
                if extension in mapping:
                    logger.warning(
                        f"Extension {extension} is supported by multiple extractors. "
                        f"Using {extractor.get_extractor_name()}"
                    )
                mapping[extension] = extractor
        
        return mapping