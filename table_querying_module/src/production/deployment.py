"""
Deployment utilities and system validation.

This module provides tools for deploying the system in production,
including health checks, system validation, and deployment helpers.
"""

import logging
import sys
import time
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field
import subprocess
import json

from ..core.context import ProcessingContext
from ..core.registry import ComponentRegistry
from ..core.exceptions import ValidationError, ConfigurationError
from .config import ProductionConfig

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of system validation."""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    checks_passed: int = 0
    checks_total: int = 0
    
    def add_error(self, message: str) -> None:
        """Add an error and mark as invalid."""
        self.errors.append(message)
        self.valid = False
    
    def add_warning(self, message: str) -> None:
        """Add a warning."""
        self.warnings.append(message)
    
    def success_rate(self) -> float:
        """Get success rate as percentage."""
        if self.checks_total == 0:
            return 100.0
        return (self.checks_passed / self.checks_total) * 100


class SystemValidator:
    """Validates system configuration and dependencies."""
    
    def __init__(self, config: ProductionConfig):
        self.config = config
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def validate_all(self) -> ValidationResult:
        """Run all validation checks."""
        result = ValidationResult(valid=True)
        
        checks = [
            self._check_python_version,
            self._check_dependencies,
            self._check_database_connection,
            self._check_llm_service,
            self._check_file_permissions,
            self._check_memory_limits,
            self._check_network_connectivity,
            self._check_security_settings
        ]
        
        result.checks_total = len(checks)
        
        for check in checks:
            try:
                check_result = check()
                if check_result:
                    result.checks_passed += 1
                    self._logger.debug(f"Check passed: {check.__name__}")
                else:
                    result.add_error(f"Check failed: {check.__name__}")
                    self._logger.error(f"Check failed: {check.__name__}")
            except Exception as e:
                result.add_error(f"Check error {check.__name__}: {str(e)}")
                self._logger.error(f"Check error {check.__name__}: {e}")
        
        self._logger.info(f"Validation completed: {result.success_rate():.1f}% passed")
        return result
    
    def _check_python_version(self) -> bool:
        """Check Python version compatibility."""
        min_version = (3, 8)
        current_version = sys.version_info[:2]
        
        if current_version < min_version:
            self._logger.error(f"Python {min_version} or higher required, got {current_version}")
            return False
        
        return True
    
    def _check_dependencies(self) -> bool:
        """Check required dependencies are installed."""
        required_packages = [
            'requests', 'pandas', 'beautifulsoup4', 'lxml', 'pydantic'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            self._logger.error(f"Missing required packages: {', '.join(missing_packages)}")
            return False
        
        return True
    
    def _check_database_connection(self) -> bool:
        """Check database connectivity."""
        try:
            # Create a temporary database client to test connection
            from ..components.factories import DatabaseClientFactory
            from ..core.context import create_default_context
            
            context = create_default_context()
            factory = DatabaseClientFactory(context)
            
            if self.config.database.type == "sqlite":
                client = factory.create_sqlite_client(Path(self.config.database.database))
            elif self.config.database.type == "postgresql":
                client = factory.create_postgresql_client(
                    host=self.config.database.host,
                    database=self.config.database.database,
                    username=self.config.database.username,
                    password=self.config.database.password,
                    port=self.config.database.port
                )
            else:
                self._logger.warning(f"Unknown database type: {self.config.database.type}")
                return True  # Skip validation for unknown types
            
            return client.health_check()
            
        except Exception as e:
            self._logger.error(f"Database connection check failed: {e}")
            return False
    
    def _check_llm_service(self) -> bool:
        """Check LLM service availability."""
        try:
            from ..components.factories import LLMClientFactory
            from ..core.context import create_default_context
            
            context = create_default_context()
            factory = LLMClientFactory(context)
            
            client = factory.create_llm_client(
                provider=self.config.llm.provider,
                model_id=self.config.llm.model_id,
                api_key=self.config.llm.api_key
            )
            
            return client.is_available()
            
        except Exception as e:
            self._logger.error(f"LLM service check failed: {e}")
            return False
    
    def _check_file_permissions(self) -> bool:
        """Check file system permissions."""
        paths_to_check = [
            Path(self.config.logging.log_file_path).parent,
            Path.cwd(),  # Current working directory
        ]
        
        for path in paths_to_check:
            if path.exists():
                if not os.access(path, os.R_OK | os.W_OK):
                    self._logger.error(f"Insufficient permissions for {path}")
                    return False
            else:
                try:
                    path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    self._logger.error(f"Cannot create directory {path}: {e}")
                    return False
        
        return True
    
    def _check_memory_limits(self) -> bool:
        """Check available memory."""
        try:
            import psutil
            memory = psutil.virtual_memory()
            
            # Check if we have at least 1GB available
            min_memory_gb = 1
            available_gb = memory.available / (1024 ** 3)
            
            if available_gb < min_memory_gb:
                self._logger.warning(f"Low available memory: {available_gb:.1f}GB (minimum: {min_memory_gb}GB)")
                return False
            
            return True
            
        except ImportError:
            self._logger.debug("psutil not available, skipping memory check")
            return True  # Skip if psutil not available
        except Exception as e:
            self._logger.error(f"Memory check failed: {e}")
            return False
    
    def _check_network_connectivity(self) -> bool:
        """Check network connectivity to required services."""
        import socket
        
        # Check LLM service connectivity
        if self.config.llm.base_url:
            from urllib.parse import urlparse
            parsed_url = urlparse(self.config.llm.base_url)
            host = parsed_url.hostname
            port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
            
            try:
                socket.create_connection((host, port), timeout=10)
                self._logger.debug(f"Network connectivity OK: {host}:{port}")
            except Exception as e:
                self._logger.error(f"Cannot connect to {host}:{port}: {e}")
                return False
        
        return True
    
    def _check_security_settings(self) -> bool:
        """Check security configuration."""
        if self.config.security.enable_authentication:
            if not self.config.security.jwt_secret_key:
                self._logger.error("JWT secret key required when authentication is enabled")
                return False
            
            if len(self.config.security.jwt_secret_key) < 32:
                self._logger.warning("JWT secret key should be at least 32 characters long")
        
        if self.config.environment == "production":
            if self.config.debug:
                self._logger.warning("Debug mode should be disabled in production")
            
            if not self.config.security.enable_https_only:
                self._logger.warning("HTTPS should be enforced in production")
        
        return True


class DeploymentManager:
    """Manages system deployment tasks."""
    
    def __init__(self, config: ProductionConfig):
        self.config = config
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def deploy(self, validate_first: bool = True) -> bool:
        """Deploy the system with configuration."""
        self._logger.info("Starting system deployment")
        
        try:
            # Validate system if requested
            if validate_first:
                validator = SystemValidator(self.config)
                validation_result = validator.validate_all()
                
                if not validation_result.valid:
                    self._logger.error(f"Validation failed: {validation_result.errors}")
                    return False
                
                if validation_result.warnings:
                    self._logger.warning(f"Validation warnings: {validation_result.warnings}")
            
            # Initialize logging
            self._setup_logging()
            
            # Initialize database
            self._initialize_database()
            
            # Initialize components
            self._initialize_components()
            
            # Setup monitoring if enabled
            if self.config.monitoring.enable_metrics:
                self._setup_monitoring()
            
            self._logger.info("System deployment completed successfully")
            return True
            
        except Exception as e:
            self._logger.error(f"Deployment failed: {e}")
            return False
    
    def _setup_logging(self) -> None:
        """Setup production logging."""
        from .logging import setup_logging
        setup_logging(self.config.logging)
    
    def _initialize_database(self) -> None:
        """Initialize database connection and schema."""
        self._logger.info("Initializing database")
        
        from ..components.factories import DatabaseClientFactory
        from ..core.context import create_production_context
        
        context = create_production_context()
        factory = DatabaseClientFactory(context)
        
        # Create database client based on configuration
        if self.config.database.type == "sqlite":
            db_path = Path(self.config.database.database)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            client = factory.create_sqlite_client(db_path)
        else:
            connection_config = self.config.database.get_connection_params()
            client = factory.create_database_client(self.config.database.type, connection_config)
        
        # Test connection
        if not client.health_check():
            raise ConfigurationError("Database health check failed")
        
        self._logger.info("Database initialized successfully")
    
    def _initialize_components(self) -> None:
        """Initialize system components."""
        self._logger.info("Initializing system components")
        
        from ..core.context import create_production_context
        from ..components.factories import create_production_factories
        
        context = create_production_context()
        factories = create_production_factories(context)
        
        # Initialize core components
        document_processor = factories["document_processor"].create_document_processor()
        query_processor = factories["query_processor"].create_query_processor()
        chat_interface = factories["chat_interface"].create_chat_interface()
        
        # Store in global registry for access
        context.registry.register_component("document_processor", type(document_processor))
        context.registry.register_component("query_processor", type(query_processor))
        context.registry.register_component("chat_interface", type(chat_interface))
        
        self._logger.info("System components initialized successfully")
    
    def _setup_monitoring(self) -> None:
        """Setup monitoring and metrics collection."""
        self._logger.info("Setting up monitoring")
        
        from .monitoring import setup_monitoring
        setup_monitoring(self.config.monitoring)
        
        self._logger.info("Monitoring setup completed")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        health_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "version": self.config.version,
            "environment": self.config.environment,
            "checks": {}
        }
        
        try:
            # Check database
            try:
                from ..core.registry import get_component
                db_client = get_component("database_client")
                health_status["checks"]["database"] = {
                    "status": "healthy" if db_client.health_check() else "unhealthy"
                }
            except Exception as e:
                health_status["checks"]["database"] = {"status": "unhealthy", "error": str(e)}
            
            # Check LLM service
            try:
                llm_client = get_component("llm_client")
                health_status["checks"]["llm_service"] = {
                    "status": "healthy" if llm_client.is_available() else "unhealthy"
                }
            except Exception as e:
                health_status["checks"]["llm_service"] = {"status": "unhealthy", "error": str(e)}
            
            # Overall status
            unhealthy_checks = [
                check for check in health_status["checks"].values()
                if check["status"] != "healthy"
            ]
            
            if unhealthy_checks:
                health_status["status"] = "unhealthy"
            
        except Exception as e:
            health_status["status"] = "error"
            health_status["error"] = str(e)
        
        return health_status
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information."""
        info = {
            "version": self.config.version,
            "environment": self.config.environment,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "configuration": {
                "database_type": self.config.database.type,
                "llm_provider": self.config.llm.provider,
                "authentication_enabled": self.config.security.enable_authentication,
                "monitoring_enabled": self.config.monitoring.enable_metrics
            }
        }
        
        # Add memory information if available
        try:
            import psutil
            memory = psutil.virtual_memory()
            info["system"] = {
                "memory_total_gb": memory.total / (1024 ** 3),
                "memory_available_gb": memory.available / (1024 ** 3),
                "cpu_count": psutil.cpu_count()
            }
        except ImportError:
            pass
        
        return info


