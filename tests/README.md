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
│   └── test_data.json            # Comprehensive test dataset
│
├── tools/              # Tool-specific tests
│   └── (tool tests)
│
├── examples/           # Demo and example scripts
│   ├── azure_api_demo.py
│   └── example_full_integration.py  # Full agents-prompts-tools demo
│
├── e2e/                # End-to-end tests
│   ├── test_e2e.py               # Basic E2E test
│   ├── test_e2e_simple.py        # Simplified E2E test
│   ├── test_e2e_full.py          # Comprehensive E2E test suite
│   └── E2E_TEST_REPORT.md        # E2E test report
│
├── orchestration/      # Multi-agent orchestration tests
│   ├── test_orchestration.py     # Basic orchestration test
│   ├── test_orchestration_fix.py # Orchestration fix validation
│   └── debug_llm_analyzer.py     # LLM analyzer debugging tool
│
└── core/               # Core functionality tests
    ├── test_config.py            # Configuration testing
    ├── test_routing.py           # Routing system testing
    ├── test_agent.py             # Agent functionality
    └── test_tool_manager.py      # Tool management testing

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

# E2E Tests
python tests/test_e2e_simple.py          # Quick E2E test
python tests/test_e2e_full.py --mode full    # Complete E2E test suite
python tests/test_e2e_full.py --mode quick   # Quick validation
python tests/test_e2e_full.py --mode scenario # Scenario-based testing

# Orchestration Tests
python tests/test_orchestration.py       # Basic orchestration test
python tests/test_orchestration_fix.py   # Verify orchestration fixes

# Debug Tools
python tests/debug_llm_analyzer.py      # Debug LLM task analysis
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

### E2E Tests
- Complete system validation
- Tests multi-agent collaboration
- Validates routing decisions
- Measures system performance
- Comprehensive test dataset in `test_data.json`

### Orchestration Tests
- Multi-agent coordination validation
- ReAct architecture testing
- Planner → Executor → Reviewer chain
- Debug tools for LLM analysis

## Test Data
- `test_data.json`: Comprehensive test dataset with 8 categories:
  - Simple tasks
  - Moderate tasks
  - Complex tasks
  - ReAct tasks
  - Tool integration tasks
  - Error handling tasks
  - Multi-language tasks
  - Performance tasks

## Recent Updates
- 2026-01-29: Moved all test scripts from root to tests directory
- 2026-01-29: Fixed multi-agent orchestration trigger issue
- 2026-01-29: Added comprehensive E2E test suite