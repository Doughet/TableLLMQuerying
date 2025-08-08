"""
Production configuration management.

This module provides comprehensive configuration management for production
deployments, including environment-based configs, validation, and secrets handling.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse
import warnings

from ..core.types import SystemConfig, ComponentConfig
from ..core.exceptions import ConfigurationError, ValidationError

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration."""
    type: str = "sqlite"
    host: str = "localhost"
    port: int = 5432
    database: str = "tables"
    username: Optional[str] = None
    password: Optional[str] = None
    connection_string: Optional[str] = None
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    ssl_mode: str = "prefer"
    
    def get_connection_params(self) -> Dict[str, Any]:
        """Get connection parameters for database client."""
        if self.connection_string:
            return {"connection_string": self.connection_string}
        
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "username": self.username,
            "password": self.password,
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "ssl_mode": self.ssl_mode
        }


@dataclass
class LLMConfig:
    """LLM service configuration."""
    provider: str = "bhub"
    model_id: str = "mistral-small"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    organization: Optional[str] = None
    max_tokens: int = 1000
    temperature: float = 0.1
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    rate_limit: Optional[int] = None
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.api_key:
            warnings.warn(f"No API key provided for {self.provider} LLM service")


@dataclass
class SecurityConfig:
    """Security configuration."""
    enable_authentication: bool = False
    jwt_secret_key: Optional[str] = None
    jwt_expiration_hours: int = 24
    allowed_origins: List[str] = field(default_factory=lambda: ["*"])
    api_key_header: str = "X-API-Key"
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600  # 1 hour
    enable_https_only: bool = True
    enable_cors: bool = True


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    enable_file_logging: bool = True
    log_file_path: str = "logs/table_querying.log"
    max_file_size_mb: int = 100
    backup_count: int = 5
    enable_json_logging: bool = False
    enable_structured_logging: bool = True


@dataclass
class MonitoringConfig:
    """Monitoring and metrics configuration."""
    enable_metrics: bool = True
    metrics_port: int = 8001
    enable_health_checks: bool = True
    health_check_interval: int = 60
    enable_tracing: bool = False
    tracing_service_name: str = "table-querying-module"
    prometheus_endpoint: str = "/metrics"


@dataclass
class ProcessingConfig:
    """Processing configuration."""
    max_concurrent_documents: int = 5
    document_timeout_seconds: int = 300
    max_table_size_mb: int = 100
    enable_table_caching: bool = True
    cache_ttl_seconds: int = 3600
    batch_size: int = 10
    enable_async_processing: bool = False
    processing_queue_size: int = 100


@dataclass
class ProductionConfig:
    """Complete production configuration."""
    environment: str = "production"
    debug: bool = False
    version: str = "1.0.0"
    
    # Service configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    
    # Additional settings
    additional_settings: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> None:
        """Validate configuration."""
        errors = []
        
        # Validate database configuration
        if self.database.type == "postgresql":
            if not self.database.username or not self.database.password:
                errors.append("PostgreSQL requires username and password")
        
        # Validate LLM configuration
        if not self.llm.api_key:
            errors.append("LLM API key is required")
        
        # Validate security configuration
        if self.security.enable_authentication and not self.security.jwt_secret_key:
            errors.append("JWT secret key is required when authentication is enabled")
        
        # Validate logging configuration
        if self.logging.enable_file_logging:
            log_dir = Path(self.logging.log_file_path).parent
            if not log_dir.exists():
                try:
                    log_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    errors.append(f"Cannot create log directory {log_dir}: {e}")
        
        if errors:
            raise ConfigurationError(
                f"Configuration validation failed: {'; '.join(errors)}",
                error_code="CONFIG_VALIDATION_FAILED",
                details={"errors": errors}
            )
    
    def to_system_config(self) -> SystemConfig:
        """Convert to SystemConfig format."""
        components = {}
        
        # Database component config
        components["database_client"] = ComponentConfig(
            component_type="database_client",
            implementation=f"{self.database.type}_client",
            config=self.database.get_connection_params()
        )
        
        # LLM component config
        components["llm_client"] = ComponentConfig(
            component_type="llm_client",
            implementation=f"{self.llm.provider}_client",
            config={
                "model_id": self.llm.model_id,
                "api_key": self.llm.api_key,
                "base_url": self.llm.base_url,
                "max_tokens": self.llm.max_tokens,
                "temperature": self.llm.temperature,
                "timeout": self.llm.timeout,
                "max_retries": self.llm.max_retries
            }
        )
        
        return SystemConfig(
            components=components,
            global_settings=self.additional_settings,
            environment=self.environment,
            debug=self.debug
        )


