# Service Architecture Guide

This guide explains how to use and extend the service architecture for plugging in custom LLM and Database services.

## Overview

The system uses an abstract service interface pattern that allows you to easily plug in different implementations for:

- **LLM Services**: Different AI/ML providers (BHub, OpenAI, Azure OpenAI, Ollama, etc.)
- **Database Services**: Different database backends (SQLite, PostgreSQL, MongoDB, etc.)

## Built-in Services

### LLM Services

1. **BHub LLM Service** (`BHubLLMService`)
   - Default service for BHub API
   - Supports all BHub models (mistral-small, etc.)
   - Endpoint: `https://api.olympia.bhub.cloud/v1`

2. **OpenAI LLM Service** (`OpenAILLMService`)
   - Compatible with OpenAI API and Azure OpenAI
   - Supports GPT models (gpt-3.5-turbo, gpt-4, etc.)
   - Configurable base URL for different providers

### Database Services

1. **SQLite Database Service** (`SQLiteDatabaseService`)
   - Default database service
   - File-based, zero-configuration
   - Full-text search and JSON support

## Quick Start

### Using Built-in Services

```python
from src.services.service_factory import ServiceFactory, ServiceConfig

# Create configuration
config = ServiceConfig(
    llm_service_type="bhub",
    llm_api_key="your-api-key",
    llm_model_id="mistral-small",
    db_service_type="sqlite",
    db_path="tables.db"
)

# Create services
llm_service, db_service = ServiceFactory.create_services(config)

# Use services
response = llm_service.generate_completion("Hello, world!")
summary = db_service.get_database_summary()
```

### Using Configuration Files

Create a JSON configuration file:

```json
{
  "llm_service_type": "openai",
  "llm_api_key": "${OPENAI_API_KEY}",
  "llm_model_id": "gpt-3.5-turbo",
  "db_service_type": "sqlite",
  "db_path": "tables.db"
}
```

Load and use:

```python
config = ServiceConfig.from_dict(json.load(open("config.json")))
llm_service, db_service = ServiceFactory.create_services(config)
```

## Creating Custom Services

### Custom LLM Service

1. **Inherit from `LLMService`**:

```python
from src.services.llm_service import LLMService, LLMResponse

class MyCustomLLMService(LLMService):
    def __init__(self, api_key: str, model_id: str = "default", **kwargs):
        super().__init__(api_key=api_key, model_id=model_id, **kwargs)
        self.api_key = api_key
        self.model_id = model_id
    
    def generate_completion(self, prompt: str, **kwargs) -> LLMResponse:
        # Your implementation here
        try:
            # Make API call to your service
            result = your_api_call(prompt, **kwargs)
            return LLMResponse(
                content=result,
                success=True,
                metadata={"model": self.model_id}
            )
        except Exception as e:
            return LLMResponse(
                content="",
                success=False,
                error=str(e)
            )
    
    def generate_chat_completion(self, messages, **kwargs) -> LLMResponse:
        # Implementation for chat-style completions
        pass
    
    def is_available(self) -> bool:
        # Check if your service is reachable
        return True
```

2. **Register your service**:

```python
from src.services.service_factory import ServiceFactory

ServiceFactory.register_llm_service("mycustom", MyCustomLLMService)

# Use it
config = ServiceConfig(llm_service_type="mycustom", ...)
```

### Custom Database Service

1. **Inherit from `DatabaseService`**:

```python
from src.services.database_service import DatabaseService, TableMetadata, QueryResult

class MyCustomDatabaseService(DatabaseService):
    def __init__(self, connection_string: str, **kwargs):
        super().__init__(connection_string=connection_string, **kwargs)
        self.connection_string = connection_string
    
    def initialize(self) -> bool:
        # Create necessary tables/collections
        return True
    
    def store_table(self, table_data: Dict[str, Any], session_id: str) -> bool:
        # Store table data in your database
        return True
    
    def get_all_tables(self) -> List[TableMetadata]:
        # Retrieve all table metadata
        return []
    
    def execute_query(self, query: str, parameters=None) -> QueryResult:
        # Execute queries against your database
        return QueryResult(success=True, data=[])
    
    # Implement other required methods...
```

2. **Register your service**:

```python
ServiceFactory.register_database_service("mycustom", MyCustomDatabaseService)
```

## Service Configuration

### Configuration Options

```python
@dataclass
class ServiceConfig:
    # LLM Service Configuration
    llm_service_type: str = "bhub"          # Service type
    llm_api_key: str = ""                   # API key
    llm_model_id: str = "mistral-small"     # Model identifier
    llm_base_url: str = ""                  # Custom base URL
    llm_organization: str = None            # Organization (OpenAI)
    llm_timeout: int = 30                   # Request timeout
    llm_max_retries: int = 3               # Retry attempts
    llm_extra_config: Dict = {}            # Additional config
    
    # Database Service Configuration  
    db_service_type: str = "sqlite"         # Service type
    db_path: str = "tables.db"             # Database path/connection
    db_timeout: float = 30.0               # Connection timeout
    db_auto_commit: bool = True            # Auto-commit transactions
    db_extra_config: Dict = {}             # Additional config
```

### Environment Variable Support

Configuration values can reference environment variables:

