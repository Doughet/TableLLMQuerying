"""
Service Configuration Examples

This file shows different ways to configure and use the service system
with various LLM and database providers.
"""

import json
import os
from pathlib import Path
from src.services.service_factory import ServiceFactory, ServiceConfig


def example_bhub_configuration():
    """Example configuration for BHub LLM service."""
    config = ServiceConfig(
        llm_service_type="bhub",
        llm_api_key=os.getenv("BHUB_API_KEY", "your-bhub-api-key"),
        llm_model_id="mistral-small",
        llm_base_url="https://api.olympia.bhub.cloud/v1",
        llm_timeout=30,
        db_service_type="sqlite",
        db_path="tables_bhub.db"
    )
    
    return config


def example_openai_configuration():
    """Example configuration for OpenAI LLM service.""" 
    config = ServiceConfig(
        llm_service_type="openai",
        llm_api_key=os.getenv("OPENAI_API_KEY", "your-openai-api-key"),
        llm_model_id="gpt-3.5-turbo",
        llm_organization=os.getenv("OPENAI_ORG_ID"),  # Optional
        llm_timeout=30,
        db_service_type="sqlite",
        db_path="tables_openai.db"
    )
    
    return config


def example_azure_openai_configuration():
    """Example configuration for Azure OpenAI service."""
    config = ServiceConfig(
        llm_service_type="openai",  # Uses OpenAI service with custom base URL
        llm_api_key=os.getenv("AZURE_OPENAI_API_KEY", "your-azure-api-key"),
        llm_model_id="gpt-35-turbo",  # Azure model deployment name
        llm_base_url="https://your-resource.openai.azure.com/",
        llm_extra_config={
            "api_version": "2023-12-01-preview"  # Azure API version
        },
        db_service_type="sqlite",
        db_path="tables_azure.db"
    )
    
    return config


def example_custom_services_configuration():
    """Example configuration using custom Ollama and PostgreSQL services."""
    # First register custom services (would be done in your custom modules)
    # ServiceFactory.register_llm_service("ollama", OllamaLLMService)
    # ServiceFactory.register_database_service("postgresql", PostgreSQLDatabaseService)
    
    config = ServiceConfig(
        llm_service_type="ollama",
        llm_model_id="llama2",
        llm_base_url="http://localhost:11434",
        llm_timeout=60,
        db_service_type="postgresql",
        db_extra_config={
            "host": "localhost",
            "port": 5432,
            "database": "tables",
            "username": "postgres",
            "password": os.getenv("POSTGRES_PASSWORD", "password")
        }
    )
    
    return config


def create_configuration_from_file(config_file: str) -> ServiceConfig:
    """Load configuration from JSON file."""
    with open(config_file, 'r') as f:
        config_dict = json.load(f)
    
    return ServiceConfig.from_dict(config_dict)


def create_sample_configuration_files():
    """Create sample configuration files for different services."""
    
    # BHub configuration
    bhub_config = {
        "llm_service_type": "bhub",
        "llm_api_key": "${BHUB_API_KEY}",  # Environment variable reference
        "llm_model_id": "mistral-small",
        "llm_timeout": 30,
        "db_service_type": "sqlite",
        "db_path": "tables.db"
    }
    
    # OpenAI configuration
    openai_config = {
        "llm_service_type": "openai",
        "llm_api_key": "${OPENAI_API_KEY}",
        "llm_model_id": "gpt-3.5-turbo",
        "llm_organization": "${OPENAI_ORG_ID}",  # Optional
        "llm_timeout": 30,
        "db_service_type": "sqlite",
        "db_path": "tables.db"
    }
    
    # Azure OpenAI configuration
    azure_config = {
        "llm_service_type": "openai",
        "llm_api_key": "${AZURE_OPENAI_API_KEY}",
        "llm_model_id": "gpt-35-turbo",
        "llm_base_url": "https://your-resource.openai.azure.com/",
        "llm_extra_config": {
            "api_version": "2023-12-01-preview"
        },
        "db_service_type": "sqlite",
        "db_path": "tables.db"
    }
    
    # Custom services configuration
    custom_config = {
        "llm_service_type": "ollama",
        "llm_model_id": "llama2",
        "llm_base_url": "http://localhost:11434",
        "llm_timeout": 60,
        "db_service_type": "postgresql",
        "db_extra_config": {
            "host": "localhost",
            "port": 5432,
            "database": "tables",
            "username": "postgres",
            "password": "${POSTGRES_PASSWORD}"
        }
    }
    
    # Save configuration files
    configs = {
        "bhub_config.json": bhub_config,
        "openai_config.json": openai_config,
        "azure_config.json": azure_config,
        "custom_config.json": custom_config
    }
    
    for filename, config in configs.items():
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"Created {filename}")


def test_service_configuration(config: ServiceConfig):
    """Test a service configuration."""
    try:
        print(f"Testing configuration with LLM: {config.llm_service_type}, DB: {config.db_service_type}")
        
        # Create services
        llm_service, db_service = ServiceFactory.create_services(config)
        
        # Test LLM service
        print("Testing LLM service...")
        if llm_service.is_available():
            response = llm_service.generate_completion("Hello, world!", max_tokens=10)
            if response.success:
                print(f"✓ LLM service working: {response.content[:50]}...")
            else:
                print(f"✗ LLM service error: {response.error}")
        else:
            print("✗ LLM service not available")
        
        # Test database service
        print("Testing database service...")
        if db_service.is_available():
            summary = db_service.get_database_summary()
            print(f"✓ Database service working: {summary}")
        else:
            print("✗ Database service not available")
        
        print("Configuration test completed.\n")
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}\n")


def main():
    """Main function to demonstrate service configuration."""
    print("Service Configuration Examples")
    print("=" * 40)
    
    # Show available services
    print(f"Available LLM services: {ServiceFactory.get_available_llm_services()}")
    print(f"Available database services: {ServiceFactory.get_available_database_services()}")
    print()
    
    # Create sample configuration files
    print("Creating sample configuration files...")
    create_sample_configuration_files()
    print()
    
    # Test different configurations
    configurations = {
        "BHub + SQLite": example_bhub_configuration(),
        "OpenAI + SQLite": example_openai_configuration(),
        "Azure OpenAI + SQLite": example_azure_openai_configuration(),
    }
    
    for name, config in configurations.items():
        print(f"Testing {name} configuration...")
        test_service_configuration(config)
    
    # Show how to load from file
    if Path("bhub_config.json").exists():
        print("Loading configuration from file...")
        try:
            file_config = create_configuration_from_file("bhub_config.json")
            print(f"Loaded configuration: LLM={file_config.llm_service_type}, DB={file_config.db_service_type}")
        except Exception as e:
            print(f"Error loading configuration from file: {e}")
    
    print("Examples completed!")


if __name__ == "__main__":
    main()