# 🔍 Table LLM Querying System

> **Extract tables from HTML and Excel documents, generate intelligent descriptions, and query your data with natural language**

A comprehensive Python system that transforms document tables (HTML, Excel) into queryable databases with AI-powered natural language descriptions. Perfect for researchers, data analysts, and developers working with structured data.

## 🌟 What Can You Do?

### 📊 **Table Processing**
- **Extract tables** from HTML documents and Excel files automatically
- **Generate schemas** with intelligent type inference (string, number, date, etc.)
- **Create descriptions** using OpenAI to explain what each table contains
- **Store everything** in a SQLite database for easy querying

### 💬 **Natural Language Queries**
- **Ask questions** like "Show me all tables with more than 100 rows"
- **Get SQL queries** automatically generated from your questions
- **Execute queries** and see results instantly
- **Save results** in multiple formats (CSV, JSON, TXT)

### 🔄 **Complete Workflow**
```
Documents (HTML/Excel) → Smart Extractor Router → Extract Tables → AI Descriptions → Database → Natural Language Queries
```

## 🎯 Perfect For

- **Web scraping projects** with table data
- **Excel analysis** and data processing workflows
- **Research papers** analysis and data extraction
- **Wiki processing** (like Minecraft Wiki, Wikipedia)
- **Documentation** with structured data tables
- **Data exploration** with conversational interfaces

## 🚀 Quick Start (5 minutes)

### 1. **Installation**
```bash
# Clone the repository
git clone https://github.com/your-username/TableLLMQuerying.git
cd TableLLMQuerying/table_querying_module

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### 2. **Get OpenAI API Key**
- Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
- Create a new API key
- Copy it for the next step

### 3. **Configuration**
Create a `.env` file in the project root:
```bash
# In /TableLLMQuerying/.env
OPENAI_API_KEY=your_openai_api_key_here
TABLE_MODEL_ID=gpt-3.5-turbo
```

### 4. **Test with Sample Data**
```bash
# Process HTML files
python -m src.table_querying.main your_document.html

# Process Excel files  
python -m src.table_querying.main your_spreadsheet.xlsx

# Chat with the results
python -m src.chatting_module.main --db table_querying.db
```

That's it! 🎉

## 📖 Complete Usage Guide

### 📄 **Processing Documents**

#### **Single File Processing**
```bash
# Basic HTML processing
python -m src.table_querying.main your_document.html

# Basic Excel processing
python -m src.table_querying.main your_spreadsheet.xlsx

# With custom configuration
python -m src.table_querying.main your_document.html --config config/config_default.json

# Specify output location
python -m src.table_querying.main your_document.html --output-dir results/
```

#### **Batch Processing**
```bash
# Process all supported files (HTML, Excel) in a directory
python -m src.table_querying.main --directory /path/to/files

# Recursive search in subdirectories
python -m src.table_querying.main --directory /path/to/docs --recursive

# Clear database and start fresh
python -m src.table_querying.main --directory docs/ --clear-database
```

### 💬 **Querying Your Data**

#### **Interactive Mode**
```bash
# Start chatting with your tables
python -m src.chatting_module.main --db table_querying.db

# Enable result saving
python -m src.chatting_module.main --db table_querying.db --save-results --output-dir exports/
```

**Chat Commands:**
- `help` - Show available commands
- `tables` - List all available tables
- `summary` - Show database overview
- `save csv` - Save last query results
- Type any question in plain English!

#### **Single Queries**
```bash
# Get SQL for a question
python -m src.chatting_module.main --db table_querying.db --query "Count all tables"

# Execute and save results automatically
python -m src.chatting_module.main --db table_querying.db --query "Show me all tables" --save-results --export-format json
```

### ⚙️ **Configuration Options**

#### **Basic Configuration** (`config/config_default.json`)
```json
{
  "api_key": "your_openai_api_key_here",
  "model_id": "gpt-3.5-turbo",
  "llm_service_type": "openai",
  "context_hint": "Generic HTML documents with table data",
  "db_path": "table_querying.db",
  "output_dir": "table_outputs"
}
```

#### **Domain-Specific Configuration**
```json
{
  "api_key": "your_openai_api_key_here", 
  "model_id": "gpt-3.5-turbo",
  "context_hint": "Minecraft Wiki pages with game mechanics and recipes",
  "db_path": "minecraft_tables.db",
  "output_dir": "minecraft_outputs"
}
```

#### **Environment Variables**
You can use environment variables in config files:
```json
{
  "api_key": "${OPENAI_API_KEY}",
  "model_id": "${TABLE_MODEL_ID}"
}
```

## 💡 Real Examples

### **Example 1: Processing Wikipedia Tables**
```bash
# Download some Wikipedia pages with tables
wget "https://en.wikipedia.org/wiki/List_of_countries_by_population" -O countries.html

# Process the tables
python -m src.table_querying.main countries.html --context-hint "Wikipedia page about country population statistics"

