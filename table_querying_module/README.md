# Table Querying Module

A self-contained Python module for extracting, processing, and querying tables from HTML documents using LLM-powered descriptions.

## 📁 Project Structure

```
table_querying_module/
├── src/table_querying/          # Core source code
│   ├── __init__.py              # Package initialization and exports
│   ├── main.py                  # CLI interface and entry point
│   ├── table_processor.py       # Main orchestrator class
│   ├── config.py                # Configuration management
│   ├── table_extractor.py       # HTML table extraction
│   ├── schema_processor.py      # Schema generation with type inference
│   ├── table_summarizer.py      # LLM description generation
│   ├── table_database.py        # SQLite database operations
│   └── document_processor.py    # Document processing and table replacement
│
├── src/chatting_module/         # Natural language query interface
│   ├── __init__.py              # Package initialization and exports
│   ├── main.py                  # CLI interface for chatting
│   ├── chat_interface.py        # Main chat orchestrator
│   ├── query_analyzer.py        # LLM query analysis
│   ├── sql_generator.py         # SQL generation with retry logic
│   ├── demo.py                  # Demo script
│   └── test_chatting.py         # Integration tests
│
├── config/                      # Configuration files and examples
│   ├── config_default.json      # Default configuration template
│   ├── config_minecraft_wiki.json # Minecraft Wiki optimized settings
│   └── sample_table.html        # Sample HTML file for testing
│
├── tests/                       # Test files
│   └── test_module.py           # Integration tests
│
├── docs/                        # Documentation
│   ├── README.md                # Main documentation
│   ├── README_STANDALONE.md     # Standalone version info
│   └── STANDALONE_PREPARATION_SUMMARY.md # Development notes
│
├── requirements.txt             # Python dependencies
├── setup.py                     # Package installation script
├── __init__.py                  # Package root
├── demo.py                      # Demo script
├── LICENSE                      # License file
└── MANIFEST.in                  # Package manifest
```

## 🚀 Quick Start

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Install as package (development mode)
pip install -e .
```

### Basic Usage

#### 1. Process Tables from HTML
```bash
# Set your OpenAI API key
export YOUR_API_KEY="your_openai_api_key_here"

# Process a single HTML file
python -m src.table_querying.main config/sample_table.html

# Process with custom configuration  
python -m src.table_querying.main file.html --config config/config_default.json

# Process with preset configuration
python -m src.table_querying.main file.html --preset minecraft-wiki
```

#### 2. Chat with Your Tables (NEW!)
```bash
# Interactive chat mode
python -m src.chatting_module.main --db table_querying.db

# Single query mode
python -m src.chatting_module.main --db table_querying.db --query "Show me all tables"

# List available tables
python -m src.chatting_module.main --db table_querying.db --list-tables
```

### Programmatic Usage

#### Table Processing
```python
from src.table_querying import TableProcessor, create_default_config

# Create configuration
config = create_default_config()
config.api_key = "your_openai_api_key_here"

# Process document
processor = TableProcessor(config.to_dict())
results = processor.process_document("document.html")
```

#### Natural Language Querying
```python
from src.chatting_module import ChatInterface

# Initialize chat interface
chat = ChatInterface("table_querying.db", "your_openai_api_key_here")

# Ask questions
result = chat.chat("Show me all tables with more than 5 rows")
# Returns either SQL query or "IMPOSSIBLE"

if result != "IMPOSSIBLE":
    # Execute the query
    data = chat.execute_sql_query(result)
    print(f"Found {len(data)} results")
```

## 📊 What It Does

### Table Processing Pipeline
1. **Extracts** HTML tables from documents and converts to markdown
2. **Processes** schemas with automatic type inference
3. **Describes** tables using LLM (OpenAI API) with natural language
4. **Stores** everything in SQLite database for querying
5. **Replaces** tables in documents with their descriptions
6. **Outputs** processed files, schemas, and reports

### Natural Language Querying (NEW!)
7. **Analyzes** user questions to determine if they can be answered by table data
8. **Generates** SQL queries from natural language requests
9. **Provides** conversational interface to query processed tables

## 🔧 Important Files

### Core Components
- `src/table_querying/table_processor.py` - Main workflow orchestrator
- `src/table_querying/main.py` - CLI interface
- `src/table_querying/config.py` - Configuration system

### Configuration
- `config/config_default.json` - Template configuration
- `config/sample_table.html` - Test HTML file
- `.env` file (create locally) - For API keys (not tracked in git)

### Testing
- `tests/test_module.py` - Run full integration test
- `demo.py` - Simple demo script

Run tests: `python tests/test_module.py`

## 📝 Output Files

Each processing run generates:
- `*_processed.md` - Document with table descriptions
- `*_original.md` - Original markdown
- `*_schemas.json` - Extracted table schemas  
- `*_descriptions.json` - LLM descriptions
- `*_replacement_report.txt` - Processing report

## 🔑 Configuration

Set API key via:
1. Environment variable: `export YOUR_API_KEY="key"`
2. Local .env file (recommended for development)
3. Configuration file: `--config your_config.json`
4. Command line: `--api-key "key"`

## 🚮 Generated Files (Cleaned Up)

The following are generated during processing and not part of source code:
- `*.db` - Database files
- `*_outputs/` - Output directories  
- `__pycache__/` - Python cache
- `fresh_test_outputs/` - Test outputs

These are now in `.gitignore` and removed from the repository.