```json
{
  "llm_api_key": "${OPENAI_API_KEY}",
  "db_path": "${TABLE_DB_PATH:/default/path/tables.db}"
}
```

## Examples

### Example 1: Using Ollama (Local LLM)

```python
# Custom Ollama service (see examples/custom_llm_service_example.py)
from examples.custom_llm_service_example import OllamaLLMService

# Register
ServiceFactory.register_llm_service("ollama", OllamaLLMService)

# Configure
config = ServiceConfig(
    llm_service_type="ollama",
    llm_model_id="llama2",
    llm_base_url="http://localhost:11434",
    llm_timeout=60,
    db_service_type="sqlite",
    db_path="tables.db"
)

# Use
llm_service, db_service = ServiceFactory.create_services(config)
```

### Example 2: Using PostgreSQL Database

```python
# Custom PostgreSQL service (see examples/custom_database_service_example.py)
from examples.custom_database_service_example import PostgreSQLDatabaseService

# Register
ServiceFactory.register_database_service("postgresql", PostgreSQLDatabaseService)

# Configure
config = ServiceConfig(
    llm_service_type="openai",
    llm_api_key="sk-...",
    db_service_type="postgresql",
    db_extra_config={
        "host": "localhost",
        "port": 5432,
        "database": "tables",
        "username": "postgres",
        "password": "password"
    }
)
```

### Example 3: Azure OpenAI

```python
config = ServiceConfig(
    llm_service_type="openai",
    llm_api_key="your-azure-key",
    llm_model_id="gpt-35-turbo",  # Azure deployment name
    llm_base_url="https://your-resource.openai.azure.com/",
    llm_extra_config={
        "api_version": "2023-12-01-preview"
    },
    db_service_type="sqlite",
    db_path="tables.db"
)
```

## Integration with Table Processing

### Using Custom Services in Table Processing

```python
from src.table_querying.table_processor import TableProcessor

# Create services with your custom configuration
llm_service, db_service = ServiceFactory.create_services(your_config)

# Create processor with custom services
processor = TableProcessor(
    llm_service=llm_service,
    database_service=db_service,
    # ... other config
)

# Process documents
result = processor.process_document("document.html")
```

### Using Custom Services in Chat Interface

```python
from src.chatting_module.chat_interface import ChatInterface

# Create services
llm_service, db_service = ServiceFactory.create_services(your_config)

# Create chat interface with custom services
chat = ChatInterface(
    llm_service=llm_service,
    database_service=db_service
)

# Use chat
response = chat.chat("Show me all tables with more than 10 rows")
```

## Service Interface Reference

### LLMService Interface

**Required Methods:**
- `generate_completion(prompt, **kwargs) -> LLMResponse`
- `generate_chat_completion(messages, **kwargs) -> LLMResponse`
- `is_available() -> bool`

**Optional Methods:**
- `generate_table_description(schema, context_hint) -> LLMResponse`
- `generate_sql_query(user_query, database_schema) -> LLMResponse`
- `analyze_query_feasibility(user_query, available_tables) -> LLMResponse`

### DatabaseService Interface

**Required Methods:**
- `initialize() -> bool`
- `is_available() -> bool`
- `store_table(table_data, session_id) -> bool`
- `get_table_metadata(table_id) -> Optional[TableMetadata]`
- `get_all_tables() -> List[TableMetadata]`
- `execute_query(query, parameters) -> QueryResult`
- `table_exists(table_id) -> bool`
- `get_database_summary() -> Dict[str, Any]`
- `clear_database() -> bool`

**Session Management:**
- `create_session(source_file) -> str`
- `update_session(session_id, total_tables, successful_tables) -> bool`
- `get_session_info(session_id) -> Optional[Dict[str, Any]]`

## Troubleshooting

### Common Issues

1. **Service Not Found**: Make sure to register custom services before using them
2. **Missing Dependencies**: Install required packages for custom services
3. **Configuration Errors**: Validate configuration with `ServiceConfig.from_dict()`
4. **Connection Issues**: Use `is_available()` to test service connectivity

### Debug Mode

Enable logging to see service operations:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Service Testing

Test your custom services:

```python
# Test LLM service
if llm_service.is_available():
    response = llm_service.generate_completion("test")
    print(f"Success: {response.success}, Content: {response.content}")

# Test database service  
if db_service.is_available():
    summary = db_service.get_database_summary()
    print(f"Database summary: {summary}")
```

## Best Practices

1. **Error Handling**: Always return appropriate success/error responses
2. **Connection Pooling**: Use connection pooling for database services
3. **Timeouts**: Set appropriate timeouts for external services
4. **Logging**: Add comprehensive logging for debugging
5. **Configuration**: Validate configuration in service constructors
6. **Testing**: Test service availability before use
7. **Documentation**: Document custom service configuration requirements

## Migration Guide

### From Direct Service Usage

**Old way:**
```python
from src.table_querying.table_summarizer import TableSummarizer
summarizer = TableSummarizer(api_key="...", model_id="...")
```

**New way:**
```python
from src.services.service_factory import ServiceFactory, ServiceConfig

config = ServiceConfig(llm_api_key="...", llm_model_id="...")
llm_service, _ = ServiceFactory.create_services(config)
# Use llm_service instead of direct summarizer
```

This abstraction provides better testability, configuration management, and extensibility while maintaining the same core functionality.