def create_deployment_script(config: ProductionConfig, output_path: Path) -> None:
    """Create a deployment script for the given configuration."""
    script_content = f"""#!/bin/bash
# Deployment script for Table Querying Module
# Generated automatically - do not edit manually

set -e

echo "Starting Table Querying Module deployment..."

# Environment variables
export ENVIRONMENT="{config.environment}"
export DEBUG="{str(config.debug).lower()}"
export DB_TYPE="{config.database.type}"
export DB_HOST="{config.database.host}"
export DB_PORT="{config.database.port}"
export DB_NAME="{config.database.database}"
export LLM_PROVIDER="{config.llm.provider}"
export LLM_MODEL_ID="{config.llm.model_id}"
export LOG_LEVEL="{config.logging.level}"

# Create necessary directories
mkdir -p "$(dirname "{config.logging.log_file_path}")"

# Install dependencies
pip install -r requirements.txt

# Run system validation
python -m src.production.deployment validate

# Start the application
python -m src.main

echo "Deployment completed successfully!"
"""
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(script_content)
    
    # Make script executable
    import stat
    output_path.chmod(stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
    
    logger.info(f"Deployment script created: {output_path}")


if __name__ == "__main__":
    """Command-line interface for deployment tools."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Table Querying Module deployment tools")
    parser.add_argument("action", choices=["validate", "deploy", "health", "info"], help="Action to perform")
    parser.add_argument("--config", type=Path, help="Configuration file path")
    parser.add_argument("--output", type=Path, help="Output path for generated files")
    
    args = parser.parse_args()
    
    # Load configuration
    from .config import load_production_config
    config = load_production_config(args.config)
    
    if args.action == "validate":
        validator = SystemValidator(config)
        result = validator.validate_all()
        
        print(f"Validation result: {'PASS' if result.valid else 'FAIL'}")
        print(f"Checks passed: {result.checks_passed}/{result.checks_total}")
        
        if result.errors:
            print("\nErrors:")
            for error in result.errors:
                print(f"  - {error}")
        
        if result.warnings:
            print("\nWarnings:")
            for warning in result.warnings:
                print(f"  - {warning}")
        
        sys.exit(0 if result.valid else 1)
    
    elif args.action == "deploy":
        manager = DeploymentManager(config)
        success = manager.deploy()
        sys.exit(0 if success else 1)
    
    elif args.action == "health":
        manager = DeploymentManager(config)
        health = manager.health_check()
        print(json.dumps(health, indent=2))
        sys.exit(0 if health["status"] == "healthy" else 1)
    
    elif args.action == "info":
        manager = DeploymentManager(config)
        info = manager.get_system_info()
        print(json.dumps(info, indent=2))