# Table Querying Module - Project Architecture

This document provides a comprehensive overview of the project's architecture, design principles, and component interactions.

## Architecture Overview

The Table Querying Module follows a **layered, component-based architecture** with **dependency injection** and **plugin support**. The system is designed for maximum modularity, testability, and extensibility.

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
                                        │
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              INFRASTRUCTURE LAYER                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│  LLM Services  │  Database Services  │  File System  │  HTTP Client  │  Logger │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Design Principles

### 1. **Separation of Concerns**
Each layer has distinct responsibilities:
- **Core**: Defines contracts and fundamental types
- **Components**: Implements business logic and orchestration
- **Infrastructure**: Handles external integrations

### 2. **Dependency Inversion**
High-level modules don't depend on low-level modules. Both depend on abstractions (interfaces).

### 3. **Open/Closed Principle**
Components are open for extension but closed for modification through:
- Interface-based design
- Plugin architecture
- Factory pattern

### 4. **Single Responsibility**
Each component has one reason to change:
- Table extraction ≠ Schema generation ≠ Description generation
- LLM client ≠ Database client ≠ Query processor

### 5. **Dependency Injection**
All dependencies are injected through:
- ProcessingContext (DI container)
- Component Registry
- Factory pattern

## Core Layer

### Interfaces (`src/core/interfaces.py`)

Defines contracts for all system components:

```python
# Processing interfaces
DocumentProcessor     # Complete document processing
TableExtractor       # Extract tables from documents
SchemaGenerator      # Generate table schemas
TableDescriptor      # Create table descriptions

# Data access interfaces
DatabaseClient       # Database operations
LLMClient            # LLM service interactions

# Query interfaces
QueryProcessor       # Process user queries
ChatInterface        # Chat-based interactions

# Management interfaces
ComponentManager     # Component lifecycle management
ConfigurationManager # Configuration handling
```

### Types (`src/core/types.py`)

Standardized data structures:

```python
# Core data types
Document            # Input documents
Table               # Extracted tables
Schema              # Table schemas
Description         # Generated descriptions
Query               # User queries
QueryResult         # Query results

# Result containers
ProcessingResult    # Complete processing results
ChatResponse        # Chat interaction results
ValidationResult    # Validation outcomes

# Configuration types
ComponentConfig     # Component configuration
SystemConfig        # System-wide configuration
```

### Registry (`src/core/registry.py`)

Central component registry with:
- **Component registration and discovery**
- **Dependency resolution**
- **Singleton management**
- **Plugin loading**
- **Circular dependency detection**

### Context (`src/core/context.py`)

Dependency injection container providing:
- **Component instance management**
- **Configuration management**
- **Session tracking**
- **Contextual component access**

### Exceptions (`src/core/exceptions.py`)

Hierarchical exception system:
```
TableQueryingError (base)
├── ConfigurationError
├── ValidationError
├── ProcessingError
│   ├── DocumentProcessingError
│   ├── TableExtractionError
│   └── SchemaGenerationError
├── DatabaseError
│   ├── DatabaseConnectionError
│   └── DatabaseQueryError
├── LLMError
│   ├── LLMConnectionError
│   └── LLMRequestError
└── QueryError
    ├── QueryParsingError
    └── QueryExecutionError
```

## Component Layer

### Factories (`src/components/factories.py`)

Create configured component instances:

```python
DocumentProcessorFactory  # Create document processors
LLMClientFactory         # Create LLM clients
DatabaseClientFactory    # Create database clients
QueryProcessorFactory    # Create query processors
ChatInterfaceFactory     # Create chat interfaces
PluginFactory           # Load plugin components
```

**Factory Pattern Benefits**:
- Encapsulates complex object creation
- Handles configuration merging
- Manages dependencies
- Provides consistent interfaces

### Adapters (`src/components/adapters.py`)

Bridge legacy services with new interfaces:

```python
LLMServiceAdapter         # Wraps legacy LLMService
DatabaseServiceAdapter   # Wraps legacy DatabaseService
MultiProviderLLMClient   # Multi-provider with fallback
```

**Adapter Pattern Benefits**:
- Gradual migration from legacy systems
- Maintains backward compatibility
- Reduces code duplication
- Enables incremental refactoring

### Plugin System

Dynamic component loading:
- **Plugin discovery** in configured paths
- **Component registration** through plugins
- **Dependency injection** for plugin components
- **Version management** and compatibility

## Legacy Integration

### Service Layer (`src/services/`)

