# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build and Development Commands

This is a Python module for extracting, processing, and querying tables from HTML documents. Key commands:

```bash
# Install dependencies
pip install -r table_querying_module/requirements.txt

# Run main processing
python -m table_querying_module.main document.html

# Process directory of HTML files
python -m table_querying_module.main --directory /path/to/html/files

# Run tests
python table_querying_module/test_module.py

# Install as package (development)
cd table_querying_module && pip install -e .

# Create configuration template
python -m table_querying_module.main --create-config-template
```

## Project Architecture

This is a self-contained table processing pipeline that extracts HTML tables, processes them with LLM descriptions, and stores them in a database. The architecture follows a pipeline pattern with distinct processing stages:

### Core Pipeline Flow
1. **TableExtractor** - Extracts HTML tables and converts document to markdown chunks
2. **SchemaProcessor** - Generates flattened schemas with type inference from HTML tables
3. **TableSummarizer** - Uses LLM (BHub API) to generate natural language descriptions
4. **TableDatabase** - Stores tables, schemas, and descriptions in SQLite database
5. **DocumentProcessor** - Replaces tables in documents with their LLM descriptions

### Main Orchestrator
- **TableProcessor** - Main class that coordinates the complete workflow and provides high-level interface

### Key Extension Points
The system is designed for modularity - each component can be used independently:
- Individual processors can be instantiated and used separately
- Configuration system allows for different processing presets (default, minecraft-wiki)
- Database querying supports filtering by source files and processing sessions

### Configuration System
- **TableProcessingConfig** dataclass with environment variable support
- JSON-based configuration files with preset configurations
- Environment variables: `YOUR_API_KEY`, `TABLE_MODEL_ID`, `TABLE_DB_PATH`, etc.

## Package Structure

```
table_querying_module/
├── main.py              # CLI interface and entry point
├── table_processor.py   # Main orchestrator class
├── config.py            # Configuration management
├── table_extractor.py   # HTML table extraction
├── schema_processor.py  # Schema generation
├── table_summarizer.py  # LLM description generation
├── table_database.py    # SQLite database operations
├── document_processor.py # Document processing and table replacement
├── test_module.py       # Integration tests
├── demo.py              # Demo script
└── examples/            # Configuration examples
```

## Dependencies and Environment

- **docling**: Document processing and HTML parsing
- **beautifulsoup4, lxml**: HTML parsing
- **pandas, numpy**: Data processing
- **requests**: HTTP requests for LLM API
- **pydantic**: Configuration validation
- **SQLite3**: Database (built-in to Python)

## Configuration

The system supports multiple configuration methods:
1. **Command line arguments** - Override any config option
2. **JSON configuration files** - Persistent configuration
3. **Environment variables** - For API keys and paths
4. **Presets** - Predefined configurations (default, minecraft-wiki)

Critical configuration:
- `api_key`: OpenAI API key for LLM processing (required)
- `model_id`: LLM model (default: "gpt-3.5-turbo")
- `llm_service_type`: LLM service provider (default: "openai")
- `context_hint`: Context for better table descriptions
- `db_path`: SQLite database file path
- `output_dir`: Directory for generated output files

## Database Schema

SQLite database with:
- **tables**: Table metadata and LLM descriptions
- **table_data**: Actual table row data
- **processing_sessions**: Processing session tracking

## Output Files

Processing generates:
- `*_processed.md`: Document with tables replaced by descriptions
- `*_original.md`: Original markdown version
- `*_schemas.json`: Extracted table schemas
- `*_descriptions.json`: LLM-generated descriptions
- `*_replacement_report.txt`: Detailed replacement report

## Testing

Run integration tests: `python table_querying_module/test_module.py`

The test suite processes sample HTML files and validates the complete workflow.

## CLI Usage Patterns

```bash
# Basic processing
python -m table_querying_module.main document.html

# Batch processing with recursive search
python -m table_querying_module.main --directory docs/ --recursive

# Custom configuration
python -m table_querying_module.main doc.html --config my_config.json

# Minecraft Wiki optimized
python -m table_querying_module.main doc.html --preset minecraft-wiki

# Clear database and save outputs
python -m table_querying_module.main doc.html --clear-database --output-dir results/
```