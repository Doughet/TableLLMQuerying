# Table Querying Module

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A powerful, self-contained Python module for extracting, processing, and querying tables from HTML documents. This module combines table extraction, schema generation, LLM-powered summarization, database storage, and intelligent document processing into a single, easy-to-use package.

## 🚀 Features

- **🔍 Smart Table Extraction**: Extract HTML tables from documents with robust error handling
- **📊 Schema Processing**: Generate flattened schemas with automatic type inference
- **🤖 LLM Summarization**: Create natural language descriptions using AI models
- **💾 Database Storage**: Store tables and metadata in SQLite with full querying capability
- **📝 Document Processing**: Replace tables with descriptions while maintaining document structure
- **⚙️ Configurable**: Flexible configuration options for different use cases
- **🔧 CLI Interface**: Easy-to-use command-line interface
- **📦 Self-Contained**: No external dependencies on other projects

## 📦 Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/your-username/table-querying-module.git
cd table-querying-module

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### Using pip (when published)

```bash
pip install table-querying-module
```

## 🏁 Quick Start

### 1. Set up your API key

```bash
export YOUR_API_KEY="your_api_key_here"
```

### 2. Process a document

```python
from table_querying_module import TableProcessor
from table_querying_module.config import create_default_config

# Create configuration
config = create_default_config()
config.output_dir = "my_outputs"

# Initialize processor
processor = TableProcessor(config.to_dict())

# Process document
results = processor.process_document("document_with_tables.html")

# Print summary
processor.print_processing_summary(results)
```

### 3. Using the CLI

```bash
# Process a single document
python -m main document.html

# Process with custom configuration
python main.py document.html --config examples/config_default.json

# Process all HTML files in a directory
python main.py --directory /path/to/html/files

# Use preset for specific domains
python main.py document.html --preset minecraft-wiki --context-hint "Gaming Wiki"
```

## 📚 Examples

### Basic Usage

```python
from table_querying_module import TableProcessor

# Simple processing
processor = TableProcessor()
results = processor.process_document("sample.html")

if results['success']:
    print(f"Processed {results['statistics']['html_tables']} tables")
    print(f"Generated {results['statistics']['successful_descriptions']} descriptions")
```

### Advanced Configuration

```python
from table_querying_module.config import TableProcessingConfig
from table_querying_module import TableProcessor

# Custom configuration
config = TableProcessingConfig(
    api_key="your-key",
    model_id="mistral-small",
    context_hint="Scientific Papers",
    db_path="research_tables.db",
    output_dir="research_outputs",
    save_outputs=True
)

processor = TableProcessor(config.to_dict())
results = processor.process_document("research_paper.html")
```

### Batch Processing

```python
import glob
from table_querying_module import TableProcessor

processor = TableProcessor()

# Process all HTML files
html_files = glob.glob("documents/*.html")
for html_file in html_files:
    results = processor.process_document(html_file)
    if results['success']:
        print(f"✅ {html_file}: {results['statistics']['successful_descriptions']} descriptions")
    else:
        print(f"❌ {html_file}: {results.get('error', 'Unknown error')}")
```

## 🔧 Configuration

### Configuration Methods

1. **Environment Variables**:
   ```bash
   export YOUR_API_KEY="your_key"
   export TABLE_MODEL_ID="mistral-small"
   export TABLE_OUTPUT_DIR="outputs"
   ```

2. **JSON Configuration**:
   ```json
   {
     "api_key": "your_key",
     "model_id": "mistral-small",
     "context_hint": "Domain context",
     "db_path": "tables.db",
     "output_dir": "outputs"
   }
   ```

3. **Python Configuration**:
   ```python
   from table_querying_module.config import TableProcessingConfig
   
   config = TableProcessingConfig(
       api_key="your_key",
       context_hint="Your domain"
   )
   ```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `api_key` | str | None | API key for LLM service |
| `model_id` | str | "mistral-small" | LLM model to use |
| `context_hint` | str | None | Domain context for better descriptions |
| `db_path` | str | "table_querying.db" | SQLite database path |
| `output_dir` | str | "table_querying_outputs" | Output directory |
| `save_outputs` | bool | True | Save output files |
| `clear_database_on_start` | bool | False | Clear database before processing |

## 📊 Workflow

The module follows a comprehensive workflow:

