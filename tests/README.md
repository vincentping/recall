# Tests Directory

This directory contains all automated tests for the ReCall project.

## Test Structure

```
tests/
├── unit/              # Unit tests (individual components)
├── integration/       # Integration tests (multiple components)
└── README.md         # This file
```

## Test Categories

### Unit Tests (`tests/unit/`)
Test individual components in isolation:
- `test_db_manager.py` - Database operations
- `test_md_parser.py` - Markdown parsing
- `test_ui_components.py` - UI components

### Integration Tests (`tests/integration/`)
Test multiple components working together:
- `test_import_flow.py` - Complete import workflow
- `test_ui_integration.py` - UI component interactions
- `test_database_ui.py` - Database + UI integration

## Running Tests

### Run all tests:
```bash
pytest tests/
```

### Run unit tests only:
```bash
pytest tests/unit/
```

### Run integration tests only:
```bash
pytest tests/integration/
```

### Run with coverage:
```bash
pytest --cov=src tests/
```

## Writing Tests

### Example unit test:
```python
# tests/unit/test_db_manager.py
import pytest
from src.core.db_manager import DBManager

def test_db_manager_initialization():
    """Test DBManager can be initialized"""
    db = DBManager(':memory:')  # Use in-memory database for testing
    assert db is not None
    assert db.conn is not None
```

### Example integration test:
```python
# tests/integration/test_import_flow.py
import pytest
from src.core.db_manager import DBManager
from src.utils.md_parser import MarkdownQuestionParser

def test_import_workflow():
    """Test complete question import workflow"""
    db = DBManager(':memory:')
    parser = MarkdownQuestionParser()
    # Test the complete flow...
```

## Test Guidelines

1. **Keep tests isolated** - Each test should be independent
2. **Use fixtures** - Reuse common setup code
3. **Mock external dependencies** - Don't rely on real database/files
4. **Name tests clearly** - Use descriptive names (test_should_do_something)
5. **Test edge cases** - Not just happy paths

## Setup for Testing

Install testing dependencies:
```bash
pip install pytest pytest-cov pytest-qt
```

## CI/CD Integration

These tests can be run automatically in CI/CD pipelines:
```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: pytest tests/ --cov=src
```

## Notes

- Tests use pytest framework
- UI tests may require pytest-qt for Qt components
- Use `:memory:` databases for isolated database tests
- Mock file I/O operations to avoid side effects