Existing service implementations:
```
services/
├── llm_service.py          # Abstract LLM service interface
├── database_service.py     # Abstract database service interface
├── service_factory.py      # Service factory and registry
└── implementations/
    ├── bhub_llm_service.py        # BHub implementation
    ├── openai_llm_service.py      # OpenAI implementation
    └── sqlite_database_service.py # SQLite implementation
```

**Integration Strategy**:
1. **Wrap legacy services** with adapters
2. **Gradual component migration**
3. **Interface compatibility** maintenance
4. **Configuration bridging**

## Application Layer

### Document Processing Pipeline

```python
DocumentProcessor
├── TableExtractor      # Extract tables from HTML
├── SchemaGenerator     # Infer table schemas
├── TableDescriptor     # Generate descriptions
└── DatabaseClient      # Store results
```

**Processing Flow**:
1. **Document ingestion** (HTML, Markdown, etc.)
2. **Table extraction** with position tracking
3. **Schema generation** with type inference
4. **Description generation** using LLM
5. **Database storage** with metadata
6. **Result aggregation** and reporting

### Query Processing Pipeline

```python
QueryProcessor
├── QueryAnalyzer      # Analyze query feasibility
├── SQLGenerator       # Convert to SQL
├── DatabaseClient     # Execute queries
└── ResultFormatter    # Format results
```

**Query Flow**:
1. **Natural language parsing**
2. **Intent recognition**
3. **Query feasibility analysis**
4. **SQL generation** with validation
5. **Query execution** with error handling
6. **Result formatting** and presentation

### Chat Interface

```python
ChatInterface
├── MessageProcessor   # Process user messages
├── ContextManager     # Manage conversation context
├── QueryProcessor     # Handle queries
└── ResponseGenerator  # Generate responses
```

**Chat Flow**:
1. **Message processing** and intent detection
2. **Context maintenance** across conversation
3. **Query routing** to appropriate handlers
4. **Response generation** with formatting
5. **Suggestion generation** for follow-ups

## Production Layer

### Configuration Management (`src/production/config.py`)

Comprehensive configuration system:

```python
ProductionConfig
├── DatabaseConfig      # Database configuration
├── LLMConfig          # LLM service configuration
├── SecurityConfig     # Security settings
├── LoggingConfig      # Logging configuration
├── MonitoringConfig   # Monitoring settings
└── ProcessingConfig   # Processing parameters
```

**Configuration Sources** (priority order):
1. **Command line arguments**
2. **Configuration files** (JSON/YAML)
3. **Environment variables**
4. **Default values**

### Deployment (`src/production/deployment.py`)

Production deployment tools:

```python
SystemValidator        # Validate system configuration
├── _check_python_version      # Python compatibility
├── _check_dependencies        # Required packages
├── _check_database_connection # Database connectivity
├── _check_llm_service        # LLM service availability
├── _check_file_permissions   # File system access
├── _check_memory_limits      # Memory requirements
├── _check_network_connectivity # Network access
└── _check_security_settings   # Security validation

DeploymentManager     # Manage deployment process
├── deploy()          # Complete deployment
├── health_check()    # System health monitoring
├── get_system_info() # System information
└── _setup_*()        # Individual setup steps
```

## Data Flow

### Document Processing Data Flow

```
HTML File → Document → Tables → Schemas → Descriptions → Database
     ↓          ↓        ↓        ↓           ↓          ↓
  File I/O → Parsing → Extract → Analyze → LLM Call → Store
```

1. **Input**: HTML file or content
2. **Parsing**: Convert to Document object
3. **Extraction**: Identify and extract tables
4. **Analysis**: Generate schemas with type inference
5. **Description**: Create natural language descriptions
6. **Storage**: Store in database with metadata

### Query Processing Data Flow

```
User Query → Analysis → SQL Generation → Execution → Results
     ↓          ↓           ↓             ↓          ↓
 Parse Text → LLM Call → Generate SQL → Database → Format
```

1. **Input**: Natural language query
2. **Analysis**: Determine feasibility and intent
3. **Generation**: Convert to SQL query
4. **Execution**: Run against database
5. **Formatting**: Present results to user

## Component Interactions

### Dependency Graph

```
DocumentProcessor
├── depends on: TableExtractor, SchemaGenerator, TableDescriptor, DatabaseClient
│
QueryProcessor
├── depends on: LLMClient, DatabaseClient
│
ChatInterface
├── depends on: QueryProcessor, SessionManager
│
LLMClient (implementations)
├── BHubLLMClient
├── OpenAILLMClient
└── MultiProviderLLMClient
│
DatabaseClient (implementations)
├── SQLiteDatabaseClient
└── PostgreSQLDatabaseClient
```

