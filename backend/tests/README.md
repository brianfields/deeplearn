# Backend Tests

This directory contains all tests for the backend application, organized around our clean two-layer API architecture.

## Test Organization Philosophy

Our tests are organized to match the **two-layer architecture**:
1. **Content Creation Layer** - For content creators using the studio interface
2. **Learning Layer** - For learners consuming educational content

## Test Structure

### Core Service Tests
- **`test_services.py`** - Tests for core business logic services
  - `RefinedMaterialService`: Extracting structured material from unstructured content
  - `MCQService`: Creating and evaluating multiple choice questions
  - Service integration workflows

### API Layer Tests
- **`test_api_content_creation.py`** - Tests for Content Creation API (`/api/content/*`)
  - Refined material extraction endpoints
  - MCQ creation workflows
  - Topic creation and management
  - Session management
  - Input validation

- **`test_api_learning.py`** - Tests for Learning API (`/api/learning/*`)
  - Topic discovery and browsing
  - Learning-optimized topic access
  - Component consumption
  - Health monitoring
  - Error handling

### Integration Tests
- **`test_integration.py`** - End-to-end workflow tests
  - Complete content creation workflow (source material → topics → components)
  - Complete learning consumption workflow (discovery → access → consumption)
  - Cross-layer integration (content creation → learning consumption)

### Supporting Tests
- **`test_data_structures.py`** - Tests for core data structures like `QuizQuestion`
- **`test_mcq_prompts.py`** - Tests for MCQ prompt templates and generation
- **`test_mcq_script.py`** - Tests for MCQ CLI scripts and command-line tools

## Running Tests

### Simple Usage

```bash
# Run all tests
python run_all_tests.py

# Run with verbose output
python run_all_tests.py -v

# Run specific test file
python run_all_tests.py --file test_services.py
```

### Test Categories

```bash
# Run only service layer tests
python -m pytest test_services.py -v

# Run only API tests
python -m pytest test_api_*.py -v

# Run only integration tests
python -m pytest test_integration.py -v

# Run specific test class
python -m pytest test_services.py::TestMCQService -v
```

### Test Coverage by Layer

**Service Layer Coverage:**
- ✅ Refined material extraction from unstructured text
- ✅ MCQ creation and evaluation
- ✅ Service integration workflows
- ✅ Error handling and edge cases

**Content Creation API Coverage:**
- ✅ All `/api/content/*` endpoints
- ✅ Topic creation from source material
- ✅ Component generation and management
- ✅ Session-based workflows
- ✅ Input validation and error handling

**Learning API Coverage:**
- ✅ All `/api/learning/*` endpoints
- ✅ Topic discovery with filtering
- ✅ Learning-optimized content access
- ✅ Component consumption interfaces
- ✅ Health monitoring

**Integration Coverage:**
- ✅ End-to-end content creation workflows
- ✅ End-to-end learning consumption workflows
- ✅ Cross-layer integration scenarios

## Test Naming Convention

Tests follow a clear naming pattern that indicates what's being tested:

- `test_services.py` - Core business logic services
- `test_api_[layer].py` - API layer for specific layer (content_creation, learning)
- `test_integration.py` - End-to-end workflow integration tests
- `test_[component].py` - Specific component or utility tests

## Architecture Alignment

These tests are designed to verify our two-layer architecture principles:

1. **Clear Separation**: Content Creation and Learning APIs are tested separately
2. **Service Reusability**: Services are tested independently and can be used by either API layer
3. **Workflow Integrity**: Integration tests verify complete user workflows work correctly
4. **Error Boundaries**: Each layer's error handling is tested appropriately

## Deprecated Tests

The following test files were removed during the architecture cleanup:
- `test_simplified_backend.py` - Tested old API structure
- `test_orchestrator_mcq.py` - Redundant with service tests
- `test_bite_sized_integration.py` - Replaced by `test_integration.py`
- `test_system.py` - Tested obsolete components
- `test_conversational.py` - Tested features not in current architecture
- `test_very_simple.py` - Tested obsolete service classes
- `test_mcq_service.py` - Redundant with `test_services.py`