# TableLLM Querying System - Implementation Guide

A comprehensive guide for implementing and extending the interface-based table processing system.

## Table of Contents

1. [System Overview](#system-overview)
2. [Quick Start](#quick-start)
3. [Architecture Deep Dive](#architecture-deep-dive)
4. [Implementing New Components](#implementing-new-components)
5. [Extending the System](#extending-the-system)
6. [Configuration Management](#configuration-management)
7. [Testing](#testing)
8. [Deployment](#deployment)
9. [Troubleshooting](#troubleshooting)

## System Overview

The TableLLM Querying system uses an **interface-based architecture** with dependency injection, component registry, and factory patterns. This design provides:

- **Modularity**: Components are loosely coupled and interchangeable
- **Extensibility**: Easy to add new implementations without changing existing code
- **Testability**: Components can be mocked and tested independently
- **Flexibility**: Multiple architectures (legacy + interface) supported

### Key Architecture Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Core Layer    │    │ Components Layer │    │ Services Layer  │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • Interfaces    │    │ • Factories     │    │ • LLM Service   │
│ • Types         │    │ • Adapters      │    │ • DB Service    │
│ • Registry      │    │ • Implementations│    │ • Service Factory│
│ • Context       │    │                 │    │                 │
│ • Exceptions    │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ Application Layer│
                    ├─────────────────┤
                    │ • TableProcessor │
                    │ • Main CLI      │
                    │ • Config Mgmt   │
                    └─────────────────┘
```

## Quick Start

### 1. Installation and Setup

```bash
# Clone the repository
git clone <repository-url>
cd TableLLMQuerying

# Install dependencies
pip install -r table_querying_module/requirements.txt

# Install the module in development mode
cd table_querying_module && pip install -e .
```

### 2. Basic Usage

```python
from table_querying.table_processor_factory import create_processor

# Create processor with interface architecture
config = {
    'api_key': 'your-openai-api-key-here',
    'model_id': 'gpt-3.5-turbo',
    'llm_service_type': 'openai',
    'db_path': 'my_tables.db',
    'architecture': 'interface'  # Use new interface system
}

processor = create_processor(config)

# Process an HTML document
results = processor.process_document('document.html')
processor.print_processing_summary(results)
```

### 3. Run Tests

```bash
# Run all tests
python tests/run_tests.py

# Run specific test categories
python tests/run_tests.py --category core
python tests/run_tests.py --category implementations
python tests/run_tests.py --category integration

# Run with verbose output
python tests/run_tests.py --verbosity 2
```

## Architecture Deep Dive

### Core Interfaces

The system defines 6 core interfaces that represent the main processing stages:

#### 1. DocumentProcessor
Main orchestrator that coordinates the entire pipeline.

```python
from core.interfaces import DocumentProcessor
from core.types import Document, ProcessingResult

class MyDocumentProcessor(DocumentProcessor):
    def process_document(self, document: Document) -> ProcessingResult:
        # Implement complete processing pipeline
        pass
    
    def process_file(self, file_path: Path) -> ProcessingResult:
        # Implement file-based processing
        pass
```

#### 2. TableExtractor
Extracts tables from documents.

```python
from core.interfaces import TableExtractor
from core.types import Document, Table

class MyTableExtractor(TableExtractor):
    def extract_tables(self, document: Document) -> List[Table]:
        # Implement table extraction logic
        pass
    
    def supported_formats(self) -> List[str]:
        return ['html', 'pdf', 'docx']
```

#### 3. SchemaGenerator
Generates structured schemas from extracted tables.

```python
from core.interfaces import SchemaGenerator
from core.types import Table, Schema

class MySchemaGenerator(SchemaGenerator):
    def generate_schema(self, table: Table) -> Schema:
        # Implement schema generation
        pass
    
    def generate_schemas(self, tables: List[Table]) -> List[Schema]:
        return [self.generate_schema(table) for table in tables]
```

#### 4. TableDescriptor
Generates natural language descriptions using LLM.

```python
from core.interfaces import TableDescriptor
from core.types import Schema, Description

class MyTableDescriptor(TableDescriptor):
    def describe_table(self, schema: Schema, context: Optional[str] = None) -> Description:
        # Implement LLM-based description generation
        pass
```

#### 5. DatabaseClient
Handles database operations for storing results.

```python
from core.interfaces import DatabaseClient
from core.types import ProcessingResult

class MyDatabaseClient(DatabaseClient):
    def store_processing_result(self, result: ProcessingResult) -> bool:
        # Implement result storage
        pass
    
    def get_table_by_id(self, table_id: str) -> Optional[Schema]:
        # Implement table retrieval
        pass
```

#### 6. LLMClient
Abstract interface for LLM interactions.

```python
from core.interfaces import LLMClient
from core.types import Schema, Description

class MyLLMClient(LLMClient):
    def generate_description(self, schema: Schema, context: Optional[str] = None) -> Description:
        # Implement LLM API calls
        pass
```

### Component Registry System

The registry manages component lifecycle and dependency resolution:

```python
from core.registry import get_global_registry
from core.types import ComponentConfig

# Get global registry instance
registry = get_global_registry()

# Register a component
registry.register_component(
    component_name='my_extractor',
    component_class=MyTableExtractor,
    config=ComponentConfig(
        component_type='table_extractor',
        implementation='MyTableExtractor',
        config={'debug': True}
    ),
    dependencies=['database_client'],  # Optional dependencies
    singleton=False  # Create new instance each time
)

# Get component (resolves dependencies automatically)
extractor = registry.get_component('my_extractor')

# Validate all dependencies
validation = registry.validate_dependencies()
if not validation.valid:
    print("Dependency errors:", validation.errors)
```

## Implementing New Components

### Step 1: Choose Your Interface

Decide which interface your component will implement:

- **TableExtractor**: For new document formats or extraction methods
- **SchemaGenerator**: For custom schema generation logic
- **TableDescriptor**: For different LLM providers or description styles
- **DatabaseClient**: For different database backends
- **DocumentProcessor**: For custom processing pipelines

### Step 2: Implement the Interface

```python
# Example: Custom PDF table extractor
from core.interfaces import TableExtractor
from core.types import Document, Table, ValidationResult, DocumentFormat, TableFormat
from core.exceptions import TableQueryingError

class PDFTableExtractor(TableExtractor):
    def __init__(self, **config):
        self.config = config
        self.debug = config.get('debug', False)
        # Initialize PDF parsing library
        
    def extract_tables(self, document: Document) -> List[Table]:
        if document.format != DocumentFormat.PDF:
            raise TableQueryingError("PDF extractor only supports PDF format")
        
        tables = []
        # Your PDF extraction logic here
        # ...
        
        return tables
    
    def supported_formats(self) -> List[str]:
        return ['pdf']
    
    def validate_table(self, table: Table) -> ValidationResult:
        result = ValidationResult(valid=True)
        
        if not table.content:
            result.add_error("Table content cannot be empty")
        
        if table.format != TableFormat.HTML:
            result.add_warning("Non-HTML tables may have limited support")
        
        return result
```

### Step 3: Register Your Component

```python
# In your initialization code
from core.registry import get_global_registry
from core.types import ComponentConfig

registry = get_global_registry()

registry.register_component(
    'pdf_extractor',
    PDFTableExtractor,
    ComponentConfig(
        component_type='table_extractor',
        implementation='PDFTableExtractor',
        config={
            'debug': True,
            'pdf_library': 'pdfplumber'
        }
    )
)
```

### Step 4: Use in TableProcessor

```python
# Create custom processor configuration
from table_querying.table_processor_v2 import TableProcessorV2

config = {
    'extractor_type': 'pdf_extractor',  # Use your custom extractor
    'api_key': 'your-api-key',
    'db_path': 'my_database.db'
}

processor = TableProcessorV2(config)
```

## Extending the System

### Adding New Service Types

1. **Define Service Interface**:

```python
# In services/my_service.py
from abc import ABC, abstractmethod

class TranslationService(ABC):
    @abstractmethod
    def translate_description(self, text: str, target_language: str) -> str:
        pass
```

2. **Implement Service**:

```python
class GoogleTranslationService(TranslationService):
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def translate_description(self, text: str, target_language: str) -> str:
        # Implement Google Translate API calls
        pass
```

3. **Add to Service Factory**:

```python
# In services/service_factory.py
class ServiceFactory:
    @staticmethod
    def create_translation_service(config: ServiceConfig) -> TranslationService:
        if config.translation_service_type == 'google':
            return GoogleTranslationService(config.translation_api_key)
        else:
            raise ValueError(f"Unknown translation service: {config.translation_service_type}")
```

### Creating Custom Adapters

Adapters bridge different interfaces or legacy systems:

```python
# Example: Adapter for legacy database to new interface
from core.interfaces import DatabaseClient
from core.types import ProcessingResult

class LegacyDatabaseAdapter(DatabaseClient):
    def __init__(self, legacy_db_instance):
        self.legacy_db = legacy_db_instance
    
    def store_processing_result(self, result: ProcessingResult) -> bool:
        # Convert new format to legacy format
        legacy_data = self._convert_to_legacy_format(result)
        
        # Use legacy database methods
        return self.legacy_db.store_data(legacy_data)
    
    def _convert_to_legacy_format(self, result: ProcessingResult):
        # Conversion logic here
        pass
```

### Plugin System

Create a plugin system for dynamic component loading:

```python
# plugins/my_plugin.py
from core.interfaces import TableExtractor

class PluginTableExtractor(TableExtractor):
    # Implementation here
    pass

def register_plugin(registry):
    """Plugin registration function"""
    registry.register_component(
        'plugin_extractor',
        PluginTableExtractor,
        # ... config
    )
```

Load plugins dynamically:

```python
import importlib
from pathlib import Path

def load_plugins(plugin_directory: Path, registry):
    for plugin_file in plugin_directory.glob('*.py'):
        if plugin_file.name.startswith('_'):
            continue
        
        module_name = plugin_file.stem
        spec = importlib.util.spec_from_file_location(module_name, plugin_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Call plugin registration
        if hasattr(module, 'register_plugin'):
            module.register_plugin(registry)
```

## Configuration Management

### Configuration Hierarchy

The system supports multiple configuration sources in order of precedence:

1. Command line arguments (highest priority)
2. Configuration files
3. Environment variables
4. Default values (lowest priority)

### Creating Configuration Presets

```python
# In config/presets.py
MINECRAFT_WIKI_PRESET = {
    'architecture': 'interface',
    'context_hint': 'This data comes from Minecraft Wiki pages with game-related information',
    'model_id': 'gpt-3.5-turbo',
    'save_outputs': True,
    'clear_database_on_start': False,
    'output_formats': ['markdown', 'json'],
    'table_processing': {
        'min_rows': 2,
        'max_columns': 20,
        'skip_empty_tables': True
    }
}
```

### Using Configuration Validation

```python
from core.types import SystemConfig, ComponentConfig
from core.exceptions import ValidationError

def validate_configuration(config_dict: dict) -> SystemConfig:
    """Validate and create system configuration."""
    
    # Required fields
    if 'api_key' not in config_dict:
        raise ValidationError("API key is required")
    
    # Create system config with validation
    system_config = SystemConfig(
        global_settings=config_dict,
        environment=config_dict.get('environment', 'production'),
        debug=config_dict.get('debug', False)
    )
    
    return system_config
```

## Testing

### Unit Testing Components

```python
import unittest
from unittest.mock import Mock, patch
from your_component import YourComponent

class TestYourComponent(unittest.TestCase):
    def setUp(self):
        self.component = YourComponent(debug=True)
    
    def test_basic_functionality(self):
        # Test your component
        result = self.component.process_data("test_input")
        self.assertEqual(result.status, "success")
    
    @patch('your_component.external_api_call')
    def test_with_mocked_dependency(self, mock_api):
        mock_api.return_value = {"status": "success"}
        
        result = self.component.process_with_api("test_data")
        self.assertTrue(result.success)
        mock_api.assert_called_once()
```

### Integration Testing

```python
def test_complete_workflow():
    """Test the complete processing workflow."""
    
    # Setup
    config = {
        'api_key': 'test-key',
        'db_path': ':memory:',
        'architecture': 'interface'
    }
    
    processor = create_processor(config)
    
    # Create test document
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write('<html><body><table><tr><td>Test</td></tr></table></body></html>')
        test_file = f.name
    
    try:
        # Process document
        results = processor.process_document(test_file)
        
        # Verify results
        assert results['success'] == True
        assert 'statistics' in results
        assert results['statistics']['html_tables'] > 0
        
    finally:
        os.unlink(test_file)
```

### Performance Testing

```python
import time
import psutil
import gc

def test_memory_usage():
    """Test memory usage with large documents."""
    
    process = psutil.Process()
    initial_memory = process.memory_info().rss
    
    # Process large document
    processor = create_processor({'db_path': ':memory:'})
    
    # Create document with many tables
    large_html = create_large_test_document(num_tables=100)
    
    start_time = time.time()
    results = processor.process_document_content(large_html)
    processing_time = time.time() - start_time
    
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    
    # Assertions
    assert processing_time < 60.0  # Should complete within 60 seconds
    assert memory_increase < 100 * 1024 * 1024  # Less than 100MB increase
    assert results['success'] == True
    
    # Cleanup
    gc.collect()
```

## Deployment

### Production Configuration

```python
# config/production.json
{
    "architecture": "interface",
    "environment": "production",
    "debug": false,
    "logging": {
        "level": "INFO",
        "file": "/var/log/table-processing.log",
        "max_size": "10MB",
        "backup_count": 5
    },
    "database": {
        "path": "/data/tables.db",
        "backup_enabled": true,
        "backup_interval": "24h"
    },
    "api_settings": {
        "timeout": 30,
        "retry_attempts": 3,
        "rate_limit": 100
    },
    "monitoring": {
        "enabled": true,
        "metrics_endpoint": "/metrics",
        "health_check_endpoint": "/health"
    }
}
```

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install
COPY table_querying_module/requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY table_querying_module/ ./table_querying_module/
COPY CLAUDE.md COMPONENTS_HIERARCHY.md ./

# Install application
RUN cd table_querying_module && pip install -e .

# Create data directory
RUN mkdir -p /data /logs

# Set environment variables
ENV TABLE_DB_PATH=/data/tables.db
ENV LOG_LEVEL=INFO

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from table_querying.table_processor_factory import create_processor; p=create_processor({'db_path':':memory:'}); print('healthy')"

# Run application
CMD ["python", "-m", "table_querying.main_v2"]
```

### Kubernetes Deployment

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: table-processor
spec:
  replicas: 3
  selector:
    matchLabels:
      app: table-processor
  template:
    metadata:
      labels:
        app: table-processor
    spec:
      containers:
      - name: table-processor
        image: table-processor:latest
        env:
        - name: YOUR_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: llm-api-key
        - name: TABLE_DB_PATH
          value: "/data/tables.db"
        volumeMounts:
        - name: data-volume
          mountPath: /data
        resources:
          requests:
            memory: "512Mi"
            cpu: "200m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
      volumes:
      - name: data-volume
        persistentVolumeClaim:
          claimName: table-processor-data
```

## Troubleshooting

### Common Issues

#### 1. Import Errors

```python
# Problem: ModuleNotFoundError
# Solution: Check sys.path and installation

import sys
from pathlib import Path

# Add to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent / 'table_querying_module' / 'src'))

# Verify installation
try:
    import table_querying
    print(f"Module location: {table_querying.__file__}")
except ImportError as e:
    print(f"Import error: {e}")
    print("Run: pip install -e table_querying_module/")
```

#### 2. Component Registration Issues

```python
# Problem: ComponentNotFoundError
# Solution: Debug registry state

from core.registry import get_global_registry

registry = get_global_registry()

# Check registered components
components = registry.list_components()
print("Registered components:", components)

# Validate dependencies
validation = registry.validate_dependencies()
if not validation.valid:
    print("Dependency errors:", validation.errors)
    print("Warnings:", validation.warnings)
```

#### 3. Configuration Problems

```python
# Problem: Configuration not loading correctly
# Solution: Debug configuration loading

def debug_configuration(config_path):
    """Debug configuration loading issues."""
    
    try:
        with open(config_path) as f:
            config_data = json.load(f)
        print("✅ Configuration file loaded successfully")
        print(f"Keys: {list(config_data.keys())}")
        
        # Check required fields
        required_fields = ['api_key', 'architecture', 'db_path']
        missing_fields = [field for field in required_fields if field not in config_data]
        
        if missing_fields:
            print(f"❌ Missing required fields: {missing_fields}")
        else:
            print("✅ All required fields present")
            
        return config_data
        
    except FileNotFoundError:
        print(f"❌ Configuration file not found: {config_path}")
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    return None
```

#### 4. Database Connection Issues

```python
# Problem: Database connection failures
# Solution: Debug database connectivity

def debug_database_connection(db_path):
    """Debug database connection issues."""
    
    from table_querying.interface_implementations import DatabaseClientImpl
    
    try:
        # Test database client creation
        db_client = DatabaseClientImpl(db_path=db_path)
        print("✅ Database client created successfully")
        
        # Test health check
        health = db_client.health_check()
        if health:
            print("✅ Database health check passed")
        else:
            print("❌ Database health check failed")
        
        # Test summary
        summary = db_client.get_database_summary()
        print(f"Database summary: {summary}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False
```

### Performance Optimization

#### 1. Memory Management

```python
import gc
import psutil

def monitor_memory_usage():
    """Monitor and optimize memory usage."""
    
    process = psutil.Process()
    
    def print_memory_info(stage):
        memory_info = process.memory_info()
        print(f"{stage}: RSS={memory_info.rss / 1024 / 1024:.1f}MB, VMS={memory_info.vms / 1024 / 1024:.1f}MB")
    
    print_memory_info("Start")
    
    # Your processing code here
    # ...
    
    print_memory_info("After processing")
    
    # Force garbage collection
    gc.collect()
    
    print_memory_info("After garbage collection")
```

#### 2. Processing Optimization

```python
def optimize_batch_processing(documents, batch_size=10):
    """Process documents in batches to optimize performance."""
    
    from table_querying.table_processor_factory import create_processor
    
    processor = create_processor({
        'db_path': ':memory:',  # Use in-memory for speed
        'save_outputs': False,   # Disable file output for batch processing
        'debug': False          # Disable debug logging
    })
    
    results = []
    
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        
        print(f"Processing batch {i//batch_size + 1}/{(len(documents) + batch_size - 1)//batch_size}")
        
        batch_results = []
        for doc in batch:
            result = processor.process_document(doc)
            batch_results.append(result)
        
        results.extend(batch_results)
        
        # Cleanup after each batch
        gc.collect()
    
    return results
```

### Debugging Tips

1. **Enable Debug Logging**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

2. **Use Component Info**:
```python
processor = create_processor(config)
info = processor.get_component_info()
print(json.dumps(info, indent=2))
```

3. **Test Individual Components**:
```python
# Test just extraction
extractor = TableExtractorImpl()
tables = extractor.extract_tables(document)
print(f"Extracted {len(tables)} tables")
```

4. **Validate All Dependencies**:
```python
from core.registry import get_global_registry
registry = get_global_registry()
validation = registry.validate_dependencies()
if not validation.valid:
    for error in validation.errors:
        print(f"Error: {error}")
```

---

## Summary

This implementation guide covers:

✅ **System Architecture**: Interface-based design with dependency injection  
✅ **Component Implementation**: Step-by-step guide for new components  
✅ **Extension Patterns**: Services, adapters, plugins  
✅ **Configuration Management**: Presets, validation, environment variables  
✅ **Testing Strategy**: Unit, integration, and performance tests  
✅ **Deployment Options**: Docker, Kubernetes, production configs  
✅ **Troubleshooting**: Common issues and debugging techniques  

The system is now fully documented with comprehensive tests and ready for production use or further extension!