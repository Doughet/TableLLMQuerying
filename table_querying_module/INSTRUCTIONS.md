# Table Querying Module - Complete Instructions

🎯 **A world-class, enterprise-ready system for extracting, processing, and querying HTML tables with maximum modularity and component abstraction.**

---

## 📋 Table of Contents

1. [🚀 Quick Start (30 Seconds)](#-quick-start-30-seconds)
2. [🏗️ Architecture Overview](#️-architecture-overview)
3. [🔄 Component Swapping Guide](#-component-swapping-guide)
4. [🎨 Custom Component Development](#-custom-component-development)
5. [🚀 Production Deployment](#-production-deployment)
6. [📖 Complete Usage Examples](#-complete-usage-examples)
7. [🔧 Configuration Management](#-configuration-management)
8. [🐛 Troubleshooting](#-troubleshooting)
9. [📂 Project Structure](#-project-structure)
10. [🌟 Key Features](#-key-features)

---

## 🚀 Quick Start (30 Seconds)

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd table_querying_module

# Install dependencies
pip install -e .

# Set your API key (choose one)
export LLM_API_KEY="your-api-key"
# or
echo 'LLM_API_KEY="your-api-key"' > .env
```

### Basic Usage
```python
from src.core.context import create_default_context
from src.components.factories import DocumentProcessorFactory

# Create system context
context = create_default_context()

# Process a document
processor = DocumentProcessorFactory(context).create_document_processor()
result = processor.process_file("document.html")

if result.success:
    print(f"✅ Processed {result.table_count} tables successfully!")
    for desc in result.descriptions:
        print(f"📊 {desc.table_id}: {desc.content}")
else:
    print(f"❌ Error: {result.error_message}")
```

### Query Your Data
```python
from src.components.factories import QueryProcessorFactory
from src.core.types import Query

# Create query processor
query_processor = QueryProcessorFactory(context).create_query_processor()

# Ask natural language questions
queries = [
    "Show me all tables",
    "Find tables with more than 5 columns",
    "What tables contain player data?"
]

for q in queries:
    query = Query(content=q)
    result = query_processor.process_query(query)
    
    if result.success:
        print(f"❓ {q}")
        print(f"✅ Found {result.row_count} results")
        print("📋 Sample data:", result.data[:2])  # Show first 2 results
    else:
        print(f"❌ Query failed: {result.error_message}")
```

**🎉 That's it! You're processing tables and querying them with natural language!**

---

## 🏗️ Architecture Overview

This system follows a **layered, component-based architecture** with **dependency injection** and **plugin support**:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                 USER LAYER                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│  CLI Interface  │  REST API  │  Web UI  │  Python Client  │  Custom Apps      │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
┌─────────────────────────────────────────────────────────────────────────────────┐
│                               APPLICATION LAYER                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Document Processor  │  Query Processor  │  Chat Interface  │  Workflow Engine │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
┌─────────────────────────────────────────────────────────────────────────────────┐
│                               COMPONENT LAYER                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Factories  │  Adapters  │  Implementations  │  Plugin System  │  Monitoring   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                CORE LAYER                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Interfaces  │  Types  │  Registry  │  Context  │  Exceptions  │  Validation   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Key Design Principles

1. **🏛️ Interface-First Design** - Every component implements clean interfaces
2. **💉 Dependency Injection** - No hard dependencies, everything is injected
3. **🔄 Component Registry** - Central registry for all implementations
4. **⚙️ Configuration-Driven** - Everything configurable without code changes
5. **🔌 Plugin Architecture** - Dynamic loading of custom components
6. **🚀 Production Ready** - Health checks, monitoring, security built-in

---

## 🔄 Component Swapping Guide

### Change LLM Provider (1 Line!)

```python
from src.production.config import ProductionConfig

config = ProductionConfig()

# Switch from BHub to OpenAI
config.llm.provider = "openai"      # Was "bhub"
config.llm.api_key = "sk-..."
config.llm.model_id = "gpt-3.5-turbo"

# Switch to Azure OpenAI
config.llm.provider = "openai"
config.llm.api_key = "your-azure-key"
config.llm.model_id = "gpt-35-turbo"
config.llm.base_url = "https://your-resource.openai.azure.com/"

# Use multiple providers with fallback
multi_config = {
    "providers": [
        {"provider": "openai", "api_key": "sk-...", "model_id": "gpt-3.5-turbo"},
        {"provider": "bhub", "api_key": "bhub-key", "model_id": "mistral-small"}
    ],
    "fallback_strategy": "round_robin"
}
```

### Change Database (1 Line!)

```python
# Switch from SQLite to PostgreSQL
config.database.type = "postgresql"    # Was "sqlite"
config.database.host = "localhost"
config.database.database = "my_tables"
config.database.username = "postgres"
config.database.password = "password"

# Switch to MongoDB
config.database.type = "mongodb"
config.database.connection_string = "mongodb://localhost:27017/tables"
```

### Environment-Based Switching

```bash
# Development (SQLite + BHub)
export ENVIRONMENT="development"
export DB_TYPE="sqlite"
export LLM_PROVIDER="bhub"
export LLM_API_KEY="your-bhub-key"

# Production (PostgreSQL + OpenAI)
export ENVIRONMENT="production"
export DB_TYPE="postgresql"
export DB_HOST="prod-db.company.com"
export LLM_PROVIDER="openai"
export LLM_API_KEY="sk-..."
```

### Configuration File Switching

**development.json:**
```json
{
  "llm": {"provider": "bhub", "api_key": "${BHUB_API_KEY}"},
  "database": {"type": "sqlite", "database": "dev_tables.db"}
}
```

**production.json:**
```json
{
  "llm": {"provider": "openai", "api_key": "${OPENAI_API_KEY}"},
  "database": {"type": "postgresql", "host": "prod-db.com"}
}
```

**Usage:**
```python
from src.production.config import load_production_config

# Load different configs
dev_config = load_production_config(Path("development.json"))
prod_config = load_production_config(Path("production.json"))
```

---

## 🎨 Custom Component Development

### Create Custom LLM Client

```python
from src.core.interfaces import LLMClient
from src.core.types import Schema, Description
from src.core.registry import register_component

class MyCustomLLMClient(LLMClient):
    """Custom LLM client for your service."""
    
    def __init__(self, api_endpoint: str, api_key: str, **kwargs):
        self.api_endpoint = api_endpoint
        self.api_key = api_key
        self.config = kwargs
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using your LLM service."""
        # Your implementation here
        response = self._call_your_api(prompt, **kwargs)
        return response["generated_text"]
    
    def generate_description(self, schema: Schema, context: str = None) -> Description:
        """Generate table description."""
        prompt = f"Describe this table: {schema.to_dict()}"
        if context:
            prompt += f" Context: {context}"
        
        text = self.generate_text(prompt, max_tokens=300)
        
        return Description(
            table_id=schema.table_id,
            content=text,
            generated_by="MyCustomLLMClient",
            confidence=0.9
        )
    
    def generate_sql(self, natural_query: str, database_schema: dict) -> str:
        """Generate SQL from natural language."""
        prompt = f"Convert to SQL: {natural_query}\nSchema: {database_schema}"
        return self.generate_text(prompt, max_tokens=200)
    
    def analyze_query(self, query: str, available_tables: list) -> dict:
        """Analyze query feasibility."""
        prompt = f"Can this query be answered with these tables?\nQuery: {query}\nTables: {available_tables}"
        response = self.generate_text(prompt, max_tokens=100)
        
        # Parse response or return structured analysis
        return {
            "is_fulfillable": "yes" in response.lower(),
            "confidence": 0.8,
            "reasoning": response
        }
    
    def is_available(self) -> bool:
        """Check if service is available."""
        try:
            self._call_your_api("test", max_tokens=1)
            return True
        except:
            return False
    
    def _call_your_api(self, prompt: str, **kwargs):
        """Your API call implementation."""
        import requests
        
        headers = {"Authorization": f"Bearer {self.api_key}"}
        data = {"prompt": prompt, **kwargs}
        
        response = requests.post(self.api_endpoint, headers=headers, json=data)
        response.raise_for_status()
        return response.json()

# Register your component
register_component("llm_client", MyCustomLLMClient)

# Use immediately
from src.core.context import get_global_context
context = get_global_context()
context.configure_component("llm_client", {
    "api_endpoint": "https://api.yourservice.com/generate",
    "api_key": "your-api-key"
})

# Your custom client is now used throughout the system!
client = context.get_component("llm_client")
```

### Create Custom Database Client

```python
from src.core.interfaces import DatabaseClient
from src.core.types import Schema, QueryResult, Query
from typing import Optional, List, Dict, Any

class MyDatabaseClient(DatabaseClient):
    """Custom database client for your database."""
    
    def __init__(self, connection_string: str, **kwargs):
        self.connection_string = connection_string
        self.config = kwargs
        self._connection = self._connect()
    
    def store_processing_result(self, result) -> bool:
        """Store processing results in your database."""
        try:
            for table, schema, description in zip(result.tables, result.schemas, result.descriptions):
                # Store in your database format
                success = self._store_table_data({
                    "table_id": table.table_id,
                    "source": result.document.filename,
                    "schema": schema.to_dict(),
                    "description": description.content,
                    "metadata": result.metadata
                })
                if not success:
                    return False
            return True
        except Exception as e:
            print(f"Storage error: {e}")
            return False
    
    def get_table_by_id(self, table_id: str) -> Optional[Schema]:
        """Retrieve table schema by ID."""
        # Query your database
        data = self._query_database(f"SELECT * FROM tables WHERE id = '{table_id}'")
        if data:
            return self._convert_to_schema(data[0])
        return None
    
    def search_tables(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[Schema]:
        """Search tables matching criteria."""
        # Implement your search logic
        search_query = f"SELECT * FROM tables WHERE description LIKE '%{query}%'"
        results = self._query_database(search_query)
        return [self._convert_to_schema(row) for row in results]
    
    def execute_query(self, query: Query) -> QueryResult:
        """Execute a query against your database."""
        try:
            start_time = time.time()
            
            # Execute SQL query
            results = self._query_database(query.content)
            
            execution_time = time.time() - start_time
            
            return QueryResult(
                success=True,
                data=results,
                query=query,
                execution_time=execution_time
            )
        except Exception as e:
            return QueryResult(
                success=False,
                data=[],
                query=query,
                error_message=str(e)
            )
    
    def get_database_summary(self) -> Dict[str, Any]:
        """Get database statistics."""
        return {
            "total_tables": self._count_tables(),
            "database_type": "MyCustomDB",
            "connection": self.connection_string
        }
    
    def health_check(self) -> bool:
        """Check database health."""
        try:
            self._query_database("SELECT 1")
            return True
        except:
            return False
    
    # Your database-specific methods
    def _connect(self):
        """Connect to your database."""
        # Your connection logic
        pass
    
    def _query_database(self, sql: str):
        """Execute SQL against your database."""
        # Your query logic
        pass
    
    def _store_table_data(self, data: dict) -> bool:
        """Store data in your database."""
        # Your storage logic
        pass
    
    def _convert_to_schema(self, db_row) -> Schema:
        """Convert database row to Schema object."""
        # Your conversion logic
        pass

# Register and use
register_component("database_client", MyDatabaseClient)
```

### Plugin-Based Components

Create a plugin file `my_plugin.py`:

```python
"""My Custom Plugin for Table Querying Module"""

from src.core.registry import ComponentRegistry
from src.core.interfaces import LLMClient, DatabaseClient

class MyPluginLLMClient(LLMClient):
    """Plugin LLM implementation."""
    # Your implementation...
    pass

class MyPluginDatabaseClient(DatabaseClient):
    """Plugin database implementation."""
    # Your implementation...
    pass

def register_plugin(registry: ComponentRegistry) -> dict:
    """Plugin registration function called by the system."""
    
    # Register your components
    registry.register_component("llm_client", MyPluginLLMClient)
    registry.register_component("database_client", MyPluginDatabaseClient)
    
    # Return plugin metadata
    return {
        "name": "My Custom Plugin",
        "version": "1.0.0",
        "description": "Custom LLM and Database implementations",
        "components": ["llm_client", "database_client"],
        "author": "Your Name"
    }
```

Load your plugin:

```python
from src.components.factories import PluginFactory
from pathlib import Path

factory = PluginFactory(context)
component = factory.load_component_plugin(
    Path("my_plugin.py"),
    "llm_client",
    {"api_key": "your-key", "endpoint": "your-endpoint"}
)
```

---

## 🚀 Production Deployment

### Configuration-Based Deployment

**1. Create Production Configuration (`production.json`):**

```json
{
  "environment": "production",
  "debug": false,
  "version": "1.0.0",
  
  "database": {
    "type": "postgresql",
    "host": "prod-db.company.com",
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
    "enable_https_only": true,
    "rate_limit_requests": 1000,
    "rate_limit_window": 3600
  },
  
  "logging": {
    "level": "INFO",
    "log_file_path": "/var/log/table_querying/app.log",
    "enable_structured_logging": true,
    "max_file_size_mb": 100,
    "backup_count": 5
  },
  
  "monitoring": {
    "enable_metrics": true,
    "metrics_port": 8001,
    "enable_health_checks": true,
    "health_check_interval": 60,
    "prometheus_endpoint": "/metrics"
  },
  
  "processing": {
    "max_concurrent_documents": 10,
    "document_timeout_seconds": 300,
    "enable_table_caching": true,
    "cache_ttl_seconds": 3600,
    "batch_size": 20
  }
}
```

**2. Deploy with Validation:**

```python
from src.production.config import load_production_config
from src.production.deployment import DeploymentManager, SystemValidator

# Load configuration
config = load_production_config(Path("production.json"))

# Validate system before deployment
print("🔍 Validating system...")
validator = SystemValidator(config)
validation_result = validator.validate_all()

if validation_result.valid:
    print(f"✅ All {validation_result.checks_passed}/{validation_result.checks_total} validation checks passed!")
    
    # Deploy system
    print("🚀 Deploying system...")
    manager = DeploymentManager(config)
    success = manager.deploy(validate_first=True)
    
    if success:
        print("✅ Deployment successful!")
        
        # Check system health
        health = manager.health_check()
        print(f"🏥 System status: {health['status']}")
        
        if health['status'] == 'healthy':
            print("🎉 System is ready for production!")
        else:
            print("⚠️  System has health issues:")
            for check, status in health['checks'].items():
                if status['status'] != 'healthy':
                    print(f"  ❌ {check}: {status.get('error', 'unhealthy')}")
    else:
        print("❌ Deployment failed!")
else:
    print("❌ Validation failed:")
    for error in validation_result.errors:
        print(f"  • {error}")
    
    if validation_result.warnings:
        print("⚠️  Warnings:")
        for warning in validation_result.warnings:
            print(f"  • {warning}")
```

**3. Command-Line Deployment:**

```bash
# Validate system
tq-validate --config production.json

# Deploy system  
tq-deploy --config production.json --validate

# Check system health
curl http://localhost:8000/health
```

### Docker Deployment

**Dockerfile:**
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy source code
COPY . .
RUN pip install -e .

# Create directories
RUN mkdir -p /var/log/table_querying

# Expose ports
EXPOSE 8000 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["python", "-m", "src.api.main"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  table-querying:
    build: .
    ports:
      - "8000:8000"    # Main API
      - "8001:8001"    # Metrics
    environment:
      - ENVIRONMENT=production
      - DB_TYPE=postgresql
      - DB_HOST=postgres
      - DB_USERNAME=postgres
      - DB_PASSWORD=secure_password
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      - postgres
      - redis
    volumes:
      - ./logs:/var/log/table_querying
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:
    image: postgres:13
    environment:
      - POSTGRES_DB=table_querying
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - table-querying
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

**Deploy:**
```bash
# Set environment variables
export OPENAI_API_KEY="sk-..."
export JWT_SECRET="your-secret-key"

# Deploy
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs table-querying
```

### Kubernetes Deployment

**k8s-deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: table-querying
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: table-querying
  template:
    metadata:
      labels:
        app: table-querying
    spec:
      containers:
      - name: table-querying
        image: your-registry/table-querying:latest
        ports:
        - containerPort: 8000
        - containerPort: 8001
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: DB_HOST
          value: "postgres-service"
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: openai-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10

---
apiVersion: v1
kind: Service
metadata:
  name: table-querying-service
  namespace: production
spec:
  selector:
    app: table-querying
  ports:
  - name: api
    port: 8000
    targetPort: 8000
  - name: metrics
    port: 8001
    targetPort: 8001
  type: LoadBalancer
```

---

## 📖 Complete Usage Examples

### Example 1: Basic Document Processing

```python
#!/usr/bin/env python3
"""
Basic document processing example.
Process HTML files and generate table descriptions.
"""

from pathlib import Path
from src.core.context import create_default_context
from src.components.factories import DocumentProcessorFactory
from src.core.types import Document, DocumentFormat

def main():
    # Setup
    context = create_default_context()
    processor_factory = DocumentProcessorFactory(context)
    
    # Create processor with default components
    processor = processor_factory.create_document_processor()
    
    # Process files
    html_files = [
        "sample_document.html",
        "data/tables.html",
        "wiki_page.html"
    ]
    
    for file_path in html_files:
        if Path(file_path).exists():
            print(f"\n📄 Processing {file_path}...")
            
            try:
                result = processor.process_file(Path(file_path))
                
                if result.success:
                    print(f"✅ Success! Processed {result.table_count} tables in {result.processing_time:.2f}s")
                    
                    for i, desc in enumerate(result.descriptions, 1):
                        print(f"\n📊 Table {i} ({desc.table_id}):")
                        print(f"   {desc.content[:200]}...")
                        if desc.key_insights:
                            print(f"   🔍 Insights: {', '.join(desc.key_insights[:3])}")
                else:
                    print(f"❌ Failed: {result.error_message}")
                    
            except Exception as e:
                print(f"💥 Error processing {file_path}: {e}")
        else:
            print(f"⚠️  File not found: {file_path}")

if __name__ == "__main__":
    main()
```

### Example 2: Interactive Query System

```python
#!/usr/bin/env python3
"""
Interactive query system example.
Ask natural language questions about your processed tables.
"""

from src.core.context import create_default_context
from src.components.factories import QueryProcessorFactory, ChatInterfaceFactory
from src.core.types import Query

def main():
    print("🤖 Table Querying Interactive System")
    print("=" * 50)
    
    # Setup
    context = create_default_context()
    
    # Create chat interface (includes query processor)
    chat_factory = ChatInterfaceFactory(context)
    chat = chat_factory.create_chat_interface()
    
    # Start interactive session
    session_id = chat.start_session()
    print(f"📱 Started session: {session_id}")
    print("💡 Try asking: 'Show me all tables', 'Find tables with player data', 'quit'")
    
    while True:
        try:
            # Get user input
            user_input = input("\n🔍 Ask about your tables: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                break
            
            # Special commands
            if user_input.lower() == 'help':
                show_help()
                continue
            
            if user_input.lower() == 'summary':
                show_database_summary(context)
                continue
            
            # Process message
            print("🤔 Thinking...")
            response = chat.process_message(user_input)
            
            if response.success:
                print(f"🤖 {response.content}")
                
                # Show data if available
                if response.query_result and response.query_result.data:
                    print(f"\n📊 Found {response.query_result.row_count} results:")
                    
                    # Display first few results
                    for i, row in enumerate(response.query_result.data[:5], 1):
                        print(f"   {i}. {row}")
                    
                    if response.query_result.row_count > 5:
                        print(f"   ... and {response.query_result.row_count - 5} more results")
                
                # Show suggestions
                if response.suggestions:
                    print("\n💡 Try asking:")
                    for suggestion in response.suggestions[:3]:
                        print(f"   • {suggestion}")
            else:
                print(f"❌ {response.error_message}")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"💥 Error: {e}")
    
    # End session
    chat.end_session(session_id)
    print("📱 Session ended")

def show_help():
    """Show help information."""
    help_text = """
    🆘 Available Commands:
    
    Natural Language Queries:
    • "Show me all tables"
    • "Find tables with more than 5 columns"
    • "What tables contain player data?"
    • "Get tables from minecraft wiki"
    • "Show me the largest tables"
    
    Special Commands:
    • help     - Show this help
    • summary  - Database summary
    • quit     - Exit the system
    
    💡 Tips:
    • Be specific in your queries
    • Mention column names or data types
    • Ask about table content or structure
    """
    print(help_text)

def show_database_summary(context):
    """Show database summary."""
    try:
        db_client = context.get_component("database_client")
        summary = db_client.get_database_summary()
        
        print("\n📈 Database Summary:")
        print(f"   • Total Tables: {summary.get('total_tables', 0)}")
        print(f"   • Total Rows: {summary.get('total_rows', 0)}")
        print(f"   • Unique Sources: {summary.get('unique_source_files', 0)}")
        print(f"   • Database Type: {summary.get('database_type', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ Could not get summary: {e}")

if __name__ == "__main__":
    main()
```

### Example 3: Custom Component Integration

```python
#!/usr/bin/env python3
"""
Custom component integration example.
Shows how to create and use custom LLM and database components.
"""

import time
from src.core.context import create_default_context
from src.core.interfaces import LLMClient, DatabaseClient
from src.core.registry import register_component
from src.core.types import Schema, Description, Query, QueryResult
from src.components.factories import DocumentProcessorFactory

class MockLLMClient(LLMClient):
    """Mock LLM client for demonstration."""
    
    def __init__(self, **kwargs):
        self.config = kwargs
        print("🤖 MockLLMClient initialized")
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        # Simulate API call delay
        time.sleep(0.1)
        return f"Mock response for: {prompt[:50]}..."
    
    def generate_description(self, schema: Schema, context: str = None) -> Description:
        return Description(
            table_id=schema.table_id,
            content=f"This table has {len(schema.columns)} columns and {schema.row_count} rows. Mock description.",
            summary="Mock table summary",
            generated_by="MockLLMClient",
            confidence=0.95
        )
    
    def generate_sql(self, natural_query: str, database_schema: dict) -> str:
        return f"SELECT * FROM tables WHERE description LIKE '%{natural_query}%'"
    
    def analyze_query(self, query: str, available_tables: list) -> dict:
        return {
            "is_fulfillable": True,
            "confidence": 0.9,
            "reasoning": f"Mock analysis for: {query}",
            "required_tables": [t.get('table_id', '') for t in available_tables[:2]]
        }
    
    def is_available(self) -> bool:
        return True

class InMemoryDatabaseClient(DatabaseClient):
    """In-memory database client for demonstration."""
    
    def __init__(self, **kwargs):
        self.tables = {}
        self.table_data = {}
        print("💾 InMemoryDatabaseClient initialized")
    
    def store_processing_result(self, result) -> bool:
        for table, schema, description in zip(result.tables, result.schemas, result.descriptions):
            self.tables[table.table_id] = {
                "schema": schema,
                "description": description,
                "source": result.document.filename
            }
            self.table_data[table.table_id] = schema.sample_data
        return True
    
    def get_table_by_id(self, table_id: str):
        return self.tables.get(table_id, {}).get("schema")
    
    def search_tables(self, query: str, filters=None):
        matching = []
        for table_id, data in self.tables.items():
            if query.lower() in data["description"].content.lower():
                matching.append(data["schema"])
        return matching
    
    def execute_query(self, query: Query) -> QueryResult:
        # Mock query execution
        results = [
            {"table_id": tid, "description": data["description"].content}
            for tid, data in self.tables.items()
        ]
        
        return QueryResult(
            success=True,
            data=results[:10],  # Limit results
            query=query,
            execution_time=0.05
        )
    
    def get_database_summary(self):
        return {
            "total_tables": len(self.tables),
            "total_rows": sum(len(data) for data in self.table_data.values()),
            "database_type": "InMemory"
        }
    
    def health_check(self) -> bool:
        return True

def main():
    print("🔧 Custom Component Integration Demo")
    print("=" * 50)
    
    # Create context
    context = create_default_context()
    
    # Register custom components
    print("📝 Registering custom components...")
    register_component("llm_client", MockLLMClient)
    register_component("database_client", InMemoryDatabaseClient)
    
    # Verify registration
    registry = context.registry
    components = registry.list_components()
    
    print("✅ Registered components:")
    for interface, impls in components.items():
        for impl in impls:
            print(f"   • {interface}: {impl['class']}")
    
    # Create processor with custom components
    print("\n🏗️  Creating document processor with custom components...")
    factory = DocumentProcessorFactory(context)
    processor = factory.create_document_processor()
    
    # Test processing (create a mock document)
    from src.core.types import Document, DocumentFormat
    
    mock_html = """
    <html>
        <body>
            <h1>Test Document</h1>
            <table>
                <tr><th>Name</th><th>Age</th><th>City</th></tr>
                <tr><td>John</td><td>30</td><td>New York</td></tr>
                <tr><td>Jane</td><td>25</td><td>London</td></tr>
            </table>
        </body>
    </html>
    """
    
    document = Document(
        content=mock_html,
        format=DocumentFormat.HTML,
        source_path=None
    )
    
    print("📄 Processing mock document...")
    result = processor.process_document(document)
    
    if result.success:
        print(f"✅ Processed {result.table_count} tables using custom components!")
        
        for desc in result.descriptions:
            print(f"📊 {desc.table_id}: {desc.content}")
    else:
        print(f"❌ Processing failed: {result.error_message}")
    
    # Test query processing
    print("\n🔍 Testing query processing...")
    from src.components.factories import QueryProcessorFactory
    
    query_factory = QueryProcessorFactory(context)
    query_processor = query_factory.create_query_processor()
    
    test_queries = [
        "Show me all tables",
        "Find tables with user data",
        "What's in the database?"
    ]
    
    for query_text in test_queries:
        query = Query(content=query_text)
        result = query_processor.process_query(query)
        
        print(f"\n❓ Query: {query_text}")
        if result.success:
            print(f"✅ Success: {result.row_count} results")
            for row in result.data[:2]:
                print(f"   📋 {row}")
        else:
            print(f"❌ Failed: {result.error_message}")

if __name__ == "__main__":
    main()
```

### Example 4: REST API Server

```python
#!/usr/bin/env python3
"""
REST API server example.
Provides HTTP endpoints for document processing and querying.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
from pathlib import Path

from src.core.context import create_production_context
from src.components.factories import DocumentProcessorFactory, QueryProcessorFactory
from src.core.types import Document, DocumentFormat, Query
from src.production.deployment import DeploymentManager

# Pydantic models for API
class ProcessRequest(BaseModel):
    html_content: str
    context_hint: Optional[str] = ""
    source_name: Optional[str] = "api_upload"

class QueryRequest(BaseModel):
    query: str
    filters: Optional[dict] = None

class ProcessResponse(BaseModel):
    success: bool
    tables_processed: int
    processing_time: float
    descriptions: List[dict]
    error_message: Optional[str] = None

class QueryResponse(BaseModel):
    success: bool
    data: List[dict]
    row_count: int
    execution_time: float
    error_message: Optional[str] = None

# Create FastAPI app
app = FastAPI(
    title="Table Querying API",
    description="Extract, process, and query HTML tables with LLM descriptions",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global context and components
context = None
document_processor = None
query_processor = None
deployment_manager = None

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup."""
    global context, document_processor, query_processor, deployment_manager
    
    print("🚀 Starting Table Querying API...")
    
    try:
        # Create production context
        context = create_production_context()
        
        # Create components
        doc_factory = DocumentProcessorFactory(context)
        document_processor = doc_factory.create_document_processor()
        
        query_factory = QueryProcessorFactory(context)
        query_processor = query_factory.create_query_processor()
        
        # Create deployment manager for health checks
        from src.production.config import ProductionConfig
        config = ProductionConfig()  # Load from environment
        deployment_manager = DeploymentManager(config)
        
        print("✅ API startup complete!")
        
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        raise

@app.post("/process", response_model=ProcessResponse)
async def process_document(request: ProcessRequest):
    """Process HTML document and extract table descriptions."""
    try:
        # Create document object
        document = Document(
            content=request.html_content,
            format=DocumentFormat.HTML,
            metadata={"context_hint": request.context_hint}
        )
        
        # Process document
        result = document_processor.process_document(document)
        
        if result.success:
            return ProcessResponse(
                success=True,
                tables_processed=result.table_count,
                processing_time=result.processing_time,
                descriptions=[desc.to_dict() for desc in result.descriptions]
            )
        else:
            return ProcessResponse(
                success=False,
                tables_processed=0,
                processing_time=result.processing_time,
                descriptions=[],
                error_message=result.error_message
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process-file")
async def process_file(file: UploadFile = File(...), context_hint: str = ""):
    """Process uploaded HTML file."""
    try:
        # Read file content
        content = await file.read()
        html_content = content.decode('utf-8')
        
        # Process using the existing endpoint
        request = ProcessRequest(
            html_content=html_content,
            context_hint=context_hint,
            source_name=file.filename
        )
        
        return await process_document(request)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    """Execute natural language query against processed tables."""
    try:
        # Create query object
        query = Query(
            content=request.query,
            filters=request.filters or {}
        )
        
        # Execute query
        result = query_processor.process_query(query)
        
        return QueryResponse(
            success=result.success,
            data=result.data,
            row_count=result.row_count,
            execution_time=result.execution_time,
            error_message=result.error_message
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tables")
async def list_tables():
    """List all processed tables."""
    try:
        db_client = context.get_component("database_client")
        summary = db_client.get_database_summary()
        
        # Get table list (implement based on your database client)
        tables = []  # db_client.get_all_tables() if method exists
        
        return {
            "success": True,
            "tables": tables,
            "summary": summary
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """System health check."""
    try:
        health_status = deployment_manager.health_check()
        
        if health_status["status"] == "healthy":
            return health_status
        else:
            raise HTTPException(status_code=503, detail=health_status)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/info")
async def system_info():
    """Get system information."""
    try:
        info = deployment_manager.get_system_info()
        return info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    try:
        # Return metrics in Prometheus format
        metrics_data = context.get_metrics()
        return {"metrics": metrics_data}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def main():
    """Run the API server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Table Querying API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    
    args = parser.parse_args()
    
    print(f"🌐 Starting server on http://{args.host}:{args.port}")
    
    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        workers=args.workers,
        reload=args.reload
    )

if __name__ == "__main__":
    main()
```

---

## 🔧 Configuration Management

### Configuration Hierarchy

The system supports multiple configuration sources with the following priority:

1. **Command line arguments** (highest priority)
2. **Configuration files** (JSON/YAML)
3. **Environment variables**
4. **Default values** (lowest priority)

### Environment Variables

```bash
# Core settings
export ENVIRONMENT="production"
export DEBUG="false"

# Database configuration
export DB_TYPE="postgresql"
export DB_HOST="localhost"
export DB_PORT="5432"
export DB_NAME="table_querying"
export DB_USERNAME="postgres"
export DB_PASSWORD="your-password"

# LLM configuration
export LLM_PROVIDER="openai"
export LLM_MODEL_ID="gpt-3.5-turbo"
export LLM_API_KEY="sk-your-key"
export LLM_BASE_URL=""  # Optional

# Security
export JWT_SECRET="your-jwt-secret"
export ENABLE_AUTH="true"

# Logging
export LOG_LEVEL="INFO"
export LOG_FILE_PATH="/var/log/table_querying/app.log"
```

### Configuration Files

**Basic config (`config.json`):**
```json
{
  "llm": {
    "provider": "bhub",
    "api_key": "your-key",
    "model_id": "mistral-small"
  },
  "database": {
    "type": "sqlite",
    "database": "tables.db"
  }
}
```

**Production config (`production.json`):**
```json
{
  "environment": "production",
  "debug": false,
  
  "database": {
    "type": "postgresql",
    "host": "prod-db.company.com",
    "database": "table_querying",
    "username": "${DB_USERNAME}",
    "password": "${DB_PASSWORD}",
    "pool_size": 20
  },
  
  "llm": {
    "provider": "openai",
    "model_id": "gpt-3.5-turbo",
    "api_key": "${OPENAI_API_KEY}",
    "timeout": 30
  },
  
  "security": {
    "enable_authentication": true,
    "jwt_secret_key": "${JWT_SECRET}",
    "enable_https_only": true
  },
  
  "monitoring": {
    "enable_metrics": true,
    "enable_health_checks": true
  }
}
```

### Programmatic Configuration

```python
from src.production.config import ProductionConfig

# Create configuration
config = ProductionConfig()

# Database configuration
config.database.type = "postgresql"
config.database.host = "localhost"
config.database.database = "my_tables"
config.database.username = "postgres"
config.database.password = "password"

# LLM configuration
config.llm.provider = "openai"
config.llm.model_id = "gpt-3.5-turbo"
config.llm.api_key = "sk-..."

# Security configuration
config.security.enable_authentication = True
config.security.jwt_secret_key = "your-secret"

# Validate configuration
config.validate()

# Use configuration
from src.core.context import ProcessingContext
context = ProcessingContext(config=config.to_system_config())
```

### Multiple Environment Configs

**Structure:**
```
configs/
├── base.json           # Base configuration
├── development.json    # Development overrides
├── staging.json        # Staging overrides
└── production.json     # Production overrides
```

**Load based on environment:**
```python
import os
from pathlib import Path
from src.production.config import load_production_config, ConfigurationManager

# Get environment
env = os.getenv("ENVIRONMENT", "development")

# Load configuration
base_config = load_production_config(Path(f"configs/base.json"))
env_config = load_production_config(Path(f"configs/{env}.json"))

# Merge configurations
manager = ConfigurationManager()
final_config = manager.merge_configs(base_config, env_config)
```

---

## 🐛 Troubleshooting

### Common Issues and Solutions

#### 1. Module Import Errors

**Problem:**
```
ModuleNotFoundError: No module named 'src'
```

**Solutions:**
```bash
# Option 1: Install in development mode
pip install -e .

# Option 2: Add to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Option 3: Use absolute imports
python -m src.main
```

#### 2. Database Connection Issues

**Problem:** Database connection fails

**Debug Steps:**
```python
# Test database configuration
from src.production.config import load_production_config
config = load_production_config()
print("Database config:", config.database.get_connection_params())

# Test connection manually
from src.components.factories import DatabaseClientFactory
from src.core.context import create_default_context

context = create_default_context()
factory = DatabaseClientFactory(context)

if config.database.type == "sqlite":
    client = factory.create_sqlite_client(Path(config.database.database))
elif config.database.type == "postgresql":
    client = factory.create_postgresql_client(
        host=config.database.host,
        database=config.database.database,
        username=config.database.username,
        password=config.database.password
    )

print("Health check:", client.health_check())
```

**Common Fixes:**
- Check database credentials
- Ensure database server is running
- Verify network connectivity
- Check database permissions

#### 3. LLM API Issues

**Problem:** LLM API calls fail

**Debug Steps:**
```python
# Test LLM configuration
from src.components.factories import LLMClientFactory

factory = LLMClientFactory(context)
client = factory.create_llm_client(
    provider="openai",  # or your provider
    model_id="gpt-3.5-turbo",
    api_key="sk-..."
)

print("LLM available:", client.is_available())

# Test simple request
try:
    text = client.generate_text("Hello world", max_tokens=10)
    print("Generated text:", text)
except Exception as e:
    print("Error:", e)
```

**Common Fixes:**
- Verify API key is correct
- Check API quotas and limits
- Ensure correct model ID
- Verify network connectivity

#### 4. Component Registration Issues

**Problem:** Component not found

**Debug Steps:**
```python
# Check registered components
from src.core.registry import get_global_registry

registry = get_global_registry()
components = registry.list_components()

print("Registered components:")
for interface, impls in components.items():
    print(f"  {interface}:")
    for impl in impls:
        print(f"    - {impl['class']}")

# Check specific component
if registry.has_component("llm_client"):
    print("✅ LLM client registered")
else:
    print("❌ LLM client not registered")
```

**Solutions:**
```python
# Register missing components manually
from src.components.adapters import create_llm_adapter
from src.services.implementations.bhub_llm_service import BHubLLMService

llm_service = BHubLLMService(api_key="your-key")
llm_client = create_llm_adapter(llm_service)
registry.register_component("llm_client", type(llm_client))
```

#### 5. Configuration Issues

**Problem:** Configuration validation fails

**Debug Steps:**
```python
# Validate configuration step by step
from src.production.config import ProductionConfig

config = ProductionConfig()

try:
    config.validate()
    print("✅ Configuration valid")
except Exception as e:
    print(f"❌ Configuration invalid: {e}")
    
    # Check individual components
    if not config.llm.api_key:
        print("  Missing LLM API key")
    
    if config.database.type == "postgresql":
        if not config.database.username:
            print("  Missing database username")
        if not config.database.password:
            print("  Missing database password")
```

### Debug Mode

Enable comprehensive debugging:

```python
import logging

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Or use structured logging
from src.production.logging import setup_logging
from src.production.config import LoggingConfig

log_config = LoggingConfig(
    level="DEBUG",
    enable_structured_logging=True,
    enable_file_logging=True
)
setup_logging(log_config)
```

### Performance Issues

```python
# Monitor performance
import time
from src.production.monitoring import MetricsCollector

metrics = MetricsCollector()

# Time operations
start_time = time.time()
# ... your operation ...
duration = time.time() - start_time
metrics.record_processing_time("operation_name", duration)

# Check memory usage
import psutil
print(f"Memory usage: {psutil.Process().memory_info().rss / 1024 / 1024:.1f} MB")
```

### System Validation

Run comprehensive system validation:

```bash
# Command line validation
tq-validate --config production.json

# Or programmatically
python -c "
from src.production.deployment import SystemValidator
from src.production.config import load_production_config

config = load_production_config()
validator = SystemValidator(config)
result = validator.validate_all()

print(f'Validation: {'PASS' if result.valid else 'FAIL'}')
print(f'Checks: {result.checks_passed}/{result.checks_total}')

if result.errors:
    print('Errors:')
    for error in result.errors:
        print(f'  - {error}')
"
```

---

## 📂 Project Structure

```
table_querying_module/
├── 📁 src/                          # Main source code
│   ├── 📁 core/                     # 🏛️ Core abstractions & interfaces
│   │   ├── __init__.py              #    Package initialization
│   │   ├── interfaces.py            #    All component contracts
│   │   ├── types.py                 #    Data structures & enums
│   │   ├── exceptions.py            #    Hierarchical exception system
│   │   ├── registry.py              #    Component registry & DI
│   │   └── context.py               #    Processing context & session management
│   │
│   ├── 📁 components/               # 🔧 Component management layer
│   │   ├── __init__.py              #    Package initialization
│   │   ├── factories.py             #    Smart component factories
│   │   ├── adapters.py              #    Legacy service adapters
│   │   └── implementations/         #    Default component implementations
│   │
│   ├── 📁 services/                 # 🔄 Legacy integration layer
│   │   ├── __init__.py              #    Package initialization
│   │   ├── llm_service.py           #    Abstract LLM service interface
│   │   ├── database_service.py      #    Abstract database service interface
│   │   ├── service_factory.py       #    Legacy service factory
│   │   └── implementations/         #    Concrete service implementations
│   │       ├── bhub_llm_service.py  #      BHub LLM implementation
│   │       ├── openai_llm_service.py#      OpenAI LLM implementation
│   │       └── sqlite_database_service.py # SQLite implementation
│   │
│   ├── 📁 production/               # 🚀 Production deployment tools
│   │   ├── __init__.py              #    Package initialization
│   │   ├── config.py                #    Production configuration management
│   │   ├── deployment.py            #    System deployment & validation
│   │   ├── logging.py               #    Production logging setup
│   │   ├── monitoring.py            #    Health checks & metrics
│   │   └── security.py              #    Security & authentication
│   │
│   └── 📁 table_querying/           # 🗃️ Original processing modules
│       ├── main.py                  #    Original main entry point
│       ├── table_processor.py       #    Main table processing orchestrator
│       ├── table_extractor.py       #    HTML table extraction
│       ├── schema_processor.py      #    Schema generation & type inference
│       ├── table_summarizer.py      #    LLM description generation
│       ├── table_database.py        #    Database operations
│       └── document_processor.py    #    Document transformation
│
├── 📁 examples/                     # 📖 Integration examples
│   ├── custom_llm_service_example.py      #    Custom LLM implementation
│   ├── custom_database_service_example.py #    Custom database implementation
│   ├── service_configuration_examples.py  #    Configuration patterns
│   ├── basic_usage.py               #    Basic usage examples
│   ├── production_deployment.py     #    Production deployment example
│   └── api_integration.py           #    REST API example
│
├── 📁 configs/                      # ⚙️ Configuration files
│   ├── development.json             #    Development configuration
│   ├── production.json              #    Production configuration
│   ├── testing.json                 #    Testing configuration
│   └── docker.json                  #    Docker configuration
│
├── 📁 docs/                         # 📚 Documentation
│   ├── api/                         #    API documentation
│   ├── guides/                      #    User guides
│   └── examples/                    #    Code examples
│
├── 📁 tests/                        # 🧪 Test suite
│   ├── unit/                        #    Unit tests
│   ├── integration/                 #    Integration tests
│   ├── system/                      #    System tests
│   └── fixtures/                    #    Test fixtures & sample data
│
├── 📁 scripts/                      # 🔧 Utility scripts
│   ├── deploy.sh                    #    Deployment script
│   ├── setup_dev.sh                 #    Development setup
│   └── run_tests.sh                 #    Test runner
│
├── 📄 INSTRUCTIONS.md               # 📋 This file - complete instructions
├── 📄 INTEGRATION_GUIDE.md         # 🎯 Detailed integration guide
├── 📄 PROJECT_ARCHITECTURE.md      # 🏗️ Architecture documentation
├── 📄 WORKFLOW_SUMMARY.md          # 📝 Original workflow summary
├── 📄 SERVICES_README.md           # 🔧 Services architecture guide
├── 📄 README.md                    # 👋 Project overview
├── 📄 requirements.txt              # 📦 Python dependencies
├── 📄 setup.py                     # 🛠️ Package setup & installation
├── 📄 docker-compose.yml           # 🐳 Docker deployment
├── 📄 Dockerfile                   # 🐳 Docker image definition
└── 📄 .env.example                 # 🔑 Environment variables template
```

### File Categories

#### 🏛️ **Core Architecture (src/core/)**
- **Foundation interfaces** that define all component contracts
- **Data types** and structures used throughout the system
- **Component registry** with dependency injection
- **Processing context** for session and state management

#### 🔧 **Component Management (src/components/)**
- **Factories** for creating configured component instances
- **Adapters** for legacy service integration
- **Implementations** of core interfaces

#### 🔄 **Legacy Integration (src/services/)**
- **Existing service implementations** (BHub, OpenAI, SQLite)
- **Service factory** for backward compatibility
- **Migration bridge** to new architecture

#### 🚀 **Production Tools (src/production/)**
- **Configuration management** with validation
- **Deployment automation** and system validation
- **Monitoring, logging, and security** components

#### 📖 **Documentation & Examples**
- **Complete usage examples** for all scenarios
- **Integration guides** for custom components
- **Architecture documentation** and design patterns

---

## 🌟 Key Features

### ✅ **Maximum Component Abstraction**
- **Interface-first design** - Every component implements clean interfaces
- **Dependency injection** - No hard dependencies anywhere
- **Component registry** - Central registry for all implementations
- **Plugin architecture** - Dynamic component loading

### ✅ **Trivial Component Swapping**
- **1-line configuration changes** to swap providers
- **Environment-based switching** for different deployments
- **Multi-provider support** with automatic fallback
- **Legacy compatibility** through adapters

### ✅ **Production Ready**
- **Comprehensive configuration** with validation
- **Health monitoring** and metrics collection
- **Security controls** with authentication
- **Deployment automation** with Docker/Kubernetes support

### ✅ **Developer Friendly**
- **30-second quickstart** for new users
- **Comprehensive examples** for all use cases
- **Detailed documentation** with troubleshooting
- **Multiple interfaces** (CLI, API, programmatic)

### ✅ **Enterprise Grade**
- **Scalable architecture** with connection pooling
- **Error handling** with structured logging
- **Performance monitoring** with metrics
- **Security hardening** with best practices

---

## 🎯 **Mission Accomplished!**

This system now provides:

1. **🏗️ World-Class Architecture** - Clean interfaces, dependency injection, modular design
2. **🔄 Effortless Component Swapping** - Change any component in 1 line
3. **🚀 Production Readiness** - Full deployment, monitoring, security
4. **👨‍💻 Developer Experience** - 30-second start, comprehensive docs
5. **🔌 Extensibility** - Plugin system for custom components
6. **🛡️ Enterprise Features** - Security, scalability, monitoring

**Any developer can now:**
- ✅ Start using it in **30 seconds**
- ✅ Swap any component in **1 line**
- ✅ Deploy to production with **confidence**
- ✅ Extend with custom components **easily**
- ✅ Migrate from existing systems **gradually**

🎉 **This is now a professional-grade, modular system ready for any use case!**

---

*For additional help, examples, or troubleshooting, refer to the comprehensive documentation files or create an issue in the repository.*