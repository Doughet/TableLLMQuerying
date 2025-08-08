# Table Querying Module - Integration Guide

This comprehensive guide shows how to integrate the Table Querying Module into your project, from simple usage to production deployment.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture Overview](#architecture-overview)
3. [Installation](#installation)
4. [Basic Usage](#basic-usage)
5. [Advanced Configuration](#advanced-configuration)
6. [Custom Components](#custom-components)
7. [Production Deployment](#production-deployment)
8. [API Integration](#api-integration)
9. [Troubleshooting](#troubleshooting)

## Quick Start

### 1. Install the Module

```bash
# Clone the repository
git clone <repository-url>
cd table_querying_module

# Install dependencies
pip install -r requirements.txt

# Install the module in development mode
pip install -e .
```

### 2. Basic Usage

```python
from src.core.context import create_default_context
from src.components.factories import DocumentProcessorFactory
from pathlib import Path

# Create processing context
context = create_default_context()

# Create document processor
processor_factory = DocumentProcessorFactory(context)
processor = processor_factory.create_document_processor()

# Process an HTML file
result = processor.process_file(Path("document.html"))

if result.success:
    print(f"Processed {result.table_count} tables successfully")
    for description in result.descriptions:
        print(f"Table {description.table_id}: {description.content}")
else:
    print(f"Processing failed: {result.error_message}")
```

### 3. Query the Database

```python
from src.components.factories import QueryProcessorFactory
from src.core.types import Query

# Create query processor
query_factory = QueryProcessorFactory(context)
query_processor = query_factory.create_query_processor()

# Execute a natural language query
query = Query(content="Show me all tables with more than 10 rows")
result = query_processor.process_query(query)

if result.success:
    print(f"Found {result.row_count} results")
    for row in result.data:
        print(row)
```

## Architecture Overview

The system is built with a highly modular architecture:

```
┌─────────────────────────────────────────────────────────────────┐
│                    CORE ABSTRACTIONS                            │
├─────────────────────────────────────────────────────────────────┤
│  Interfaces  │  Types  │  Exceptions  │  Registry  │  Context   │
└─────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────┐
│                     COMPONENTS                                  │
├─────────────────────────────────────────────────────────────────┤
│  Factories  │  Adapters  │  Implementations  │  Plugins        │
└─────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────┐
│                 LEGACY SERVICES                                 │
├─────────────────────────────────────────────────────────────────┤
│  LLM Services  │  Database Services  │  Processing Pipeline    │
└─────────────────────────────────────────────────────────────────┘
```

### Key Concepts

- **Interfaces**: Define contracts for all components
- **Context**: Manages dependency injection and configuration
- **Registry**: Central registry for component implementations
- **Factories**: Create configured component instances
- **Adapters**: Bridge legacy services with new interfaces

## Installation

### Requirements

- Python 3.8 or higher
- Required packages (see `requirements.txt`)

### Development Installation

```bash
# Clone the repository
git clone <repository-url>
cd table_querying_module

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt
```

### Production Installation

```bash
# Install as a package
pip install git+<repository-url>

# Or from source
python setup.py install
```

## Basic Usage

### Document Processing

```python
from src.core.context import ProcessingContext, create_default_context
from src.components.factories import DocumentProcessorFactory
from src.core.types import Document, DocumentFormat
from pathlib import Path

# Method 1: Process from file
context = create_default_context()
factory = DocumentProcessorFactory(context)
processor = factory.create_document_processor()

result = processor.process_file(Path("document.html"))

# Method 2: Process from content
document = Document(
    content="<html><body><table>...</table></body></html>",
    format=DocumentFormat.HTML,
    source_path=Path("document.html")
)

result = processor.process_document(document)

# Check results
if result.success:
    print(f"✓ Processed {result.table_count} tables")
    print(f"✓ Generated {len(result.descriptions)} descriptions")
    
    for desc in result.descriptions:
        print(f"Table {desc.table_id}: {desc.summary}")
else:
    print(f"✗ Processing failed: {result.error_message}")
```

### Querying Data

```python
from src.components.factories import QueryProcessorFactory, ChatInterfaceFactory
from src.core.types import Query

# Create query processor
query_factory = QueryProcessorFactory(context)
processor = query_factory.create_query_processor()

# Execute queries
queries = [
    "Show all tables",
    "Find tables with more than 5 columns", 
    "What tables contain player data?",
    "Get average values from numeric columns"
]

for query_text in queries:
    query = Query(content=query_text)
    result = processor.process_query(query)
    
    if result.success:
        print(f"Query: {query_text}")
        print(f"Results: {result.row_count} rows")
        for row in result.data[:3]:  # Show first 3 results
            print(f"  {row}")
        print()
```

### Chat Interface

```python
from src.components.factories import ChatInterfaceFactory

# Create chat interface
chat_factory = ChatInterfaceFactory(context)
chat = chat_factory.create_chat_interface()

# Interactive chat
while True:
    user_input = input("Ask about your tables: ")
    if user_input.lower() in ['quit', 'exit']:
        break
    
    response = chat.process_message(user_input)
    
    if response.success:
        print(f"Assistant: {response.content}")
        
        if response.query_result and response.query_result.data:
            print("Data found:")
            for row in response.query_result.data[:5]:
                print(f"  {row}")
    else:
        print(f"Error: {response.error_message}")
```

## Advanced Configuration

### Configuration Management

```python
from src.production.config import ProductionConfig, load_production_config
from src.core.context import ProcessingContext

# Method 1: Programmatic configuration
config = ProductionConfig()
config.llm.provider = "openai"
config.llm.api_key = "sk-..."
config.llm.model_id = "gpt-3.5-turbo"
config.database.type = "postgresql"
config.database.host = "localhost"
config.database.database = "my_tables"

# Method 2: Load from file
config = load_production_config(Path("config.json"))

# Method 3: Environment variables
import os
os.environ["LLM_PROVIDER"] = "openai"
os.environ["LLM_API_KEY"] = "sk-..."
os.environ["DB_TYPE"] = "postgresql"

config = load_production_config(use_env=True)

# Create context with custom configuration
system_config = config.to_system_config()
context = ProcessingContext(config=system_config)
```

### Service Configuration

```python
from src.components.factories import LLMClientFactory, DatabaseClientFactory

# Configure LLM service
llm_factory = LLMClientFactory(context)

# OpenAI
openai_client = llm_factory.create_llm_client(
    provider="openai",
    model_id="gpt-3.5-turbo",
    api_key="sk-...",
    config={"temperature": 0.1, "max_tokens": 1000}
)

# Azure OpenAI  
azure_client = llm_factory.create_llm_client(
    provider="openai",
    model_id="gpt-35-turbo",
    api_key="your-azure-key",
    config={
        "base_url": "https://your-resource.openai.azure.com/",
        "api_version": "2023-12-01-preview"
    }
)

# Multi-provider with fallback
multi_client = llm_factory.create_multi_provider_client([
    {"provider": "openai", "model_id": "gpt-3.5-turbo", "api_key": "sk-..."},
    {"provider": "bhub", "model_id": "mistral-small", "api_key": "bhub-key"}
], fallback_strategy="round_robin")

# Configure database
db_factory = DatabaseClientFactory(context)

# SQLite
sqlite_client = db_factory.create_sqlite_client(Path("tables.db"))

# PostgreSQL
postgres_client = db_factory.create_postgresql_client(
    host="localhost",
    database="tables",
    username="user",
    password="password",
    port=5432,
    config={"pool_size": 20}
)
```

## Custom Components

### Creating Custom LLM Client

```python
from src.core.interfaces import LLMClient
from src.core.types import Schema, Description, Query, QueryResult
from src.core.registry import register_component

class MyCustomLLMClient(LLMClient):
    def __init__(self, api_endpoint: str, api_key: str, **kwargs):
        self.api_endpoint = api_endpoint
        self.api_key = api_key
        self.config = kwargs
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        # Your implementation
        response = self._call_api(prompt, **kwargs)
        return response["text"]
    
    def generate_description(self, schema: Schema, context: str = None) -> Description:
        prompt = f"Describe this table: {schema.to_dict()}"
        if context:
            prompt += f" Context: {context}"
        
        text = self.generate_text(prompt)
        
        return Description(
            table_id=schema.table_id,
            content=text,
            generated_by="MyCustomLLMClient"
        )
    
    def is_available(self) -> bool:
        try:
            self._call_api("test", max_tokens=1)
            return True
        except:
            return False
    
    def _call_api(self, prompt: str, **kwargs):
        # Your API call implementation
        pass

# Register your custom client
register_component("llm_client", MyCustomLLMClient)

# Use it
from src.core.context import get_global_context
context = get_global_context()
context.configure_component("llm_client", {
    "api_endpoint": "https://api.example.com",
    "api_key": "your-key"
})

client = context.get_component("llm_client")
```

### Creating Custom Database Client

```python
from src.core.interfaces import DatabaseClient
from src.core.types import Schema, QueryResult, ValidationResult

class MyDatabaseClient(DatabaseClient):
    def __init__(self, connection_string: str, **kwargs):
        self.connection_string = connection_string
        self.config = kwargs
    
    def store_processing_result(self, result) -> bool:
        # Store tables in your database
        for table, schema, description in zip(result.tables, result.schemas, result.descriptions):
            success = self._store_table(schema, description)
            if not success:
                return False
        return True
    
    def get_table_by_id(self, table_id: str) -> Optional[Schema]:
        # Retrieve table schema
        pass
    
    def execute_query(self, query: Query) -> QueryResult:
        # Execute query against your database
        pass
    
    def health_check(self) -> bool:
        # Check database connectivity
        pass
    
    # Implement other required methods...

# Register and use
register_component("database_client", MyDatabaseClient)
```

### Plugin Architecture

Create a plugin file `my_plugin.py`:

```python
# my_plugin.py
from src.core.registry import ComponentRegistry
from src.core.interfaces import LLMClient

class MyPluginLLMClient(LLMClient):
    # Implementation...
    pass

def register_plugin(registry: ComponentRegistry) -> dict:
    """Plugin registration function."""
    registry.register_component("llm_client", MyPluginLLMClient)
    
    return {
        "name": "My Custom LLM Plugin",
        "version": "1.0.0",
        "components": ["llm_client"]
    }
```

Load plugin:

```python
from src.components.factories import PluginFactory
from pathlib import Path

factory = PluginFactory(context)
component = factory.load_component_plugin(
    Path("my_plugin.py"),
    "llm_client",
    {"api_key": "your-key"}
)
```

## Production Deployment

### Configuration File

Create `production_config.json`:

```json
{
  "environment": "production",
  "debug": false,
  
  "database": {
    "type": "postgresql",
    "host": "db.example.com",
    "port": 5432,
    "database": "table_querying_prod",
    "username": "${DB_USERNAME}",
    "password": "${DB_PASSWORD}",
    "pool_size": 20,
    "ssl_mode": "require"
  },
  
  "llm": {
    "provider": "openai",
    "model_id": "gpt-3.5-turbo",
    "api_key": "${OPENAI_API_KEY}",
    "max_tokens": 1000,
    "timeout": 30,
    "max_retries": 3
  },
  
  "security": {
    "enable_authentication": true,
    "jwt_secret_key": "${JWT_SECRET}",
    "allowed_origins": ["https://yourdomain.com"],
    "enable_https_only": true
  },
  
  "logging": {
    "level": "INFO",
    "log_file_path": "/var/log/table_querying/app.log",
    "enable_structured_logging": true
  },
  
  "monitoring": {
    "enable_metrics": true,
    "enable_health_checks": true
  }
}
```

### Deployment Script

```python
from src.production.config import load_production_config
from src.production.deployment import DeploymentManager
from pathlib import Path

# Load configuration
config = load_production_config(Path("production_config.json"))

# Deploy system
manager = DeploymentManager(config)
success = manager.deploy(validate_first=True)

if success:
    print("✓ Deployment successful")
    
    # Check system health
    health = manager.health_check()
    print(f"System status: {health['status']}")
else:
    print("✗ Deployment failed")
```

### Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN pip install -e .

EXPOSE 8000 8001

CMD ["python", "-m", "src.api.main"]
```

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  table-querying:
    build: .
    ports:
      - "8000:8000"
      - "8001:8001"
    environment:
      - ENVIRONMENT=production
      - DB_TYPE=postgresql
      - DB_HOST=postgres
      - DB_USERNAME=postgres
      - DB_PASSWORD=password
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - postgres
    volumes:
      - ./logs:/var/log/table_querying

  postgres:
    image: postgres:13
    environment:
      - POSTGRES_DB=table_querying
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

Deploy with:

```bash
docker-compose up -d
```

### System Validation

```python
from src.production.deployment import SystemValidator

# Validate before deployment
validator = SystemValidator(config)
result = validator.validate_all()

if result.valid:
    print("✓ All validation checks passed")
else:
    print("✗ Validation failed:")
    for error in result.errors:
        print(f"  - {error}")
    
    print("Warnings:")
    for warning in result.warnings:
        print(f"  - {warning}")
```

## API Integration

### REST API

Create a FastAPI service:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.core.context import create_production_context
from src.components.factories import DocumentProcessorFactory, QueryProcessorFactory

app = FastAPI(title="Table Querying API")
context = create_production_context()

class ProcessRequest(BaseModel):
    html_content: str
    context_hint: str = ""

class QueryRequest(BaseModel):
    query: str

@app.post("/process")
async def process_document(request: ProcessRequest):
    try:
        processor_factory = DocumentProcessorFactory(context)
        processor = processor_factory.create_document_processor()
        
        document = Document(content=request.html_content, format=DocumentFormat.HTML)
        result = processor.process_document(document)
        
        if result.success:
            return {
                "success": True,
                "tables_processed": result.table_count,
                "descriptions": [desc.to_dict() for desc in result.descriptions]
            }
        else:
            raise HTTPException(status_code=400, detail=result.error_message)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def execute_query(request: QueryRequest):
    try:
        query_factory = QueryProcessorFactory(context)
        processor = query_factory.create_query_processor()
        
        query = Query(content=request.query)
        result = processor.process_query(query)
        
        if result.success:
            return {
                "success": True,
                "data": result.data,
                "row_count": result.row_count
            }
        else:
            raise HTTPException(status_code=400, detail=result.error_message)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    from src.production.deployment import DeploymentManager
    manager = DeploymentManager(context.config)
    return manager.health_check()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Client Integration

```python
import requests

class TableQueryingClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def process_document(self, html_content: str, context_hint: str = "") -> dict:
        response = requests.post(
            f"{self.base_url}/process",
            json={"html_content": html_content, "context_hint": context_hint}
        )
        response.raise_for_status()
        return response.json()
    
    def query(self, query: str) -> dict:
        response = requests.post(
            f"{self.base_url}/query",
            json={"query": query}
        )
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> dict:
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

# Usage
client = TableQueryingClient()

# Process document
with open("document.html", "r") as f:
    html_content = f.read()

result = client.process_document(html_content)
print(f"Processed {result['tables_processed']} tables")

# Query data
result = client.query("Show me all tables with more than 5 rows")
print(f"Found {result['row_count']} results")
```

## Troubleshooting

### Common Issues

#### 1. Import Errors

**Problem**: `ModuleNotFoundError: No module named 'src'`

**Solution**:
```bash
# Install in development mode
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### 2. Database Connection Issues

**Problem**: Database connection fails

**Solutions**:
```python
# Check database configuration
config = load_production_config()
print(config.database.get_connection_params())

# Test connection manually
from src.components.factories import DatabaseClientFactory
client = factory.create_sqlite_client(Path("test.db"))
print(client.health_check())
```

#### 3. LLM Service Issues

**Problem**: LLM API calls fail

**Solutions**:
```python
# Check API key and configuration
from src.components.factories import LLMClientFactory
client = factory.create_llm_client(
    provider="openai",
    model_id="gpt-3.5-turbo", 
    api_key="sk-..."
)
print(client.is_available())

# Test with simple request
text = client.generate_text("Hello world", max_tokens=10)
print(text)
```

#### 4. Component Registration Issues

**Problem**: Component not found

**Solutions**:
```python
# Check registered components
from src.core.registry import get_global_registry
registry = get_global_registry()
print(registry.list_components())

# Register component manually
from src.components.adapters import create_llm_adapter
from src.services.implementations.bhub_llm_service import BHubLLMService

llm_service = BHubLLMService(api_key="your-key")
llm_client = create_llm_adapter(llm_service)
registry.register_component("llm_client", type(llm_client))
```

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or use structured logging
from src.production.logging import setup_logging
from src.production.config import LoggingConfig

log_config = LoggingConfig(level="DEBUG", enable_structured_logging=True)
setup_logging(log_config)
```

### Performance Tuning

```python
# Configure processing limits
from src.production.config import ProcessingConfig

processing_config = ProcessingConfig(
    max_concurrent_documents=10,
    document_timeout_seconds=600,
    enable_table_caching=True,
    batch_size=20
)

# Monitor performance
from src.production.monitoring import MetricsCollector

metrics = MetricsCollector()
metrics.record_processing_time("document_processing", 15.2)
```

### Health Monitoring

```python
from src.production.deployment import DeploymentManager

manager = DeploymentManager(config)

# Check system health
health = manager.health_check()
if health["status"] != "healthy":
    print("System issues detected:")
    for check, status in health["checks"].items():
        if status["status"] != "healthy":
            print(f"  {check}: {status.get('error', 'unhealthy')}")

# Get system information
info = manager.get_system_info()
print(f"Version: {info['version']}")
print(f"Environment: {info['environment']}")
```

## Migration from Legacy System

If you have an existing table processing system:

### 1. Gradual Migration

```python
# Keep using your existing services
from your_existing_system import YourLLMService, YourDatabaseService

# Create adapters
from src.components.adapters import create_llm_adapter, create_database_adapter

llm_client = create_llm_adapter(YourLLMService())
db_client = create_database_adapter(YourDatabaseService())

# Register with new system
from src.core.registry import register_component

register_component("llm_client", type(llm_client))
register_component("database_client", type(db_client))
```

### 2. Component-by-Component Migration

```python
# Phase 1: Use new interfaces with legacy implementations
context = create_default_context()
factories = create_default_factories(context)

# Phase 2: Migrate LLM service
new_llm = factories["llm_client"].create_llm_client("openai", "gpt-3.5-turbo")
context.registry.register_component("llm_client", type(new_llm))

# Phase 3: Migrate database
new_db = factories["database_client"].create_postgresql_client(...)
context.registry.register_component("database_client", type(new_db))
```

---

## Summary

The Table Querying Module provides a highly flexible, modular system for processing HTML tables and enabling natural language queries. Key benefits:

- **Modular Architecture**: Easy component swapping
- **Production Ready**: Comprehensive configuration, monitoring, and deployment tools
- **Extensible**: Plugin system and custom component support
- **Multiple Interfaces**: CLI, API, and programmatic access
- **Legacy Compatible**: Adapters for existing systems

For additional help, check the examples in the repository or create an issue on GitHub.