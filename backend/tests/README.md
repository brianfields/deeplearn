# Backend Tests

This directory contains all tests for the backend application.

## Test Structure

### Core Tests
- **`test_data_structures.py`** - Tests for core data structures like `QuizQuestion`
- **`test_very_simple.py`** - Basic functionality tests for the simplified backend

### MCQ System Tests
- **`test_mcq_prompts.py`** - Tests for MCQ prompt templates
- **`test_mcq_service.py`** - Tests for the two-pass MCQ service
- **`test_orchestrator_mcq.py`** - Tests for MCQ orchestration
- **`test_mcq_script.py`** - Tests for MCQ CLI scripts

### Backend Service Tests
- **`test_conversational.py`** - Tests for conversational AI features
- **`test_bite_sized_integration.py`** - Integration tests for bite-sized topics
- **`test_system.py`** - System-level tests

### Excluded Tests
- **`test_simplified_backend.py`** - Excluded due to architectural incompatibilities with old codebase

## Running Tests

### Simple Usage

```bash
# Run all tests
python run_all_tests.py

# Run with verbose output
python run_all_tests.py -v

# Run specific test file
python run_all_tests.py --file test_mcq_service.py
```

### Test Categories

```bash
# Run only quick tests
python run_all_tests.py --quick

# Run only MCQ-related tests
python run_all_tests.py --mcq

# Run only integration tests
python run_all_tests.py --integration
```

### Advanced Options

```bash
# Run with coverage report
python run_all_tests.py --coverage

# Run tests in parallel
python run_all_tests.py --parallel

# Combine options
python run_all_tests.py --mcq --verbose --coverage
```

### Using pytest directly

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_mcq_service.py

# Run with verbose output
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## Test Organization

Tests are organized by functionality:

1. **Core Data Structures** - Basic data models and validation
2. **MCQ System** - Multiple choice question generation and evaluation
3. **Backend Services** - API endpoints and service layer
4. **Integration Tests** - End-to-end functionality

Each test file is self-contained and can be run independently.

## Writing New Tests

- Place new tests in the appropriate category
- Follow the existing naming convention: `test_<component>.py`
- Use descriptive test method names
- Include docstrings explaining what each test verifies
- Mock external dependencies (LLM calls, database operations)

## CI/CD Integration

These tests are designed to run in CI/CD environments. The `run_all_tests.py` script returns proper exit codes for automated testing.