# Table LLM Querying System

A powerful Python system for extracting HTML tables, processing them with LLM descriptions, and enabling natural language queries over the data.

## 🚀 Features

- **HTML Table Extraction** - Automatically extract and process tables from HTML documents
- **Schema Inference** - Smart type detection and schema generation
- **LLM Descriptions** - Generate natural language descriptions using OpenAI
- **Natural Language Queries** - Chat with your table data using plain English
- **Multiple Export Formats** - Save results as CSV, JSON, or formatted text
- **Modular Architecture** - Clean interfaces for easy extension

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/your-username/TableLLMQuerying.git
cd TableLLMQuerying/table_querying_module

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

## ⚙️ Configuration

1. **Set your OpenAI API key:**
```bash
export YOUR_API_KEY="your_openai_api_key_here"
```

2. **Or create a local .env file:**
```
YOUR_API_KEY=your_openai_api_key_here
TABLE_MODEL_ID=gpt-3.5-turbo
```

## 🎯 Quick Start

### Process HTML Tables
```bash
# Process a single HTML file
python -m src.table_querying.main document.html

# Process with configuration
python -m src.table_querying.main document.html --config config/config_default.json

# Process directory of files
python -m src.table_querying.main --directory /path/to/html/files
```

### Query Your Tables
```bash
# Interactive chat mode
python -m src.chatting_module.main --db table_querying.db

# Save query results
python -m src.chatting_module.main --db table_querying.db --save-results --export-format json

# Single query
python -m src.chatting_module.main --db table_querying.db --query "Show me all tables"
```

## 🏗️ Architecture

### Core Components
- **TableProcessor** - Main orchestrator for the extraction pipeline
- **TableExtractor** - HTML table extraction and markdown conversion
- **SchemaProcessor** - Type inference and schema generation  
- **TableSummarizer** - LLM-powered description generation
- **ChatInterface** - Natural language query interface
- **ResultExporter** - Multi-format result export

### LLM Providers
The system supports pluggable LLM providers:
- **OpenAI** (default) - Standard industry provider
- **Custom providers** - Extend via service factory pattern

## 📊 Output Files

Processing generates:
- `*_processed.md` - Documents with table descriptions
- `*_schemas.json` - Extracted table schemas
- `*_descriptions.json` - LLM-generated descriptions
- `*.db` - SQLite database with table data

## 🤖 Natural Language Queries

Ask questions like:
- "Show me all tables from the minecraft files"
- "Count how many rows are in each table"
- "Find tables with more than 10 columns"
- "What's the structure of the inventory table?"

## 🔧 Configuration Options

Key configuration parameters:
- `llm_service_type` - LLM provider ("openai")
- `llm_model_id` - Model to use ("gpt-3.5-turbo")
- `context_hint` - Context for better descriptions
- `db_path` - Database file location
- `output_dir` - Output directory for results

## 🧪 Testing

```bash
# Run integration tests
python tests/test_module.py

# Test with sample file
python -m src.table_querying.main config/sample_table.html
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/awesome-feature`)
3. Commit your changes (`git commit -am 'Add awesome feature'`)
4. Push to the branch (`git push origin feature/awesome-feature`)
5. Open a Pull Request

## 📋 Requirements

- Python 3.8+
- OpenAI API key
- Dependencies in `requirements.txt`

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support

- Create an issue for bugs or feature requests
- Check existing issues before creating new ones
- Provide detailed information for faster resolution

## 🔮 Roadmap

- [ ] Support for PDF table extraction
- [ ] Additional LLM provider integrations  
- [ ] Web interface for easier interaction
- [ ] Batch processing optimizations
- [ ] Advanced query capabilities