class ConfigurationManager:
    """Manages configuration loading and validation."""
    
    def __init__(self):
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def load_from_file(self, config_path: Path) -> ProductionConfig:
        """Load configuration from file."""
        if not config_path.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r') as f:
                if config_path.suffix.lower() == '.json':
                    config_dict = json.load(f)
                elif config_path.suffix.lower() in ['.yaml', '.yml']:
                    import yaml
                    config_dict = yaml.safe_load(f)
                else:
                    raise ConfigurationError(f"Unsupported configuration file format: {config_path.suffix}")
            
            return self._dict_to_config(config_dict)
            
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration from {config_path}: {e}", cause=e)
    
    def load_from_env(self) -> ProductionConfig:
        """Load configuration from environment variables."""
        config = ProductionConfig()
        
        # Load database configuration
        config.database.type = os.getenv("DB_TYPE", config.database.type)
        config.database.host = os.getenv("DB_HOST", config.database.host)
        config.database.port = int(os.getenv("DB_PORT", str(config.database.port)))
        config.database.database = os.getenv("DB_NAME", config.database.database)
        config.database.username = os.getenv("DB_USERNAME")
        config.database.password = os.getenv("DB_PASSWORD")
        config.database.connection_string = os.getenv("DATABASE_URL")
        
        # Load LLM configuration
        config.llm.provider = os.getenv("LLM_PROVIDER", config.llm.provider)
        config.llm.model_id = os.getenv("LLM_MODEL_ID", config.llm.model_id)
        config.llm.api_key = os.getenv("LLM_API_KEY")
        config.llm.base_url = os.getenv("LLM_BASE_URL")
        config.llm.organization = os.getenv("LLM_ORGANIZATION")
        
        # Load security configuration
        config.security.enable_authentication = os.getenv("ENABLE_AUTH", "false").lower() == "true"
        config.security.jwt_secret_key = os.getenv("JWT_SECRET_KEY")
        
        # Load logging configuration
        config.logging.level = os.getenv("LOG_LEVEL", config.logging.level)
        config.logging.log_file_path = os.getenv("LOG_FILE_PATH", config.logging.log_file_path)
        
        # Load general settings
        config.environment = os.getenv("ENVIRONMENT", config.environment)
        config.debug = os.getenv("DEBUG", "false").lower() == "true"
        
        return config
    
    def merge_configs(self, *configs: ProductionConfig) -> ProductionConfig:
        """Merge multiple configurations, with later configs overriding earlier ones."""
        if not configs:
            return ProductionConfig()
        
        base_config = configs[0]
        
        for config in configs[1:]:
            # Merge each dataclass field
            for field_name in base_config.__dataclass_fields__.keys():
                if field_name == "additional_settings":
                    # Merge dictionaries
                    base_config.additional_settings.update(config.additional_settings)
                elif hasattr(config, field_name):
                    # Override with non-None values
                    new_value = getattr(config, field_name)
                    if new_value is not None:
                        setattr(base_config, field_name, new_value)
        
        return base_config
    
    def _dict_to_config(self, config_dict: Dict[str, Any]) -> ProductionConfig:
        """Convert dictionary to ProductionConfig."""
        # This is a simplified version - in production you'd want more robust conversion
        config = ProductionConfig()
        
        # Map dictionary keys to config structure
        if "database" in config_dict:
            db_config = config_dict["database"]
            for key, value in db_config.items():
                if hasattr(config.database, key):
                    setattr(config.database, key, value)
        
        if "llm" in config_dict:
            llm_config = config_dict["llm"]
            for key, value in llm_config.items():
                if hasattr(config.llm, key):
                    setattr(config.llm, key, value)
        
        # Add other config sections as needed
        
        return config


def load_production_config(
    config_file: Optional[Path] = None,
    use_env: bool = True,
    validate: bool = True
) -> ProductionConfig:
    """
    Load production configuration from multiple sources.
    
    Args:
        config_file: Optional configuration file path
        use_env: Whether to load from environment variables
        validate: Whether to validate the configuration
        
    Returns:
        ProductionConfig instance
    """
    manager = ConfigurationManager()
    configs = []
    
    # Load from file if provided
    if config_file:
        configs.append(manager.load_from_file(config_file))
    
    # Load from environment variables
    if use_env:
        configs.append(manager.load_from_env())
    
    # If no configs loaded, use default
    if not configs:
        configs.append(ProductionConfig())
    
    # Merge configurations
    config = manager.merge_configs(*configs)
    
    # Validate if requested
    if validate:
        config.validate()
    
    logger.info(f"Loaded production configuration for environment: {config.environment}")
    return config


def create_config_template() -> Dict[str, Any]:
    """Create a configuration template for production deployment."""
    return {
        "environment": "production",
        "debug": False,
        "version": "1.0.0",
        
        "database": {
            "type": "postgresql",  # or "sqlite"
            "host": "localhost",
            "port": 5432,
            "database": "table_querying",
            "username": "${DB_USERNAME}",
            "password": "${DB_PASSWORD}",
            "pool_size": 10,
            "max_overflow": 20,
            "ssl_mode": "require"
        },
        
        "llm": {
            "provider": "bhub",  # or "openai", "azure", etc.
            "model_id": "mistral-small",
            "api_key": "${LLM_API_KEY}",
            "max_tokens": 1000,
            "temperature": 0.1,
            "timeout": 30,
            "max_retries": 3
        },
        
        "security": {
            "enable_authentication": True,
            "jwt_secret_key": "${JWT_SECRET_KEY}",
            "jwt_expiration_hours": 24,
            "allowed_origins": ["https://yourdomain.com"],
            "rate_limit_requests": 100,
            "rate_limit_window": 3600,
            "enable_https_only": True
        },
        
        "logging": {
            "level": "INFO",
            "enable_file_logging": True,
            "log_file_path": "/var/log/table_querying/app.log",
            "max_file_size_mb": 100,
            "backup_count": 5,
            "enable_structured_logging": True
        },
        
        "monitoring": {
            "enable_metrics": True,
            "metrics_port": 8001,
            "enable_health_checks": True,
            "health_check_interval": 60,
            "prometheus_endpoint": "/metrics"
        },
        
        "processing": {
            "max_concurrent_documents": 10,
            "document_timeout_seconds": 300,
            "max_table_size_mb": 100,
            "enable_table_caching": True,
            "cache_ttl_seconds": 3600,
            "batch_size": 20
        }
    }