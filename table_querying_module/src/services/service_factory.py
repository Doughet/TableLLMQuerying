"""
Service Factory for creating LLM and Database service instances.

This module provides a factory pattern for creating service instances
based on configuration, making it easy to switch between different
implementations.
"""

import logging
from typing import Dict, Any, Optional, Type, List
from dataclasses import dataclass, field

from .llm_service import LLMService
from .database_service import DatabaseService
from .implementations.openai_llm_service import OpenAILLMService
from .implementations.sqlite_database_service import SQLiteDatabaseService

# Conditionally import private BHUB implementation
try:
    from .private.bhub_llm_service import BHubLLMService
    _BHUB_AVAILABLE = True
except ImportError:
    _BHUB_AVAILABLE = False
    BHubLLMService = None

logger = logging.getLogger(__name__)


@dataclass
class ServiceConfig:
    """Configuration for service creation."""
    
    # LLM Service Configuration
    llm_service_type: str = "openai"  # "openai" or custom class name
    llm_api_key: str = ""
    llm_model_id: str = "gpt-3.5-turbo"
    llm_base_url: str = ""
    llm_organization: Optional[str] = None  # For OpenAI
    llm_timeout: int = 30
    llm_max_retries: int = 3
    llm_extra_config: Dict[str, Any] = field(default_factory=dict)
    
    # Database Service Configuration
    db_service_type: str = "sqlite"  # "sqlite" or custom class name
    db_path: str = "tables.db"
    db_timeout: float = 30.0
    db_auto_commit: bool = True
    db_extra_config: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ServiceConfig':
        """Create ServiceConfig from dictionary."""
        # Map common keys to our structure
        mapped_config = {}
        
        # LLM configuration mapping
        if 'api_key' in config_dict:
            mapped_config['llm_api_key'] = config_dict['api_key']
        if 'model_id' in config_dict:
            mapped_config['llm_model_id'] = config_dict['model_id']
        
        # Database configuration mapping
        if 'db_path' in config_dict:
            mapped_config['db_path'] = config_dict['db_path']
        
        # Direct mapping for service-specific keys
        for key, value in config_dict.items():
            if key.startswith('llm_') or key.startswith('db_'):
                mapped_config[key] = value
        
        # Create instance with mapped config
        return cls(**{k: v for k, v in mapped_config.items() if k in cls.__dataclass_fields__})


