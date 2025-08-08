# Full Pipeline Usage Guide

The `full_pipeline.py` script provides a complete workflow for table processing and interactive chatting.

## Prerequisites

1. **Install Dependencies**:
   ```bash
   cd table_querying_module
   pip install -r requirements.txt
   ```

2. **Set API Key** (required for chatting):
   ```bash
   export YOUR_API_KEY="your-bhub-api-key-here"
   ```

## Basic Usage

### Process Single HTML File

```bash
cd table_querying_module
python full_pipeline.py ../test_sample.html
```

This will:
1. Check if `test_sample.html` has already been processed
2. If not processed: Extract tables, generate schemas, create descriptions, store in database
3. If already processed: Skip processing step
4. Start interactive chat to query the database

### Process Directory of HTML Files

```bash
python full_pipeline.py --directory /path/to/html/files --recursive
```

### Interactive Chat Only

If you already have processed data and just want to chat:

```bash
python full_pipeline.py --interactive-only
```

### Force Reprocessing

To reprocess files even if they're already in the database:

```bash
python full_pipeline.py document.html --force-reprocess
```

## Configuration Options

### Using API Key

```bash
python full_pipeline.py document.html --api-key "your-key-here"
```

### Custom Database Path

```bash
python full_pipeline.py document.html --db-path "my_tables.db"
```

### Clear Database Before Processing

```bash
python full_pipeline.py document.html --clear-database
```

### Skip Chat After Processing

```bash
python full_pipeline.py document.html --no-chat
```

## Interactive Chat Commands

Once in chat mode, you can use:

### Natural Language Questions
- "Show me all tables"
- "Count how many tables we have"
- "What tables come from sample.html?"
- "Find tables with more than 3 rows"
- "List all table IDs"

### Special Commands
- `help` - Show example questions
- `summary` - Show database summary
- `tables` - List all available tables
- `quit` or `exit` - Exit the chat

### Example Chat Session

```
💬 Your question: Show me all tables

🔍 Analyzing your question...
✅ Generated SQL Query:
   SELECT table_id, source_file, rows, columns, description FROM tables

🔍 Execute this query to see results? (y/N): y

📊 Query Results (2 rows):
Row 1:
  table_id: test_sample_table_1
  source_file: test_sample.html
  rows: 4
  columns: 4
  description: Sales data table showing products, prices, quantities and totals...

Row 2:
  table_id: test_sample_table_2
  source_file: test_sample.html  
  rows: 3
  columns: 3
  description: Employee information table with names, departments and salaries...
```

## Pipeline Flow

```
1. 📄 Check if file processed ──┐
                               │
2. ❓ Already processed? ──────┤
   │                          │
   ├─ YES → Skip processing    │
   │                          │
   └─ NO → Process tables ─────┘
            │
            ├─ Extract HTML tables
            ├─ Generate schemas  
            ├─ Create LLM descriptions
            ├─ Store in database
            └─ Create processed documents
                               │
3. 🤖 Start Interactive Chat ──┘
   │
   ├─ Natural language questions
   ├─ Generate SQL queries
   └─ Execute and show results
```

## Output Files

When processing, the pipeline creates:
- `*_processed.md` - Document with tables replaced by descriptions  
- `*_original.md` - Original markdown version
- `*_schemas.json` - Extracted table schemas
- `*_descriptions.json` - LLM-generated descriptions
- `*_replacement_report.txt` - Detailed replacement report
- `table_querying.db` - SQLite database with all data

## Error Handling

The pipeline handles:
- **Missing API key**: Clear error message with instructions
- **File not found**: Detailed error with file path
- **Database errors**: Graceful degradation with warnings
- **LLM API failures**: Continues processing other tables
- **Invalid queries**: Returns "IMPOSSIBLE" for unanswerable questions

## Advanced Configuration

Create custom config files for specific use cases:

```bash
python full_pipeline.py document.html --config custom_config.json
```

Use presets for optimized processing:

```bash
python full_pipeline.py document.html --preset minecraft-wiki
```

## Troubleshooting

1. **Import errors**: Make sure you're in the `table_querying_module` directory
2. **API key errors**: Set `YOUR_API_KEY` environment variable
3. **No tables found**: Check if HTML files contain actual `<table>` elements
4. **Chat not working**: Verify database exists and contains processed tables