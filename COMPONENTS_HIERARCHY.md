# Components Hierarchy Documentation

## Table Querying System Architecture Overview

This document provides a comprehensive view of all components, interfaces, and their interactions within the Table Querying System. The system is designed as a modular, extensible pipeline for extracting, processing, and querying tables from HTML documents.

## System Architecture Layers

### 1. Core Layer (`src/core/`)

The foundational layer that defines the system's architecture through interfaces, types, and component management.

#### Core Interfaces (`interfaces.py`)

**Primary Processing Interfaces:**
- `DocumentProcessor` - High-level document processing orchestrator
- `TableExtractor` - Extracts tables from documents
- `SchemaGenerator` - Generates table schemas 
- `TableDescriptor` - Creates natural language descriptions

**Data Access Interfaces:**
- `DatabaseClient` - Database operations and storage
- `LLMClient` - LLM service interactions
- `QueryProcessor` - User query processing
- `ChatInterface` - Chat-based interactions

**System Management Interfaces:**
- `ComponentManager` - Component registration and lifecycle
- `PluginManager` - Plugin loading and management
- `ConfigurationManager` - Configuration management
- `MetricsCollector` - System metrics collection
- `Logger` - Structured logging

**Advanced Interfaces:**
- `StreamingProcessor` - Async/streaming processing
- `EventHandler` - System event handling

#### Core Types (`types.py`)

**Data Structures:**
- `Document` - Represents documents to be processed
- `Table` - Extracted table representation
- `Schema` - Table schema with column types and metadata
- `Description` - LLM-generated table descriptions
- `Query` - User query representation
- `QueryResult` - Query execution results
- `ProcessingResult` - Complete processing outcomes
- `ChatResponse` - Chat interaction responses

**Configuration Types:**
- `ComponentConfig` - Component-specific configuration
- `SystemConfig` - System-wide configuration
- `ValidationResult` - Validation outcomes

**Enumerations:**
- `DocumentFormat` - Supported document formats (HTML, Markdown, JSON, XML)
- `TableFormat` - Table representation formats
- `DataType` - Column data types
- `ProcessingStatus` - Processing state tracking

#### Component Management (`registry.py`)

**ComponentRegistry:**
- Central registry for all system components
- Dependency injection and lifecycle management  
- Component validation against interfaces
- Singleton pattern support
- Plugin loading capabilities

**ComponentRegistration:**
- Component metadata and instantiation logic
- Dependency resolution
- Factory pattern integration

### 2. Services Layer (`src/services/`)

Concrete implementations of core interfaces, providing pluggable service architectures.

#### Service Abstractions

**LLMService** (`llm_service.py`)
- Abstract base for LLM interactions
- Standardized API for different providers
- Error handling and retry logic

**DatabaseService** (`database_service.py`)
- Abstract base for database operations
- Connection management
- Transaction handling

#### Service Implementations (`implementations/`)

**LLM Providers:**
- `BHubLLMService` - BHub API integration
- `OpenAILLMService` - OpenAI API integration  
- `SQLiteDatabaseService` - SQLite database implementation

#### Service Factory (`service_factory.py`)

**ServiceFactory:**
- Creates configured service instances
- Manages service registration
- Provides service discovery
- Configuration validation and injection

**ServiceConfig:**
- Unified configuration for all services
- Environment variable integration
- Provider-specific parameter handling

### 3. Components Layer (`src/components/`)

Component creation and management utilities.

#### Factory Pattern (`factories.py`)

**Specialized Factories:**
- `DocumentProcessorFactory` - Creates complete document processors
- `LLMClientFactory` - Multi-provider LLM client creation
- `DatabaseClientFactory` - Database client instantiation
- `QueryProcessorFactory` - Query processor configuration
- `ChatInterfaceFactory` - Chat interface setup
- `PluginFactory` - Plugin-based component loading

#### Adapter Pattern (`adapters.py`)

**Service Adapters:**
- Bridge between legacy implementations and new interfaces
- Protocol translation layers
- Backward compatibility support

### 4. Table Querying Layer (`src/table_querying/`)

The main business logic implementing the table processing pipeline.

#### Core Pipeline Components

**TableProcessor** (`table_processor.py`)
- **Role:** Main orchestrator for the entire pipeline
- **Dependencies:** TableExtractor, SchemaProcessor, TableSummarizer, TableDatabase, DocumentProcessor
- **Workflow:**
  1. Initialize processing session
  2. Extract tables and markdown content
  3. Generate schemas for all tables
  4. Create LLM descriptions
  5. Store everything in database
  6. Replace tables with descriptions in document
  7. Save all outputs

**TableExtractor** (`table_extractor.py`)
- **Role:** Extracts HTML tables and converts documents to markdown
- **Technologies:** docling, BeautifulSoup
- **Outputs:** HTML tables, markdown chunks, full markdown content

**SchemaProcessor** (`schema_processor.py`)
- **Role:** Analyzes tables and generates flattened schemas
- **Features:** Type inference, data sampling, metadata extraction
- **Outputs:** Structured schemas with column types and statistics

**TableSummarizer** (`table_summarizer.py`)
- **Role:** Uses LLM to generate natural language table descriptions
- **Features:** Context-aware descriptions, batch processing
- **Integration:** Works with multiple LLM providers via ServiceFactory

**TableDatabase** (`table_database.py`)
- **Role:** SQLite-based storage for tables, schemas, and descriptions
- **Schema:** tables, table_data, processing_sessions
- **Features:** Session tracking, querying, database statistics

