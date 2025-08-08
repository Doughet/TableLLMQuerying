# Configuration Guide

This document explains all available configuration parameters for the Table LLM Querying System.

## 📋 Complete Parameter List

### 🤖 LLM Configuration
- **`api_key`** - Your OpenAI API key (string, required)
- **`model_id`** - LLM model to use (string, default: "gpt-3.5-turbo")
- **`llm_service_type`** - LLM provider type (string, default: "openai")
- **`llm_base_url`** - Custom API base URL (string, optional)
- **`llm_organization`** - OpenAI organization ID (string, optional)
- **`llm_timeout`** - Request timeout in seconds (int, default: 30)
- **`llm_max_retries`** - Maximum retry attempts (int, default: 3)
- **`context_hint`** - Context for better descriptions (string, optional)

### 💾 Database Configuration
- **`db_path`** - SQLite database file path (string, default: "table_querying.db")
- **`db_service_type`** - Database provider (string, default: "sqlite")
- **`db_timeout`** - Database operation timeout (float, default: 30.0)
- **`db_auto_commit`** - Auto-commit transactions (bool, default: true)
- **`clear_database_on_start`** - Clear DB before processing (bool, default: false)

### 📁 Output Configuration
- **`save_outputs`** - Save processed files (bool, default: true)
- **`output_dir`** - Output directory path (string, default: "table_querying_outputs")
- **`max_tables_per_document`** - Max tables to process (int, default: 100)

### ⚙️ Processing Options
- **`enable_schema_validation`** - Validate table schemas (bool, default: true)
- **`enable_description_generation`** - Generate LLM descriptions (bool, default: true)

## 🔧 Configuration Methods

### 1. JSON Configuration Files
```json
{
  "api_key": "your_openai_api_key_here",
  "model_id": "gpt-3.5-turbo",
  "llm_service_type": "openai",
  "context_hint": "Scientific research papers",
  "db_path": "research_tables.db",
  "output_dir": "research_outputs"
}
```

### 2. Environment Variables
```bash
export YOUR_API_KEY="your_openai_api_key"
export TABLE_MODEL_ID="gpt-4"
```

Use in JSON:
```json
{
  "api_key": "${YOUR_API_KEY}",
  "model_id": "${TABLE_MODEL_ID}"
}
```

### 3. Command Line Arguments
```bash
python -m src.table_querying.main document.html --api-key "your-key" --model-id "gpt-4"
```

## 📝 Configuration Templates

### Basic Template
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

### Research Papers
```json
{
  "api_key": "${YOUR_API_KEY}",
  "model_id": "gpt-4",
  "context_hint": "Scientific research papers with experimental data",
  "db_path": "research_tables.db",
  "output_dir": "research_outputs",
  "max_tables_per_document": 50
}
```

### Large Scale Processing
```json
{
  "api_key": "${YOUR_API_KEY}",
  "model_id": "gpt-3.5-turbo",
  "context_hint": "Large corpus of web documents",
  "db_path": "bulk_tables.db",
  "output_dir": "bulk_outputs",
  "max_tables_per_document": 200,
  "llm_timeout": 60,
  "llm_max_retries": 5
}
```

## ⚡ Performance Tuning

### For Speed
```json
{
  "model_id": "gpt-3.5-turbo",
  "llm_timeout": 15,
  "llm_max_retries": 2,
  "enable_schema_validation": false
}
```

### For Quality
```json
{
  "model_id": "gpt-4",
  "llm_timeout": 60,
  "llm_max_retries": 5,
  "context_hint": "Detailed context about your domain"
}
```

## 🔐 Security Best Practices

1. **Never commit API keys** to version control
2. **Use environment variables** for sensitive data
3. **Use .env files** for local development
4. **Set proper file permissions** on configuration files

```bash
# Secure your config files
chmod 600 config/config_local.json
```

## 🎯 Domain-Specific Configurations

### Wikipedia Processing
```json
{
  "context_hint": "Wikipedia articles with structured data tables",
  "model_id": "gpt-3.5-turbo",
  "max_tables_per_document": 20
}
```

### E-commerce Data
```json
{
  "context_hint": "E-commerce product listings and specifications",
  "model_id": "gpt-3.5-turbo",
  "output_dir": "ecommerce_data"
}
```

### Financial Reports
```json
{
  "context_hint": "Financial statements and regulatory filings",
  "model_id": "gpt-4",
  "enable_schema_validation": true
}
```