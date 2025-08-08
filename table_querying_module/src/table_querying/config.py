"""
Configuration module for the Table Querying Module.

This module provides configuration classes and utilities for setting up
the table processing workflow.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TableProcessingConfig:
    """Configuration settings for table processing."""
    
    # LLM Configuration
    api_key: Optional[str] = None
    model_id: str = "gpt-3.5-turbo"
    llm_service_type: str = "openai"
    llm_base_url: Optional[str] = None
    llm_organization: Optional[str] = None
    llm_timeout: int = 30
    llm_max_retries: int = 3
    context_hint: Optional[str] = None
    
    # Database Configuration
    db_path: str = "table_querying.db"
    db_service_type: str = "sqlite"
    db_timeout: float = 30.0
    db_auto_commit: bool = True
    clear_database_on_start: bool = False
    
    # Output Configuration
    save_outputs: bool = True
    output_dir: str = "table_querying_outputs"
    
    # Processing Options
    max_tables_per_document: int = 100
    enable_schema_validation: bool = True
    enable_description_generation: bool = True
    
    def __post_init__(self):
        """Post-initialization processing."""
        # Set API key from environment if not provided
        if not self.api_key:
            self.api_key = os.getenv("YOUR_API_KEY")
        
        # Ensure paths are Path objects
        self.output_dir = str(Path(self.output_dir).resolve())
        self.db_path = str(Path(self.db_path).resolve())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'api_key': self.api_key,
            'model_id': self.model_id,
            'llm_service_type': self.llm_service_type,
            'llm_base_url': self.llm_base_url,
            'llm_organization': self.llm_organization,
            'llm_timeout': self.llm_timeout,
            'llm_max_retries': self.llm_max_retries,
            'context_hint': self.context_hint,
            'db_path': self.db_path,
            'db_service_type': self.db_service_type,
            'db_timeout': self.db_timeout,
            'db_auto_commit': self.db_auto_commit,
            'clear_database_on_start': self.clear_database_on_start,
            'save_outputs': self.save_outputs,
            'output_dir': self.output_dir,
            'max_tables_per_document': self.max_tables_per_document,
            'enable_schema_validation': self.enable_schema_validation,
            'enable_description_generation': self.enable_description_generation
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'TableProcessingConfig':
        """Create configuration from dictionary."""
        return cls(**{k: v for k, v in config_dict.items() if hasattr(cls, k)})
    
    @classmethod
    def from_file(cls, config_file: str) -> 'TableProcessingConfig':
        """Load configuration from JSON file."""
        import json
        import re
        
        config_path = Path(config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # Expand environment variables in string values
        def expand_env_vars(obj):
            if isinstance(obj, str):
                # Replace ${VAR_NAME} with environment variable value
                def replace_var(match):
                    var_name = match.group(1)
                    return os.getenv(var_name, match.group(0))  # Keep original if not found
                return re.sub(r'\$\{([^}]+)\}', replace_var, obj)
            elif isinstance(obj, dict):
                return {key: expand_env_vars(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [expand_env_vars(item) for item in obj]
            else:
                return obj
        
        config_data = expand_env_vars(config_data)
        return cls.from_dict(config_data)
    
    def save_to_file(self, config_file: str):
        """Save configuration to JSON file."""
        import json
        
        config_path = Path(config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)


def create_default_config() -> TableProcessingConfig:
    """Create a default configuration."""
    return TableProcessingConfig()


def create_config_for_minecraft_wiki() -> TableProcessingConfig:
    """Create a configuration optimized for Minecraft Wiki processing."""
    return TableProcessingConfig(
        context_hint="Minecraft Wiki pages containing game data, recipes, items, blocks, and mechanics information",
        output_dir="minecraft_wiki_outputs",
        db_path="minecraft_tables.db",
        save_outputs=True
    )


def create_config_template(output_path: str = "table_processing_config.json"):
    """Create a configuration template file."""
    config = create_default_config()
    config.save_to_file(output_path)
    
    print(f"Configuration template saved to: {output_path}")
    print("Please update the settings as needed:")
    print("- api_key: Your OpenAI API key")
    print("- model_id: LLM model to use (gpt-3.5-turbo, gpt-4, etc.)")
    print("- llm_service_type: LLM provider ('openai' by default)")
    print("- context_hint: Context for better table descriptions")
    print("- db_path: Database file path")
    print("- output_dir: Directory for output files")


# Environment variable mapping
ENV_VAR_MAPPING = {
    'YOUR_API_KEY': 'api_key',
    'TABLE_MODEL_ID': 'model_id',
    'TABLE_DB_PATH': 'db_path',
    'TABLE_OUTPUT_DIR': 'output_dir',
    'TABLE_CONTEXT_HINT': 'context_hint'
}


def load_config_from_env() -> Dict[str, Any]:
    """Load configuration from environment variables."""
    config = {}
    
    for env_var, config_key in ENV_VAR_MAPPING.items():
        value = os.getenv(env_var)
        if value:
            # Convert boolean strings
            if value.lower() in ['true', 'false']:
                value = value.lower() == 'true'
            # Convert numeric strings
            elif value.isdigit():
                value = int(value)
            
            config[config_key] = value
    
    return config