# Table Querying Module - Workflow Summary

## Overview

This system provides a complete pipeline for extracting HTML tables, processing them with LLM-generated descriptions, storing them in a database, and enabling natural language queries against the processed data.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    TABLE PROCESSING PIPELINE                    │
└─────────────────────────────────────────────────────────────────┘
HTML Files → Extract → Schema → Summarize → Database → Transform
     ↓         ↓        ↓         ↓          ↓          ↓
  Raw HTML   Tables   Types    LLM Desc   SQLite    Modified MD

┌─────────────────────────────────────────────────────────────────┐
│                     CHATTING INTERFACE                         │
└─────────────────────────────────────────────────────────────────┘
User Query → Analyze → Generate SQL → Execute → Return Results
     ↓         ↓          ↓           ↓          ↓
  Natural   Feasible?   SQL Query   Database   Formatted
  Language              with Types   Results    Response
```

## Main Workflow Components

### 1. Table Processing Pipeline (5 Steps)

#### Step 1: Table Extraction
- **File**: `table_extractor.py`
- **Class**: `TableExtractor`
- **Purpose**: Extract HTML tables and convert documents to markdown
- **Key Functions**:
  - `extract_from_file(html_file_path)` - Process complete HTML file
  - `extract_html_tables(soup)` - Extract table elements from BeautifulSoup
  - `identify_table_chunks(markdown_content)` - Locate table positions in markdown

#### Step 2: Schema Processing  
- **File**: `schema_processor.py`
- **Class**: `SchemaProcessor`
- **Purpose**: Generate structured schemas with type inference
- **Key Functions**:
  - `extract_schemas_from_tables(html_tables)` - Batch schema extraction
  - `extract_schema_from_html_table(table_soup)` - Individual table schema
  - `_infer_type_from_values(values)` - Automatic type detection (string, integer, float)

#### Step 3: Table Summarization
- **File**: `table_summarizer.py` 
- **Class**: `TableSummarizer`
- **Purpose**: Generate LLM descriptions of table content and purpose
- **Key Functions**:
  - `describe_multiple_tables(schemas, context_hint)` - Batch description generation
  - `describe_table_from_schema(schema, context_hint)` - Single table description
  - `_build_table_description_prompt(schema)` - Create LLM prompts

#### Step 4: Database Storage
- **File**: `table_database.py`
- **Class**: `TableDatabase` 
- **Purpose**: Store processed data in SQLite database
- **Key Functions**:
  - `store_multiple_tables(tables_data, session_id)` - Batch storage
  - `store_table_data(table_data, session_id)` - Individual table storage
  - `query_tables_by_source(source_file)` - Retrieve by source file
  - `get_database_summary()` - Database statistics

#### Step 5: Document Processing
- **File**: `document_processor.py`
- **Class**: `DocumentProcessor`
- **Purpose**: Replace tables in documents with LLM descriptions  
- **Key Functions**:
  - `create_processed_document(chunks, descriptions)` - Assemble final document
  - `replace_tables_with_descriptions(chunks, descriptions)` - Replace table chunks
  - `create_replacement_report(chunks, descriptions)` - Detailed replacement log

### 2. Chatting Interface (3 Steps)

#### Step 1: Query Analysis
- **File**: `query_analyzer.py`
- **Class**: `QueryAnalyzer`
- **Purpose**: Determine if queries can be fulfilled with available data
- **Key Functions**:
  - `analyze_query(user_query, available_tables)` - Main analysis entry point
  - `_build_tables_context(available_tables)` - Create database context
  - `_parse_analysis_response(response)` - Parse LLM JSON responses

#### Step 2: SQL Generation  
- **File**: `sql_generator.py`
- **Class**: `SQLGenerator`
- **Purpose**: Convert natural language to SQL with retry logic
- **Key Functions**:
  - `generate_sql(user_query, database_schema, db_path)` - Main generation (5 retries)
  - `_validate_sql(sql_query, db_path)` - SQL syntax validation  
  - `_build_schema_context(database_schema)` - Database schema context

#### Step 3: Chat Interface
- **File**: `chat_interface.py`
- **Class**: `ChatInterface` 
- **Purpose**: Orchestrate complete query processing
- **Key Functions**:
  - `chat(user_query)` - Main entry point for natural language queries
  - `execute_sql_query(sql_query)` - Direct SQL execution (testing)
  - `get_database_summary()` - Database statistics
  - `list_available_tables()` - Table enumeration

## Main Entry Points

### CLI Interfaces

#### Table Processing CLI
- **File**: `main.py`
- **Usage**: `python -m table_querying_module.main [file/directory]`
- **Key Functions**:
  - `process_single_document(file_path, config)` - Single file processing
  - `process_multiple_documents(directory, config)` - Batch processing
  - `main()` - CLI argument parsing and execution

#### Chatting CLI  
- **File**: `src/chatting_module/main.py`
- **Usage**: `python -m table_querying_module.src.chatting_module.main`
- **Key Functions**:
  - `interactive_mode(chat_interface)` - Continuous chat session
  - `single_query_mode(chat_interface, query)` - One-shot query

#### Full Pipeline
- **File**: `full_pipeline.py` 
- **Class**: `FullPipeline`
- **Purpose**: Complete workflow with smart processing detection
- **Key Functions**:
  - `run_pipeline(html_file_path)` - Complete workflow execution
  - `process_single_file(html_file_path)` - Processing with duplicate detection
  - `start_interactive_chat()` - Interactive chat session  
  - `_dump_database_content()` - Complete database inspection

### Programmatic Interfaces

#### Main Orchestrator
- **File**: `table_processor.py`
- **Class**: `TableProcessor`
- **Key Functions**:
  - `process_document(html_file_path)` - Complete processing workflow
  - `print_processing_summary()` - Formatted results display

## Database Schema

### Tables Structure
```sql
-- Table metadata and descriptions
CREATE TABLE tables (
    id INTEGER PRIMARY KEY,
    table_id TEXT UNIQUE,
    source_file TEXT,
    rows INTEGER,
    columns INTEGER, 
    column_names TEXT,  -- JSON array
    column_types TEXT,  -- JSON object with type mapping
    description TEXT,   -- LLM-generated description
    created_at TIMESTAMP
);

