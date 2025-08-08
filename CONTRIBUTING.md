# Contributing to Table LLM Querying System

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## 🚀 Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Install dependencies**: `pip install -r requirements.txt`
4. **Create a branch** for your feature: `git checkout -b feature/my-feature`

## 🏗️ Development Setup

```bash
# Install in development mode
cd table_querying_module
pip install -e .

# Set up your API key for testing
export YOUR_API_KEY="your_openai_api_key"

# Run tests
python tests/test_module.py
```

## 📝 Contribution Types

We welcome contributions in these areas:

### 🐛 Bug Fixes
- Fix issues with table extraction
- Resolve schema inference problems
- Address query generation bugs

### ✨ New Features
- Additional LLM provider integrations
- New export formats
- Enhanced query capabilities
- Performance improvements

### 📚 Documentation
- Improve README and guides
- Add code examples
- Create tutorials

### 🧪 Testing
- Add test cases
- Improve test coverage
- Performance benchmarks

## 🎯 Code Standards

### Python Style
- Follow **PEP 8** style guidelines
- Use **type hints** where possible
- Add **docstrings** for classes and functions
- Keep functions focused and modular

### Code Organization
- Maintain the **modular architecture**
- Keep **interfaces clean** and well-defined
- Follow existing **naming conventions**
- Add appropriate **logging**

### Example Code Style
```python
def process_table(table_data: List[Dict[str, Any]], 
                 config: TableProcessingConfig) -> ProcessingResult:
    """
    Process table data with the given configuration.
    
    Args:
        table_data: Raw table data to process
        config: Processing configuration
        
    Returns:
        Processing results with metadata
    """
    logger.info(f"Processing {len(table_data)} table rows")
    # Implementation...
```

## 🔄 Pull Request Process

1. **Create descriptive commit messages**
2. **Update documentation** if needed
3. **Add tests** for new functionality
4. **Ensure all tests pass**
5. **Update CHANGELOG.md** if applicable

### PR Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement

## Testing
- [ ] Tests added/updated
- [ ] All tests passing
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No breaking changes
```

## 🚫 What NOT to Include

**Never commit these items:**
- API keys or secrets
- Database files with real data
- Private implementation details
- Large binary files
- IDE-specific configuration

## 🏷️ Issue Guidelines

### Bug Reports
Include:
- **Clear description** of the problem
- **Steps to reproduce**
- **Expected vs actual behavior**
- **Environment details** (Python version, OS)
- **Error messages** or logs

### Feature Requests
Include:
- **Clear description** of the feature
- **Use case** and motivation
- **Proposed implementation** (if applicable)
- **Backwards compatibility** considerations

## 🧪 Testing Guidelines

### Running Tests
```bash
# Run all tests
python tests/test_module.py

# Test specific functionality
python -m src.table_querying.main config/sample_table.html
python -m src.chatting_module.main --db test.db --list-tables
```

### Writing Tests
- Test both **success and failure cases**
- Use **meaningful test data**
- Keep tests **independent**
- Add tests for **edge cases**

## 🏆 Recognition

Contributors will be:
- **Listed in CONTRIBUTORS.md**
- **Mentioned in release notes**
- **Thanked in the community**

## 📞 Getting Help

- **GitHub Issues** - For bugs and feature requests
- **Discussions** - For questions and ideas
- **Code Review** - All PRs get reviewed promptly

## 🎨 Architecture Guidelines

When adding features:
- **Maintain modularity** - Keep components independent
- **Follow interfaces** - Use existing abstract classes
- **Add configuration** - Make features configurable
- **Consider extensibility** - Think about future needs

Thank you for contributing! 🙏