**DocumentProcessor** (`document_processor.py`)
- **Role:** Replaces tables in documents with their LLM descriptions
- **Features:** Intelligent table identification, content preservation
- **Outputs:** Processed documents, replacement reports

#### Configuration System (`config.py`)

**TableProcessingConfig:**
- Comprehensive configuration management
- Environment variable integration
- Preset configurations for different use cases
- Validation and default handling

### 5. Chat Module (`src/chatting_module/`)

Natural language querying interface over processed tables.

#### Chat Components

**ChatInterface** (`chat_interface.py`)
- **Role:** Main chat interaction handler
- **Dependencies:** QueryAnalyzer, SQLGenerator, DatabaseService
- **Features:** Session management, context preservation

**QueryAnalyzer** (`query_analyzer.py`)
- **Role:** Analyzes natural language queries
- **Features:** Intent recognition, table identification, complexity assessment

**SQLGenerator** (`sql_generator.py`)
- **Role:** Converts natural language to SQL queries
- **Features:** Schema-aware generation, safety validation

### 6. Production Layer (`src/production/`)

Production deployment and configuration management.

#### Production Configuration (`config.py`)

**ProductionConfig:**
- Environment-specific configurations
- Security settings
- Performance optimizations
- Monitoring integration

#### Deployment Support (`deployment.py`)

**DeploymentManager:**
- Container orchestration
- Service discovery
- Health checks
- Scaling configuration

## Component Interaction Flow

### Primary Processing Flow

```
HTML Document → TableExtractor → SchemaProcessor → TableSummarizer → TableDatabase
                      ↓                                    ↓
              DocumentProcessor ← ← ← ← ← ← ← ← ← ← ← ← Description
```

### Service Architecture Flow

```
TableProcessor → ServiceFactory → LLMService/DatabaseService
                      ↓
              ComponentRegistry → Interface Implementations
```

### Chat Query Flow

```
User Query → ChatInterface → QueryAnalyzer → SQLGenerator → DatabaseService → Results
```

## Key Design Patterns

### 1. Abstract Factory Pattern
- **ServiceFactory**: Creates families of related services (LLM, Database)
- **ComponentFactory**: Creates configured component instances
- **PluginFactory**: Dynamically loads external components

### 2. Registry Pattern
- **ComponentRegistry**: Central component registration and discovery
- **Plugin loading**: Dynamic component registration from external modules

### 3. Strategy Pattern
- **LLMService**: Interchangeable LLM providers (BHub, OpenAI, etc.)
- **DatabaseService**: Pluggable database implementations

### 4. Pipeline Pattern
- **TableProcessor**: Sequential processing stages with error handling
- **Document flow**: Extraction → Schema → Description → Storage → Replacement

### 5. Adapter Pattern
- **Service adapters**: Bridge between legacy and new interfaces
- **Protocol translation**: Normalize different API formats

## Extension Points

### 1. Adding New LLM Providers
1. Implement `LLMService` interface
2. Register with `ServiceFactory`
3. Add configuration parameters

### 2. Adding New Database Backends
1. Implement `DatabaseService` interface
2. Register with `ServiceFactory`
3. Add connection configuration

### 3. Custom Processing Components
1. Implement relevant core interface
2. Register with `ComponentRegistry`
3. Configure via `ComponentFactory`

### 4. Plugin Development
1. Create plugin file with `register_plugin()` function
2. Implement required interfaces
3. Use `PluginLoader` for dynamic loading

## Configuration Architecture

### 1. Hierarchical Configuration
- **System-level**: Global settings and defaults
- **Component-level**: Component-specific configuration
- **Runtime-level**: Dynamic overrides and parameters

### 2. Configuration Sources
- **JSON files**: Persistent configuration storage
- **Environment variables**: Runtime environment settings
- **Command-line arguments**: Execution-specific parameters
- **Presets**: Predefined configuration bundles

### 3. Configuration Validation
- **Type checking**: Pydantic-based validation
- **Required parameters**: Automatic validation of mandatory settings
- **Default values**: Intelligent fallback mechanisms

## Error Handling and Resilience

### 1. Custom Exception Hierarchy
- **TableQueryingError**: Base exception for all system errors
- **ComponentNotFoundError**: Component registration/discovery errors
- **ConfigurationError**: Configuration validation errors
- **ValidationError**: Data validation errors

### 2. Graceful Degradation
- **Service fallbacks**: Automatic failover between LLM providers
- **Partial processing**: Continue processing despite individual table failures
- **Recovery mechanisms**: Session restoration and error recovery

### 3. Monitoring and Observability
- **MetricsCollector**: System performance monitoring
- **Structured logging**: Comprehensive event tracking
- **Health checks**: Service availability monitoring

## Database Schema

### Core Tables

**tables:**
- `id`: Primary key
- `session_id`: Processing session identifier
- `source_file`: Original document path
- `table_index`: Table position in document
- `html_content`: Original HTML table
- `llm_description`: Generated description
- `schema_json`: Table schema metadata
- `created_at`: Timestamp

**table_data:**
- `id`: Primary key
- `table_id`: Foreign key to tables
- `row_data`: JSON row data
- `row_index`: Row position

**processing_sessions:**
- `id`: Session identifier
- `source_file`: Processed document
- `created_at`: Processing timestamp
- `completed`: Processing status

This architecture provides a robust, extensible foundation for table processing with clear separation of concerns, pluggable components, and comprehensive configuration management.