-- Actual table row data
CREATE TABLE table_data (
    id INTEGER PRIMARY KEY,
    table_id TEXT,
    row_index INTEGER,
    row_data TEXT,      -- JSON object with column values
    created_at TIMESTAMP
);

-- Processing session tracking  
CREATE TABLE processing_sessions (
    id INTEGER PRIMARY KEY,
    session_id TEXT UNIQUE,
    source_file TEXT,
    total_tables INTEGER,
    successful_tables INTEGER,
    created_at TIMESTAMP
);
```

## Configuration System

### Configuration Management
- **File**: `config.py`
- **Class**: `TableProcessingConfig`
- **Key Functions**:
  - `create_default_config()` - Default settings
  - `create_config_for_minecraft_wiki()` - Specialized preset
  - `load_config_from_env()` - Environment variable loading

### Key Configuration Options
```python
@dataclass
class TableProcessingConfig:
    api_key: str                    # BHub API key (required)
    model_id: str = "mistral-small" # LLM model selection
    context_hint: str = ""          # Context for better descriptions
    db_path: str                    # SQLite database file path
    output_dir: str                 # Output directory for files
    clear_database: bool = False    # Clear database before processing
```

## Special Chat Commands

When using the interactive chat interface:

- **`help`** - Show available commands
- **`summary`** - Database statistics and overview
- **`tables`** - List all available tables with details
- **`dump`** - Show complete database content (all tables and data)
- **`quit`** - Exit chat session

## Example Usage Workflows

### Complete Processing + Chat
```bash
# Process HTML file and start chat
python full_pipeline.py document.html

# Batch process directory
python -m table_querying_module.main --directory docs/ --recursive

# Use custom configuration  
python -m table_querying_module.main doc.html --config my_config.json
```

### Chat-Only Mode
```bash
# Interactive chat session
python -m table_querying_module.src.chatting_module.main --interactive

# Single query
python -m table_querying_module.src.chatting_module.main --query "show all players with level > 10"
```

## Output Files Generated

- `*_processed.md` - Document with tables replaced by descriptions
- `*_original.md` - Original markdown conversion
- `*_schemas.json` - Extracted table schemas  
- `*_descriptions.json` - LLM-generated descriptions
- `*_replacement_report.txt` - Detailed replacement report
- SQLite database with all processed data

## Key Features

1. **Smart Processing Detection** - Avoids reprocessing already stored tables
2. **Retry Logic** - SQL generation with up to 5 retry attempts and validation
3. **Type-Aware Queries** - Proper type casting for JSON data queries
4. **Comprehensive Logging** - Full logging without truncation
5. **Modular Design** - Each component can be used independently
6. **Multiple Interfaces** - CLI, programmatic, and interactive modes
7. **Robust Error Handling** - Graceful failure handling throughout pipeline