### Communication Patterns

1. **Synchronous**: Direct method calls for most operations
2. **Asynchronous**: Optional for long-running operations
3. **Event-driven**: Processing events and hooks
4. **Request-response**: API interactions
5. **Publish-subscribe**: Monitoring and metrics

## Configuration Architecture

### Hierarchical Configuration

```
Global Settings
├── Component Configurations
│   ├── LLM Client Config
│   ├── Database Client Config
│   └── Processing Config
└── Environment-specific Overrides
    ├── Development
    ├── Testing
    └── Production
```

### Configuration Merging Strategy

1. **Load defaults** from code
2. **Apply configuration file** settings
3. **Override with environment variables**
4. **Apply command-line arguments**
5. **Validate final configuration**

## Error Handling Strategy

### Exception Hierarchy

All exceptions inherit from `TableQueryingError` with:
- **Structured error information**
- **Error codes** for programmatic handling
- **Contextual details** for debugging
- **Cause chaining** for root cause analysis

### Error Handling Patterns

1. **Fail fast** for configuration errors
2. **Graceful degradation** for service failures
3. **Retry logic** with exponential backoff
4. **Circuit breaker** for external services
5. **Comprehensive logging** for debugging

## Testing Architecture

### Test Categories

1. **Unit Tests**: Individual component testing
2. **Integration Tests**: Component interaction testing
3. **System Tests**: End-to-end workflow testing
4. **Performance Tests**: Load and stress testing
5. **Security Tests**: Security vulnerability testing

### Test Structure

```
tests/
├── unit/
│   ├── test_core/
│   ├── test_components/
│   └── test_services/
├── integration/
│   ├── test_pipeline/
│   └── test_api/
├── system/
│   └── test_workflows/
└── fixtures/
    ├── sample_documents/
    └── test_configs/
```

## Security Architecture

### Security Layers

1. **Authentication**: JWT-based user authentication
2. **Authorization**: Role-based access control
3. **Input Validation**: Comprehensive input sanitization
4. **Output Encoding**: Prevent injection attacks
5. **Transport Security**: HTTPS and encrypted connections
6. **Data Protection**: Encryption at rest and in transit

### Security Controls

- **API Key Management**: Secure storage and rotation
- **Rate Limiting**: Prevent abuse and DoS
- **CORS Configuration**: Controlled cross-origin access
- **Security Headers**: Comprehensive HTTP security headers
- **Audit Logging**: Security event logging

## Monitoring and Observability

### Metrics Collection

- **Performance Metrics**: Response times, throughput
- **Error Metrics**: Error rates, failure types
- **Resource Metrics**: Memory, CPU, disk usage
- **Business Metrics**: Documents processed, queries executed

### Logging Strategy

- **Structured Logging**: JSON-formatted logs
- **Correlation IDs**: Request tracking across components
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Log Aggregation**: Centralized log collection

### Health Monitoring

- **Component Health**: Individual component status
- **System Health**: Overall system status
- **External Dependencies**: Third-party service status
- **Performance Health**: Performance degradation detection

## Scalability Considerations

### Horizontal Scaling

- **Stateless Components**: Enable load balancing
- **Database Scaling**: Read replicas and sharding
- **Cache Layer**: Redis/Memcached for performance
- **Message Queues**: Asynchronous processing

### Performance Optimization

- **Connection Pooling**: Database and HTTP connections
- **Caching Strategies**: Multi-level caching
- **Batch Processing**: Reduce API calls
- **Resource Limits**: Memory and CPU constraints

## Extension Points

### Plugin System

- **Component Plugins**: Custom implementations
- **Processing Plugins**: Custom processing steps
- **Storage Plugins**: Alternative storage backends
- **UI Plugins**: Custom user interfaces

### API Extensions

- **Custom Endpoints**: Domain-specific APIs
- **Webhook Support**: Event-driven integrations
- **Batch APIs**: Bulk operations
- **Streaming APIs**: Real-time data processing

## Migration Strategy

### Legacy System Integration

1. **Assessment Phase**: Analyze existing system
2. **Adapter Creation**: Wrap legacy components
3. **Gradual Migration**: Component-by-component replacement
4. **Validation Phase**: Ensure feature parity
5. **Cutover Phase**: Switch to new system

### Data Migration

1. **Schema Mapping**: Map legacy to new schema
2. **ETL Process**: Extract, transform, load data
3. **Validation**: Verify data integrity
4. **Rollback Plan**: Handle migration failures

This architecture provides a solid foundation for a scalable, maintainable, and extensible table querying system that can evolve with changing requirements while maintaining stability and performance.