1. **📄 Document Input**: Load HTML document
2. **🔍 Table Extraction**: Extract HTML tables and convert to markdown
3. **📋 Schema Generation**: Create flattened schemas with type inference
4. **🤖 LLM Processing**: Generate natural language descriptions
5. **💾 Database Storage**: Store tables, schemas, and descriptions
6. **📝 Document Processing**: Replace tables with descriptions
7. **📁 Output Generation**: Save all results and reports

## 📁 Output Files

For each processed document, the module generates:

- `{document}_processed.md`: Document with table descriptions
- `{document}_original.md`: Original markdown version
- `{document}_schemas.json`: Table schemas with metadata
- `{document}_descriptions.json`: LLM-generated descriptions
- `{document}_replacement_report.txt`: Detailed processing report

## 🗃️ Database Schema

The SQLite database includes:

- **tables**: Table metadata and descriptions
- **table_data**: Actual table row data
- **processing_sessions**: Session tracking and history

### Query Examples

```python
# Get database summary
summary = processor.get_database_summary()
print(f"Total tables: {summary['total_tables']}")

# Query tables from specific document
tables = processor.query_tables_by_source("document.html")
for table in tables:
    print(f"Table {table['table_id']}: {table['description']}")
```

## 🧪 Testing

### Run Tests

```bash
# Run the test suite
python test_module.py

# Run with pytest (if installed)
pytest test_module.py -v
```

### Test with Sample Data

```bash
# Use the provided sample
python main.py examples/sample_table.html --output-dir test_outputs
```

## 🔗 API Reference

### Core Classes

#### TableProcessor
Main orchestrator class that coordinates the entire workflow.

```python
processor = TableProcessor(config_dict)
results = processor.process_document(html_file)
processor.print_processing_summary(results)
```

#### TableExtractor
Handles HTML table extraction and markdown conversion.

```python
from table_querying_module import TableExtractor
extractor = TableExtractor()
data = extractor.extract_from_file("document.html")
```

#### SchemaProcessor
Creates flattened schemas with type inference.

```python
from table_querying_module import SchemaProcessor
processor = SchemaProcessor()
schemas = processor.extract_schemas_from_tables(html_tables)
```

#### TableSummarizer
Generates LLM descriptions of tables.

```python
from table_querying_module import TableSummarizer
summarizer = TableSummarizer(api_key="key")
descriptions = summarizer.describe_multiple_tables(schemas)
```

#### TableDatabase
Manages SQLite database operations.

```python
from table_querying_module import TableDatabase
db = TableDatabase("tables.db")
session_id = db.start_processing_session("document.html")
```

## 🎯 Use Cases

- **📚 Academic Research**: Process research papers with complex tables
- **📊 Data Analysis**: Extract and analyze tabular data from web content
- **📝 Content Migration**: Convert table-heavy documents to readable formats
- **🔍 Information Extraction**: Build structured databases from HTML documents
- **🤖 AI Training**: Create datasets from web-scraped tables
- **📖 Documentation**: Generate summaries of technical documentation

## 🛠️ Development

### Project Structure

```
table_querying_module/
├── __init__.py              # Package initialization
├── table_extractor.py       # HTML table extraction
├── schema_processor.py      # Schema generation
├── table_summarizer.py      # LLM summarization
├── table_database.py        # Database operations
├── document_processor.py    # Document processing
├── table_processor.py       # Main orchestrator
├── config.py               # Configuration management
├── main.py                 # CLI interface
├── setup.py               # Package setup
├── requirements.txt       # Dependencies
├── examples/             # Sample files and configs
└── README.md            # This file
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run the test suite (`python test_module.py`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Support

- **🐛 Bug Reports**: [GitHub Issues](https://github.com/your-username/table-querying-module/issues)
- **💬 Discussions**: [GitHub Discussions](https://github.com/your-username/table-querying-module/discussions)
- **📖 Documentation**: [README](https://github.com/your-username/table-querying-module#readme)

## 🙏 Acknowledgments

- Built for the CraftGraphRag project
- Uses Docling for HTML to Markdown conversion
- Powered by Mistral AI models via BHub API
- Built with pandas for data processing

## 🔄 Version History

- **v1.0.0**: Initial release with full functionality
  - Table extraction and schema processing
  - LLM-powered summarization
  - Database storage and querying
  - Document processing and CLI interface

---

**Made with ❤️ for better document processing**