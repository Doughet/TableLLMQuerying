"""
Component factories for creating configured instances.

This module provides factory classes that create component instances
with proper configuration and dependency injection.
"""

import logging
from typing import Type, Dict, Any, Optional, List
from pathlib import Path

from ..core.interfaces import *
from ..core.types import ComponentConfig, SystemConfig
from ..core.registry import ComponentRegistry
from ..core.context import ProcessingContext
from ..core.exceptions import ComponentNotFoundError, ConfigurationError

logger = logging.getLogger(__name__)


class ComponentFactory:
    """Base factory for creating component instances."""
    
    def __init__(self, context: ProcessingContext):
        self.context = context
        self.registry = context.registry
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def create_component(self, component_type: str, config: Optional[Dict[str, Any]] = None) -> Any:
        """Create a component instance with configuration."""
        try:
            # Merge configuration
            merged_config = self._merge_config(component_type, config or {})
            
            # Get component from registry
            component = self.registry.get_component(component_type, **merged_config)
            
            self._logger.debug(f"Created component: {component_type}")
            return component
            
        except Exception as e:
            self._logger.error(f"Failed to create component {component_type}: {e}")
            raise ComponentNotFoundError(
                f"Could not create component '{component_type}'",
                error_code="COMPONENT_CREATION_FAILED",
                cause=e
            )
    
    def _merge_config(self, component_type: str, override_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge component configuration from multiple sources."""
        # Start with global configuration
        merged_config = dict(self.context.config.global_settings)
        
        # Add component-specific configuration
        component_config = self.context.config.get_component_config(component_type)
        if component_config:
            merged_config.update(component_config.config)
        
        # Override with provided configuration
        merged_config.update(override_config)
        
        return merged_config


class DocumentProcessorFactory(ComponentFactory):
    """Factory for creating document processor instances."""
    
    def create_document_processor(
        self,
        extractor_type: str = "default",
        schema_type: str = "default",
        descriptor_type: str = "default",
        database_type: str = "default",
        config: Optional[Dict[str, Any]] = None
    ) -> DocumentProcessor:
        """Create a configured document processor."""
        
        # Create sub-components
        table_extractor = self.create_component("table_extractor", {"implementation": extractor_type})
        schema_generator = self.create_component("schema_generator", {"implementation": schema_type})
        table_descriptor = self.create_component("table_descriptor", {"implementation": descriptor_type})
        database_client = self.create_component("database_client", {"implementation": database_type})
        
        # Create processor configuration
        processor_config = self._merge_config("document_processor", config or {})
        processor_config.update({
            "table_extractor": table_extractor,
            "schema_generator": schema_generator,
            "table_descriptor": table_descriptor,
            "database_client": database_client
        })
        
        return self.create_component("document_processor", processor_config)


class LLMClientFactory(ComponentFactory):
    """Factory for creating LLM client instances."""
    
    SUPPORTED_PROVIDERS = {
        "bhub": "BHubLLMClient",
        "openai": "OpenAILLMClient",
        "azure": "AzureOpenAILLMClient",
        "ollama": "OllamaLLMClient",
        "anthropic": "AnthropicLLMClient",
        "huggingface": "HuggingFaceLLMClient"
    }
    
    def create_llm_client(
        self,
        provider: str,
        model_id: str,
        api_key: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> LLMClient:
        """Create an LLM client for the specified provider."""
        
        if provider not in self.SUPPORTED_PROVIDERS:
            raise ConfigurationError(
                f"Unsupported LLM provider: {provider}",
                error_code="UNSUPPORTED_PROVIDER",
                details={"supported_providers": list(self.SUPPORTED_PROVIDERS.keys())}
            )
        
        # Create client configuration
        client_config = self._merge_config("llm_client", config or {})
        client_config.update({
            "provider": provider,
            "model_id": model_id,
            "api_key": api_key or self.context.get_config(f"{provider}_api_key")
        })
        
        # Add provider-specific configuration
        provider_config = self.context.get_config(f"{provider}_config", {})
        client_config.update(provider_config)
        
        return self.create_component("llm_client", client_config)
    
    def create_multi_provider_client(
        self,
        providers: List[Dict[str, Any]],
        fallback_strategy: str = "round_robin"
    ) -> LLMClient:
        """Create a multi-provider LLM client with fallback support."""
        
        # Create individual clients
        clients = []
        for provider_config in providers:
            client = self.create_llm_client(**provider_config)
            clients.append(client)
        
        # Create multi-provider wrapper
        multi_config = {
            "clients": clients,
            "fallback_strategy": fallback_strategy
        }
        
        return self.create_component("multi_llm_client", multi_config)


class DatabaseClientFactory(ComponentFactory):
    """Factory for creating database client instances."""
    
    SUPPORTED_DATABASES = {
        "sqlite": "SQLiteDatabaseClient",
        "postgresql": "PostgreSQLDatabaseClient",
        "mysql": "MySQLDatabaseClient",
        "mongodb": "MongoDBDatabaseClient",
        "elasticsearch": "ElasticsearchDatabaseClient"
    }
    
    def create_database_client(
        self,
        database_type: str,
        connection_config: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> DatabaseClient:
        """Create a database client for the specified type."""
        
        if database_type not in self.SUPPORTED_DATABASES:
            raise ConfigurationError(
                f"Unsupported database type: {database_type}",
                error_code="UNSUPPORTED_DATABASE",
                details={"supported_databases": list(self.SUPPORTED_DATABASES.keys())}
            )
        
        # Create client configuration
        client_config = self._merge_config("database_client", config or {})
        client_config.update({
            "database_type": database_type,
            "connection": connection_config
        })
        
        return self.create_component("database_client", client_config)
    
    def create_sqlite_client(self, db_path: Path, config: Optional[Dict[str, Any]] = None) -> DatabaseClient:
        """Create a SQLite database client."""
        connection_config = {"db_path": str(db_path)}
        return self.create_database_client("sqlite", connection_config, config)
    
    def create_postgresql_client(
        self,
        host: str,
        database: str,
        username: str,
        password: str,
        port: int = 5432,
        config: Optional[Dict[str, Any]] = None
    ) -> DatabaseClient:
        """Create a PostgreSQL database client."""
        connection_config = {
            "host": host,
            "port": port,
            "database": database,
            "username": username,
            "password": password
        }
        return self.create_database_client("postgresql", connection_config, config)


class QueryProcessorFactory(ComponentFactory):
    """Factory for creating query processor instances."""
    
    def create_query_processor(
        self,
        llm_client: Optional[LLMClient] = None,
        database_client: Optional[DatabaseClient] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> QueryProcessor:
        """Create a configured query processor."""
        
        # Create or use provided clients
        if llm_client is None:
            llm_client = self.create_component("llm_client")
        
        if database_client is None:
            database_client = self.create_component("database_client")
        
        # Create processor configuration
        processor_config = self._merge_config("query_processor", config or {})
        processor_config.update({
            "llm_client": llm_client,
            "database_client": database_client
        })
        
        return self.create_component("query_processor", processor_config)


class ChatInterfaceFactory(ComponentFactory):
    """Factory for creating chat interface instances."""
    
    def create_chat_interface(
        self,
        query_processor: Optional[QueryProcessor] = None,
        session_manager: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> ChatInterface:
        """Create a configured chat interface."""
        
        # Create or use provided components
        if query_processor is None:
            query_processor = self.create_component("query_processor")
        
        if session_manager is None:
            session_manager = self.create_component("session_manager", {})
        
        # Create interface configuration
        interface_config = self._merge_config("chat_interface", config or {})
        interface_config.update({
            "query_processor": query_processor,
            "session_manager": session_manager
        })
        
        return self.create_component("chat_interface", interface_config)


class PluginFactory:
    """Factory for creating plugin-based components."""
    
    def __init__(self, context: ProcessingContext):
        self.context = context
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def load_component_plugin(
        self,
        plugin_path: Path,
        component_type: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Load a component from a plugin file."""
        
        # Load plugin module
        import importlib.util
        import sys
        
        spec = importlib.util.spec_from_file_location(plugin_path.stem, plugin_path)
        if spec is None or spec.loader is None:
            raise ConfigurationError(f"Cannot load plugin from {plugin_path}")
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[plugin_path.stem] = module
        spec.loader.exec_module(module)
        
        # Look for component factory function
        factory_func_name = f"create_{component_type}"
        if hasattr(module, factory_func_name):
            factory_func = getattr(module, factory_func_name)
            component = factory_func(self.context, **(config or {}))
            self._logger.info(f"Loaded component {component_type} from plugin: {plugin_path}")
            return component
        
        # Look for component class
        component_class_name = f"{component_type.title()}Component"
        if hasattr(module, component_class_name):
            component_class = getattr(module, component_class_name)
            component = component_class(**(config or {}))
            self._logger.info(f"Created component {component_type} from plugin: {plugin_path}")
            return component
        
        raise ConfigurationError(
            f"Plugin {plugin_path} does not provide component {component_type}",
            error_code="PLUGIN_COMPONENT_NOT_FOUND"
        )


# Pre-configured factory functions
def create_default_factories(context: ProcessingContext) -> Dict[str, ComponentFactory]:
    """Create a set of default component factories."""
    return {
        "document_processor": DocumentProcessorFactory(context),
        "llm_client": LLMClientFactory(context),
        "database_client": DatabaseClientFactory(context),
        "query_processor": QueryProcessorFactory(context),
        "chat_interface": ChatInterfaceFactory(context),
        "plugin": PluginFactory(context)
    }


def create_production_factories(context: ProcessingContext) -> Dict[str, ComponentFactory]:
    """Create production-optimized component factories."""
    factories = create_default_factories(context)
    
    # Add production-specific configurations
    # This could include connection pooling, caching, monitoring, etc.
    
    return factories