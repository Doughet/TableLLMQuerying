"""
Factory for creating TableProcessor instances with different architectures.

This provides a simple way to switch between the legacy and new interface-based
architectures based on configuration.
"""

import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path

logger = logging.getLogger(__name__)


class TableProcessorFactory:
    """Factory for creating TableProcessor instances."""
    
    @staticmethod
    def create_processor(
        config: Optional[Dict[str, Any]] = None,
        architecture: str = "auto"
    ) -> Union['TableProcessor', 'TableProcessorV2']:
        """
        Create a TableProcessor instance.
        
        Args:
            config: Configuration dictionary
            architecture: Architecture to use ("legacy", "interface", "auto")
            
        Returns:
            TableProcessor instance (legacy or new)
        """
        config = config or {}
        
        # Determine architecture
        if architecture == "auto":
            # Auto-detect based on configuration or environment
            architecture = config.get('architecture', 'interface')
            
            # Fallback logic - use interface architecture by default
            if architecture not in ['legacy', 'interface']:
                architecture = 'interface'
        
        logger.info(f"Creating TableProcessor with {architecture} architecture")
        
        try:
            if architecture == 'interface':
                return TableProcessorFactory._create_interface_processor(config)
            else:  # legacy
                return TableProcessorFactory._create_legacy_processor(config)
                
        except Exception as e:
            logger.error(f"Failed to create {architecture} processor: {e}")
            
            # Fallback to the other architecture
            fallback_arch = 'legacy' if architecture == 'interface' else 'interface'
            logger.warning(f"Falling back to {fallback_arch} architecture")
            
            if fallback_arch == 'interface':
                return TableProcessorFactory._create_interface_processor(config)
            else:
                return TableProcessorFactory._create_legacy_processor(config)
    
    @staticmethod
    def _create_interface_processor(config: Dict[str, Any]) -> 'TableProcessorV2':
        """Create a new interface-based processor."""
        try:
            from .table_processor_v2 import TableProcessorV2
            return TableProcessorV2(config)
        except Exception as e:
            logger.error(f"Failed to create interface processor: {e}")
            raise
    
    @staticmethod
    def _create_legacy_processor(config: Dict[str, Any]) -> 'TableProcessor':
        """Create a legacy processor."""
        try:
            from .table_processor import TableProcessor
            return TableProcessor(config)
        except Exception as e:
            logger.error(f"Failed to create legacy processor: {e}")
            raise
    
    @staticmethod
    def get_available_architectures() -> Dict[str, str]:
        """Get information about available architectures."""
        architectures = {}
        
        # Test legacy architecture
        try:
            from .table_processor import TableProcessor
            architectures['legacy'] = "Available - Legacy direct implementation"
        except ImportError as e:
            architectures['legacy'] = f"Not available - {e}"
        
        # Test interface architecture  
        try:
            from .table_processor_v2 import TableProcessorV2
            from ..core.interfaces import DocumentProcessor
            architectures['interface'] = "Available - Interface-based architecture"
        except ImportError as e:
            architectures['interface'] = f"Not available - {e}"
        
        return architectures
    
    @staticmethod
    def create_config_template(architecture: str = "interface") -> Dict[str, Any]:
        """Create a configuration template for the specified architecture."""
        base_config = {
            "# Architecture Configuration": None,
            "architecture": architecture,
            
            "# LLM Configuration": None, 
            "api_key": "your-openai-api-key-here",
            "model_id": "gpt-3.5-turbo",
            "llm_service_type": "openai",
            
            "# Database Configuration": None,
            "db_path": f"table_querying_{architecture}.db",
            
            "# Processing Options": None,
            "save_outputs": True,
            "clear_database_on_start": False,
            "context_hint": "",
            "output_dir": "table_querying_outputs",
            
            "# System Options": None,
            "environment": "development", 
            "debug": False
        }
        
        if architecture == "interface":
            base_config.update({
                "# Interface Architecture Specific": None,
                "component_registry_enabled": True,
                "dependency_injection": True,
                "plugin_support": True
            })
        
        return base_config


def create_processor(config: Optional[Dict[str, Any]] = None, **kwargs) -> Union['TableProcessor', 'TableProcessorV2']:
    """
    Convenience function for creating a TableProcessor.
    
    Args:
        config: Configuration dictionary
        **kwargs: Additional configuration options (will override config)
        
    Returns:
        TableProcessor instance
    """
    final_config = dict(config) if config else {}
    final_config.update(kwargs)
    
    architecture = final_config.get('architecture', 'interface')
    return TableProcessorFactory.create_processor(final_config, architecture)


def show_architecture_comparison():
    """Show a comparison of available architectures."""
    architectures = TableProcessorFactory.get_available_architectures()
    
    print("\n" + "="*80)
    print("TABLE PROCESSING ARCHITECTURES")
    print("="*80)
    
    print("\n🏛️  LEGACY ARCHITECTURE:")
    print("   - Direct component instantiation")
    print("   - Tightly coupled dependencies")
    print("   - Simpler setup and configuration")
    print("   - Proven stable implementation")
    print(f"   - Status: {architectures.get('legacy', 'Unknown')}")
    
    print("\n🔧 INTERFACE ARCHITECTURE (V2):")
    print("   - Interface-based design") 
    print("   - Dependency injection container")
    print("   - Component registry and factories")
    print("   - Plugin system support")
    print("   - More flexible and extensible")
    print(f"   - Status: {architectures.get('interface', 'Unknown')}")
    
    print("\n💡 RECOMMENDATION:")
    print("   - Use 'interface' for new projects and extensibility")
    print("   - Use 'legacy' for stability and simplicity")
    print("   - Factory supports automatic fallback between architectures")
    
    print("="*80)


if __name__ == "__main__":
    """Demo and testing."""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "compare":
        show_architecture_comparison()
        sys.exit(0)
    
    # Test both architectures
    test_config = {
        "api_key": "test-key",
        "db_path": ":memory:",  # In-memory database for testing
        "save_outputs": False
    }
    
    print("Testing TableProcessor architectures...")
    
    # Test interface architecture
    try:
        processor_v2 = TableProcessorFactory.create_processor(test_config, architecture="interface")
        print("✅ Interface architecture created successfully")
        
        # Test component info
        try:
            info = processor_v2.get_component_info()
            print(f"   - Components registered: {len(info.get('registered_components', {}))}")
            print(f"   - Dependencies valid: {info.get('dependency_validation', {}).get('valid', False)}")
        except Exception as e:
            print(f"   - Component info error: {e}")
            
    except Exception as e:
        print(f"❌ Interface architecture failed: {e}")
    
    # Test legacy architecture
    try:
        processor_v1 = TableProcessorFactory.create_processor(test_config, architecture="legacy")
        print("✅ Legacy architecture created successfully")
    except Exception as e:
        print(f"❌ Legacy architecture failed: {e}")
    
    print("\nArchitecture comparison:")
    show_architecture_comparison()