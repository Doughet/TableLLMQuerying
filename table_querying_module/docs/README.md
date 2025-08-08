# Table Querying Module

A self-contained application for extracting, processing, and querying tables from HTML documents. This module extracts tables from documents, creates flattened schemas, generates LLM summaries, stores them in a database, and replaces table content with descriptions.

## Features

- **Table Extraction**: Extract HTML tables from documents and convert to markdown
- **Schema Processing**: Generate flattened schemas with automatic type inference
- **LLM Summarization**: Generate natural language descriptions of tables using AI
- **Database Storage**: Store tables, schemas, and descriptions in SQLite database
- **Document Processing**: Replace tables in documents with their descriptions
- **CLI Interface**: Easy-to-use command-line interface
- **Configurable**: Flexible configuration options for different use cases

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Make sure you have an API key for the LLM service (BHub/Olympia):
```bash
export YOUR_API_KEY="your_api_key_here"
```

## Quick Start

### Process a Single HTML Document

```bash
python -m table_querying_module.main document.html
```

### Process All HTML Files in a Directory

```bash
python -m table_querying_module.main --directory /path/to/html/files
```

### Use Minecraft Wiki Optimized Settings

```bash
python -m table_querying_module.main document.html --preset minecraft-wiki
```

### Process with Custom Configuration

```bash
python -m table_querying_module.main document.html --config my_config.json
```

## Module Components

### 1. TableExtractor
Extracts HTML tables from documents and converts them to markdown format.

```python
from table_querying_module import TableExtractor

extractor = TableExtractor()
extraction_data = extractor.extract_from_file("document.html")
```

### 2. SchemaProcessor
Creates flattened schemas from HTML tables with automatic type inference.

```python
from table_querying_module import SchemaProcessor

processor = SchemaProcessor()
schemas = processor.extract_schemas_from_tables(html_tables)
```

### 3. TableSummarizer
Generates LLM descriptions of tables based on their schemas.

```python
from table_querying_module import TableSummarizer

summarizer = TableSummarizer(api_key="your_key")
descriptions = summarizer.describe_multiple_tables(schemas)
```

### 4. TableDatabase
Manages storage and querying of table data and metadata.

```python
from table_querying_module import TableDatabase

db = TableDatabase("tables.db")
session_id = db.start_processing_session("document.html")
db.store_multiple_tables(schemas, descriptions, session_id, "document.html")
```

### 5. DocumentProcessor
Handles document processing and table replacement.

```python
from table_querying_module import DocumentProcessor

processor = DocumentProcessor()
modified_chunks, info = processor.replace_tables_with_descriptions(
    chunks, table_positions, descriptions
)
```

### 6. TableProcessor (Main Orchestrator)
Coordinates all components in a complete workflow.

```python
from table_querying_module import TableProcessor

processor = TableProcessor(config)
results = processor.process_document("document.html")
```

## Configuration

### Using Configuration Files

Create a configuration template:
```bash
python -m table_querying_module.main --create-config-template
```

Load from configuration file:
```bash
python -m table_querying_module.main document.html --config config.json
```

### Configuration Options

```json
{
  "api_key": "your_api_key",
  "model_id": "mistral-small",
  "context_hint": "Minecraft Wiki",
  "db_path": "table_querying.db",
  "output_dir": "table_querying_outputs",
  "save_outputs": true,
  "clear_database_on_start": false
}
```

### Environment Variables

- `YOUR_API_KEY`: BHub API key
- `TABLE_MODEL_ID`: LLM model ID
- `TABLE_DB_PATH`: Database file path
- `TABLE_OUTPUT_DIR`: Output directory
- `TABLE_CONTEXT_HINT`: Context hint for descriptions

## Command Line Options

```
usage: main.py [-h] [--directory DIRECTORY | --create-config-template] 
               [--config CONFIG] [--preset {default,minecraft-wiki}]
               [--api-key API_KEY] [--model-id MODEL_ID] 
               [--context-hint CONTEXT_HINT] [--output-dir OUTPUT_DIR]
               [--db-path DB_PATH] [--clear-database] [--no-save] 
               [--recursive] [--verbose] [--version]
               [html_file]

Options:
  html_file                   HTML file to process
  --directory, -d             Directory containing HTML files
  --config, -c               Path to JSON configuration file
  --preset, -p               Predefined configuration preset
  --api-key                  BHub API key for LLM processing
  --model-id                 LLM model ID to use
  --context-hint             Context hint for better descriptions
  --output-dir               Directory for output files
  --db-path                  Path to SQLite database file
  --clear-database           Clear database before processing
  --no-save                  Do not save output files
  --recursive, -r            Search subdirectories recursively
  --verbose, -v              Enable verbose logging
```

## Output Files

When processing is complete, the module generates several output files:

- `{document}_processed.md`: Document with tables replaced by descriptions
- `{document}_original.md`: Original markdown version
- `{document}_schemas.json`: Extracted table schemas
- `{document}_descriptions.json`: LLM-generated descriptions
- `{document}_replacement_report.txt`: Detailed replacement report

## Database Schema

The module uses SQLite database with the following tables:

- **tables**: Table metadata and descriptions
- **table_data**: Actual table row data
- **processing_sessions**: Processing session tracking

## Example Workflow

1. **Extract**: HTML tables → structured data
2. **Process**: Generate flattened schemas with type inference
3. **Describe**: Use LLM to create natural language descriptions
4. **Store**: Save everything in SQLite database
5. **Replace**: Create new document with table descriptions
6. **Output**: Save processed files and reports

## Testing

Run the test suite:

```bash
python table_querying_module/test_module.py
```

This will test all components and run a full integration test with sample data.

## Use Cases

- **Document Processing**: Clean up documents by replacing complex tables with summaries
- **Data Analysis**: Extract and analyze tabular data from HTML documents
- **Content Migration**: Convert table-heavy documents to more readable formats
- **Knowledge Extraction**: Build databases of structured information from web content
- **Research**: Process academic papers, reports, or wiki pages with tables

## Troubleshooting

### Common Issues

1. **API Key Error**: Make sure `YOUR_API_KEY` environment variable is set
2. **Import Errors**: Install required dependencies with `pip install -r requirements.txt`
3. **File Not Found**: Ensure HTML file paths are correct and files exist
4. **Database Locked**: Close other connections to the database file

### Debug Mode

Use verbose logging for debugging:
```bash
python -m table_querying_module.main document.html --verbose
```

## Integration with CraftGraphRag

This module is designed to work seamlessly with the existing CraftGraphRag pipeline:

```python
# Use in existing pipeline
from table_querying_module import TableProcessor

processor = TableProcessor(config)
results = processor.process_document(html_file)

# Access processed content
processed_markdown = results['processed_content']
table_descriptions = results['descriptions']
```

## License

This module is part of the CraftGraphRag project and inherits its license terms.