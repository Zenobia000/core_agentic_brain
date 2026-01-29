# Tests Directory Structure

## Overview
This directory contains all tests for the Core Agentic Brain project.

## Structure

```
tests/
├── unit/               # Unit tests for individual components
│   ├── test_config.py             # Configuration testing
│   ├── test_simple_logger.py      # Simple logger testing
│   ├── test_tools.py              # Tools testing
│   └── test_types.py              # Type definitions testing
│
├── integration/        # Integration tests
│   ├── test_api_connection.py    # Test OpenAI API connection
│   ├── test_main_minimal.py      # Test main app in minimal mode
│   ├── test_llm_simple.py        # Test simple LLM queries
│   ├── test_prompt_integration.py # Test agents-prompts-tools integration
│   ├── test_layer1.py            # Test Layer 1 routing
│   └── test_routing.py           # Test routing system
│
├── performance/        # Performance and load tests
│   └── (performance tests)
│
├── fixtures/           # Test fixtures and mock data
│   └── (test data files)
│
├── tools/              # Tool-specific tests
│   └── (tool tests)
│
└── examples/           # Demo and example scripts
    ├── azure_api_demo.py
    └── example_full_integration.py  # Full agents-prompts-tools demo

```

## Running Tests

### Run all tests
```bash
pytest tests/
```

### Run specific test category
```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Performance tests
pytest tests/performance/
```

### Run individual test files
```bash
# Test API connection
python tests/integration/test_api_connection.py

# Test main application
python tests/integration/test_main_minimal.py

# Test simple LLM queries
python tests/integration/test_llm_simple.py
```

## Test Categories

### Unit Tests
- Focus on individual components in isolation
- Mock external dependencies
- Fast execution
- No network calls

### Integration Tests
- Test component interactions
- May include actual API calls
- Test the system with real configurations
- Verify end-to-end functionality

### Performance Tests
- Measure response times
- Test under load
- Memory usage analysis
- Concurrency testing

### Examples
- Demo scripts showing usage patterns
- Not part of the test suite
- Useful for manual testing and exploration