# Query the data
python -m src.chatting_module.main --db table_querying.db --query "Show me countries with population over 100 million"
```

### **Example 2: Research Paper Analysis**
```bash
# Process multiple research papers
python -m src.table_querying.main --directory research_papers/ --context-hint "Scientific research papers with experimental data"

# Interactive exploration
python -m src.chatting_module.main --db table_querying.db --save-results
# Ask: "Find all tables with statistical significance results"
# Ask: "Show me tables with correlation coefficients"
```

### **Example 3: E-commerce Data**
```bash
# Process product catalog pages
python -m src.table_querying.main product_pages/ --context-hint "E-commerce product listings and specifications"

# Query with saving
python -m src.chatting_module.main --db table_querying.db --query "Find all product tables with price information" --save-results --export-format csv
```

## 📁 What You Get

### **Generated Files**
After processing, you'll find:
- `document_processed.md` - Document with table descriptions
- `document_schemas.json` - Extracted table structures  
- `document_descriptions.json` - AI-generated table descriptions
- `table_querying.db` - SQLite database with all data
- `table_outputs/` - Directory with organized results

### **Query Result Exports**
When saving query results:
- **CSV** - Spreadsheet-compatible format
- **JSON** - Structured data with metadata
- **TXT** - Human-readable table format

## 🎛️ Advanced Features

### **Custom Configurations**
```bash
# Create configuration template
python -m src.table_querying.main --create-config-template

# Use preset configurations
python -m src.table_querying.main document.html --preset minecraft-wiki
```

### **Database Operations**
```bash
# List all tables in database
python -m src.chatting_module.main --db table_querying.db --list-tables

# Show database summary
python -m src.chatting_module.main --db table_querying.db --summary

# Process with different database
python -m src.table_querying.main document.html --db-path my_tables.db
```

### **Export Options**
```bash
# Save results with custom filename
python -m src.chatting_module.main --db table_querying.db --query "Count rows per table" --save-results --export-filename table_summary

# Specify output directory
python -m src.chatting_module.main --db table_querying.db --save-results --output-dir exports/
```

## 🤖 Natural Language Query Examples

You can ask questions like:

**Basic Queries:**
- "Show me all tables"
- "Count how many tables are in the database"
- "List tables with more than 10 rows"

**Content Queries:**
- "Find tables containing price information"
- "Show me tables from minecraft files"  
- "What columns does the inventory table have?"

**Analytical Queries:**
- "Which table has the most rows?"
- "Show me tables with date columns"
- "Find tables with numeric data"

**Complex Queries:**
- "Show me all data from tables with 'recipe' in the description"
- "Count rows in each table and order by count"
- "Find tables that mention 'statistics' in their description"

## 📊 System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   HTML Files    │───▶│  Table Processor │───▶│   SQLite DB     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │  OpenAI Descrip. │    │  Chat Interface │
                       └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
                                               ┌─────────────────┐
                                               │ Export Results  │
                                               │ (CSV/JSON/TXT)  │
                                               └─────────────────┘
```

### **Core Components**
- **TableExtractor** - HTML parsing and table extraction
- **SchemaProcessor** - Type inference and structure analysis
- **TableSummarizer** - AI-powered description generation
- **ChatInterface** - Natural language query processing
- **ResultExporter** - Multi-format output generation

## 🔧 Requirements

- **Python 3.8+**
- **OpenAI API key** (get one at [platform.openai.com](https://platform.openai.com))
- **Dependencies** (auto-installed):
  - `docling` - Document processing
  - `beautifulsoup4` - HTML parsing
  - `pandas` - Data manipulation
  - `requests` - API communication
  - `python-dotenv` - Environment variables

## ❓ Troubleshooting

### **Common Issues**

**"API key not found"**
```bash
# Make sure your .env file exists and contains:
OPENAI_API_KEY=your_actual_api_key_here
```

**"No tables found"**
- Check that your HTML file contains `<table>` elements
- Try with the included `config/sample_table.html` first

**"Database not found"**
```bash
# Make sure you process files first to create the database
python -m src.table_querying.main config/sample_table.html
```

**"Module not found"**
```bash
# Install in development mode
pip install -e .
```

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### **Quick Contribution Setup**
```bash
# Fork the repo, then:
git clone https://github.com/your-username/TableLLMQuerying.git
cd TableLLMQuerying/table_querying_module
pip install -e .

# Make your changes, then:
python tests/test_module.py  # Run tests
git commit -am "Add awesome feature"
git push origin feature-branch
# Create pull request
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙋‍♂️ Support

- **Issues** - Report bugs or request features
- **Discussions** - Ask questions or share ideas
- **Documentation** - Check the `/docs` folder for detailed guides

## 🔮 Roadmap

- [ ] **PDF table extraction** support
- [ ] **Additional LLM providers** (Anthropic Claude, local models)
- [ ] **Web interface** for easier interaction
- [ ] **Batch processing** optimizations
- [ ] **Advanced query** capabilities
- [ ] **Real-time processing** for live websites

---

**⭐ If this project helps you, please give it a star! It helps others discover it too.**

**🚀 Ready to turn your HTML tables into intelligent, queryable databases? Get started now!**