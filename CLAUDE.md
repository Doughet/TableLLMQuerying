# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build and Development Commands

This is a Python-based Table LLM Querying System. Key commands:

```bash
# Install for development
pip install -e .

# Install with all dependencies
pip install -e .[all]

# Process HTML documents (extract tables)
python -m src.table_querying.main document.html --config config/config_default.json

# Process Excel documents (extract tables)
python -m src.table_querying.main workbook.xlsx --config config/config_default.json

# Query processed data (natural language)
python -m src.chatting_module.main --db table_querying.db

# Batch process directory (supports HTML and Excel)
python -m src.table_querying.main --directory files/ --recursive

# Create configuration template
python -m src.table_querying.main --create-config-template
```

## Project Architecture

This system follows a **two-phase pipeline architecture** for converting document tables (HTML, Excel) into queryable databases:

### Core Pipeline Flow
1. **Processing Phase**: `table_querying` module extracts tables from supported documents, infers schemas, generates AI descriptions, stores in SQLite
2. **Querying Phase**: `chatting_module` converts natural language to SQL, executes queries, exports results

### Key Components

**Table Processing Pipeline** (`src/table_querying/`):
- `TableProcessor` - Main workflow orchestrator
- `ExtractorRouter` - Routes files to appropriate extractors (HTML, Excel)
- `HTMLTableExtractor` - HTML parsing using BeautifulSoup + docling
- `ExcelTableExtractor` - Excel parsing using pandas + openpyxl
- `ExtractorFactory` - Factory for creating and managing extractors
- `SchemaProcessor` - Type inference and validation
- `TableSummarizer` - LLM-powered description generation
- `TableDatabase` - SQLite storage with JSON data

**Query Interface** (`src/chatting_module/`):
- `ChatInterface` - Natural language query processor
- `QueryAnalyzer` - Determines query feasibility
- `SQLGenerator` - NL to SQL conversion with retry logic
- `ResultExporter` - Multi-format exports (CSV, JSON, TXT)

**Service Layer** (`src/services/`):
- Factory pattern for pluggable LLM/database services
- `OpenAILLMService` for OpenAI API integration
- `SQLiteDatabaseService` with abstraction for future backends
- Private service implementations in `services/private/` (gitignored)

### Configuration System

Multi-layered configuration with precedence: CLI args → JSON config → environment variables → defaults

- **Environment variable expansion**: `"${OPENAI_API_KEY}"` syntax in JSON configs
- **Domain-specific presets**: `config/config_minecraft_wiki.json`, etc.
- **Template generation**: `--create-config-template` creates starter configs
- **Security**: Private implementations in `services/private/` (gitignored)

Key configuration classes:
- `TableProcessingConfig` - Complete parameter set with validation
- Configuration loading supports `.env` file discovery up the directory tree

### Database Architecture

SQLite schema with three main tables:
- `tables` - Metadata (table_id, source_file, schema, descriptions)
- `table_data` - Actual row data stored as JSON
- `processing_sessions` - Batch processing tracking

Data flow: Document (HTML/Excel) → ExtractorRouter → Specific Extractor → Pandas DataFrame → Schema Analysis → LLM Description → SQLite JSON storage

### Entry Points

The system provides multiple CLI interfaces:
- **Table Processing**: Process supported documents (HTML, Excel) into database
- **Chat Interface**: Query database with natural language
- **Batch Operations**: Directory processing, configuration management

Both modules support:
- Interactive and single-command modes
- Result saving with multiple formats
- Comprehensive error handling and progress tracking
- Environment variable configuration

### Extension Points

Easy to extend via:
- **LLM Services**: Implement `LLMService` abstract class
- **Database Backends**: Implement `DatabaseService` abstract class
- **Export Formats**: Extend `ResultExporter` class
- **Document Types**: Implement `BaseTableExtractor` and register with `ExtractorFactory`

### Development Notes

- Uses `docling` for HTML document parsing and table extraction
- Uses `pandas` with `openpyxl`/`xlrd` for Excel file processing
- Pluggable extractor architecture via Strategy pattern
- LLM calls have retry logic and timeout handling
- Database operations are transactional with session tracking
- Configuration supports both development (.env) and production deployment
- Private/sensitive components isolated in `services/private/`
- Entry points defined in `setup.py` for CLI command installation

### Adding New File Types

To add support for new document types:

1. **Create a new extractor**: Implement `BaseTableExtractor` abstract class
2. **Register the extractor**: Use `ExtractorFactory.register_extractor()` 
3. **Test the integration**: ExtractorRouter will automatically route files to your extractor

Example:
```python
class PDFTableExtractor(BaseTableExtractor):
    def supports_file_type(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() == '.pdf'
    
    def get_supported_extensions(self) -> List[str]:
        return ['.pdf']
    
    def extract_from_file(self, file_path: str) -> ExtractionResult:
        # Implementation here
        pass

# Register the new extractor
ExtractorFactory.register_extractor('pdf', PDFTableExtractor)
```