"""
Extractor Factory.

This module provides factory methods for creating and configuring table extractors.
It serves as the main entry point for getting extractors and routers.
"""

from typing import Optional, Dict, Any, List
import logging

from .base_extractor import BaseTableExtractor
from .html_extractor import HTMLTableExtractor
from .excel_extractor import ExcelTableExtractor
from .extractor_router import ExtractorRouter

logger = logging.getLogger(__name__)


class ExtractorFactory:
    """Factory for creating and configuring table extractors."""
    
    # Registry of available extractor classes
    _EXTRACTOR_REGISTRY = {
        'html': HTMLTableExtractor,
        'excel': ExcelTableExtractor,
    }
    
    @staticmethod
    def create_router(extractors: Optional[List[str]] = None) -> ExtractorRouter:
        """
        Create a configured router with specified extractors.
        
        Args:
            extractors: List of extractor names to include. If None, includes all available extractors.
            
        Returns:
            Configured ExtractorRouter instance
            
        Raises:
            ValueError: If an unknown extractor name is specified
        """
        router = ExtractorRouter.__new__(ExtractorRouter)  # Create without calling __init__
        router.extractors = []
        
        # Determine which extractors to include
        if extractors is None:
            # Include all available extractors
            extractor_names = list(ExtractorFactory._EXTRACTOR_REGISTRY.keys())
        else:
            extractor_names = extractors
        
        # Create and add extractors
        for name in extractor_names:
            if name not in ExtractorFactory._EXTRACTOR_REGISTRY:
                available = ', '.join(ExtractorFactory._EXTRACTOR_REGISTRY.keys())
                raise ValueError(f"Unknown extractor: {name}. Available: {available}")
            
            extractor_class = ExtractorFactory._EXTRACTOR_REGISTRY[name]
            extractor = extractor_class()
            router.extractors.append(extractor)
        
        # Build the extension mapping
        router._extension_mapping = router._build_extension_mapping()
        
        logger.info(f"Created router with {len(router.extractors)} extractors: {extractor_names}")
        return router
    
    @staticmethod
    def create_extractor(extractor_type: str) -> BaseTableExtractor:
        """
        Create a specific extractor by type.
        
        Args:
            extractor_type: Type of extractor to create ('html', 'excel', etc.)
            
        Returns:
            BaseTableExtractor instance
            
        Raises:
            ValueError: If the extractor type is not recognized
        """
        if extractor_type not in ExtractorFactory._EXTRACTOR_REGISTRY:
            available = ', '.join(ExtractorFactory._EXTRACTOR_REGISTRY.keys())
            raise ValueError(f"Unknown extractor type: {extractor_type}. Available: {available}")
        
        extractor_class = ExtractorFactory._EXTRACTOR_REGISTRY[extractor_type]
        return extractor_class()
    
    @staticmethod
    def get_extractor_for_file(file_path: str, router: Optional[ExtractorRouter] = None) -> BaseTableExtractor:
        """
        Get the appropriate extractor for a specific file.
        
        This is a convenience method that creates a router if needed.
        
        Args:
            file_path: Path to the file
            router: Optional router to use. If None, creates a default router.
            
        Returns:
            BaseTableExtractor instance for the file
            
        Raises:
            ValueError: If no extractor is found for the file type
        """
        if router is None:
            router = ExtractorFactory.create_router()
        
        return router.get_extractor(file_path)
    
    @staticmethod
    def get_available_extractors() -> Dict[str, Any]:
        """
        Get information about all available extractors.
        
        Returns:
            Dictionary with information about available extractors
        """
        info = {
            'total_available': len(ExtractorFactory._EXTRACTOR_REGISTRY),
            'extractors': {}
        }
        
        for name, extractor_class in ExtractorFactory._EXTRACTOR_REGISTRY.items():
            # Create temporary instance to get metadata
            temp_extractor = extractor_class()
            info['extractors'][name] = {
                'class_name': extractor_class.__name__,
                'supported_extensions': temp_extractor.get_supported_extensions()
            }
        
        return info
    
    @staticmethod
    def register_extractor(name: str, extractor_class) -> None:
        """
        Register a new extractor type.
        
        This allows for dynamic registration of custom extractors.
        
        Args:
            name: Name for the extractor type
            extractor_class: Class that implements BaseTableExtractor
            
        Raises:
            ValueError: If the extractor class doesn't inherit from BaseTableExtractor
        """
        if not issubclass(extractor_class, BaseTableExtractor):
            raise ValueError(f"Extractor class must inherit from BaseTableExtractor")
        
        if name in ExtractorFactory._EXTRACTOR_REGISTRY:
            logger.warning(f"Overriding existing extractor registration: {name}")
        
        ExtractorFactory._EXTRACTOR_REGISTRY[name] = extractor_class
        logger.info(f"Registered extractor: {name} -> {extractor_class.__name__}")
    
    @staticmethod
    def unregister_extractor(name: str) -> bool:
        """
        Unregister an extractor type.
        
        Args:
            name: Name of the extractor type to remove
            
        Returns:
            True if extractor was found and removed, False otherwise
        """
        if name in ExtractorFactory._EXTRACTOR_REGISTRY:
            del ExtractorFactory._EXTRACTOR_REGISTRY[name]
            logger.info(f"Unregistered extractor: {name}")
            return True
        else:
            logger.warning(f"Extractor not found for unregistration: {name}")
            return False
    
    @staticmethod
    def create_custom_router(custom_extractors: List[BaseTableExtractor]) -> ExtractorRouter:
        """
        Create a router with custom extractor instances.
        
        This allows for advanced customization where you need pre-configured
        extractor instances.
        
        Args:
            custom_extractors: List of pre-configured extractor instances
            
        Returns:
            ExtractorRouter with the custom extractors
        """
        router = ExtractorRouter.__new__(ExtractorRouter)  # Create without calling __init__
        router.extractors = custom_extractors.copy()
        router._extension_mapping = router._build_extension_mapping()
        
        extractor_names = [ext.get_extractor_name() for ext in custom_extractors]
        logger.info(f"Created custom router with extractors: {extractor_names}")
        
        return router