class ServiceFactory:
    """Factory for creating service instances."""
    
    # Registry for custom service implementations
    _llm_services: Dict[str, Type[LLMService]] = {
        "openai": OpenAILLMService,
    }
    
    # Add BHUB service if available (private implementation)
    if _BHUB_AVAILABLE:
        _llm_services["bhub"] = BHubLLMService
    
    _database_services: Dict[str, Type[DatabaseService]] = {
        "sqlite": SQLiteDatabaseService,
    }
    
    @classmethod
    def register_llm_service(cls, name: str, service_class: Type[LLMService]) -> None:
        """
        Register a custom LLM service implementation.
        
        Args:
            name: Service name identifier
            service_class: Class implementing LLMService interface
        """
        cls._llm_services[name] = service_class
        logger.info(f"Registered LLM service: {name}")
    
    @classmethod
    def register_database_service(cls, name: str, service_class: Type[DatabaseService]) -> None:
        """
        Register a custom database service implementation.
        
        Args:
            name: Service name identifier
            service_class: Class implementing DatabaseService interface
        """
        cls._database_services[name] = service_class
        logger.info(f"Registered database service: {name}")
    
    @classmethod
    def create_llm_service(cls, config: ServiceConfig) -> LLMService:
        """
        Create an LLM service instance.
        
        Args:
            config: Service configuration
            
        Returns:
            LLMService instance
            
        Raises:
            ValueError: If service type is not registered
            TypeError: If required configuration is missing
        """
        service_type = config.llm_service_type.lower()
        
        if service_type not in cls._llm_services:
            raise ValueError(f"Unknown LLM service type: {service_type}. Available: {list(cls._llm_services.keys())}")
        
        service_class = cls._llm_services[service_type]
        
        # Build service-specific configuration
        service_config = {
            "api_key": config.llm_api_key,
            "model_id": config.llm_model_id,
            "timeout": config.llm_timeout,
            **config.llm_extra_config
        }
        
        # Add service-specific parameters
        if service_type == "bhub" and config.llm_base_url:
            service_config["base_url"] = config.llm_base_url
        elif service_type == "openai":
            if config.llm_base_url:
                service_config["base_url"] = config.llm_base_url
            if config.llm_organization:
                service_config["organization"] = config.llm_organization
        
        # Validate required configuration
        if not config.llm_api_key:
            raise TypeError(f"API key is required for {service_type} LLM service")
        
        try:
            service = service_class(**service_config)
            logger.info(f"Created {service_type} LLM service with model {config.llm_model_id}")
            return service
        except Exception as e:
            logger.error(f"Failed to create {service_type} LLM service: {e}")
            raise
    
    @classmethod
    def create_database_service(cls, config: ServiceConfig) -> DatabaseService:
        """
        Create a database service instance.
        
        Args:
            config: Service configuration
            
        Returns:
            DatabaseService instance
            
        Raises:
            ValueError: If service type is not registered
            TypeError: If required configuration is missing
        """
        service_type = config.db_service_type.lower()
        
        if service_type not in cls._database_services:
            raise ValueError(f"Unknown database service type: {service_type}. Available: {list(cls._database_services.keys())}")
        
        service_class = cls._database_services[service_type]
        
        # Build service-specific configuration
        service_config = {
            "timeout": config.db_timeout,
            "auto_commit": config.db_auto_commit,
            **config.db_extra_config
        }
        
        # Add service-specific parameters
        if service_type == "sqlite":
            service_config["db_path"] = config.db_path
        
        # Validate required configuration
        if service_type == "sqlite" and not config.db_path:
            raise TypeError("Database path is required for SQLite service")
        
        try:
            service = service_class(**service_config)
            
            # Initialize the database
            if not service.initialize():
                raise RuntimeError(f"Failed to initialize {service_type} database service")
            
            logger.info(f"Created and initialized {service_type} database service")
            return service
        except Exception as e:
            logger.error(f"Failed to create {service_type} database service: {e}")
            raise
    
    @classmethod
    def create_services(cls, config: ServiceConfig) -> tuple[LLMService, DatabaseService]:
        """
        Create both LLM and database service instances.
        
        Args:
            config: Service configuration
            
        Returns:
            Tuple of (LLMService, DatabaseService)
        """
        llm_service = cls.create_llm_service(config)
        db_service = cls.create_database_service(config)
        
        return llm_service, db_service
    
    @classmethod
    def get_available_llm_services(cls) -> List[str]:
        """Get list of available LLM service types."""
        return list(cls._llm_services.keys())
    
    @classmethod
    def get_available_database_services(cls) -> List[str]:
        """Get list of available database service types."""
        return list(cls._database_services.keys())
    
    @classmethod
    def create_default_config(cls) -> ServiceConfig:
        """Create a default service configuration."""
        return ServiceConfig()
    
    @classmethod
    def create_config_template(cls) -> Dict[str, Any]:
        """Create a configuration template dictionary."""
        return {
            "# LLM Service Configuration": None,
            "llm_service_type": "openai",  # "openai" is the default
            "llm_api_key": "your-openai-api-key-here",
            "llm_model_id": "gpt-3.5-turbo",
            "llm_base_url": "",  # optional, service-specific base URL
            "llm_organization": None,  # optional, for OpenAI
            "llm_timeout": 30,
            "llm_max_retries": 3,
            
            "# Database Service Configuration": None,
            "db_service_type": "sqlite",
            "db_path": "tables.db",
            "db_timeout": 30.0,
            "db_auto_commit": True,
            
            "# Example configurations for different services": None,
            "example_openai_config": {
                "llm_service_type": "openai", 
                "llm_api_key": "your-openai-api-key",
                "llm_model_id": "gpt-3.5-turbo",
                "llm_organization": "your-org-id",  # optional
                "db_service_type": "sqlite",
                "db_path": "tables.db"
            },
            
            "example_openai_gpt4_config": {
                "llm_service_type": "openai",
                "llm_api_key": "your-openai-api-key",
                "llm_model_id": "gpt-4",
                "llm_organization": "your-org-id",  # optional
                "db_service_type": "sqlite",
                "db_path": "tables.db"
            }
        }