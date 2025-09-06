# LLM Services Testing Guide

This directory contains comprehensive tests for the LLM Services module, including both unit tests with mocks and integration tests with real LLM APIs.

## Test Types

### 1. Unit Tests (`test_llm_service.py`)
- **Purpose**: Fast, reliable tests that don't make external API calls
- **Uses**: Mocked LLM clients
- **Cost**: Free
- **Speed**: Very fast (~1-2 seconds)
- **When to run**: Always, on every commit/PR

```bash
# Run unit tests only
pytest modules/llm_services/tests/test_llm_service.py -v
```

### 2. Integration Tests (`test_llm_integration.py`)
- **Purpose**: Test real LLM integration and behavior
- **Uses**: Real OpenAI API calls
- **Cost**: Small cost (~$0.01-0.05 per full run)
- **Speed**: Slower (~30-60 seconds)
- **When to run**: Before releases, when changing LLM logic

```bash
# Option 1: Using .env file (recommended)
# Create backend/.env with your API key, then:
pytest modules/llm_services/tests/test_llm_integration.py -v -m integration

# Option 2: Using environment variables
export OPENAI_API_KEY="your-key-here"
pytest modules/llm_services/tests/test_llm_integration.py -v -m integration
```

## Quick Commands

### Using Test Runner Scripts (Recommended)

```bash
# Run LLM Services unit tests (fast, mocked)
python scripts/run_unit.py --module llm_services

# Run LLM Services integration tests (real LLM, costs money)
python scripts/run_integration.py --module llm_services

# Check environment and estimate costs
python scripts/run_integration.py --cost-check

# Run all backend unit tests
python scripts/run_unit.py

# Run all backend integration tests
python scripts/run_integration.py
```

### Direct pytest Commands

```bash
# Unit tests
pytest modules/llm_services/tests/test_llm_service.py -v -m "not integration"

# Integration tests
pytest modules/llm_services/tests/test_llm_integration.py -v -m integration --integration
```

## Environment Variables

### Setting Up Environment Variables

The test infrastructure automatically loads environment variables from `.env` files using a built-in parser. Create a `.env` file in the `backend/` directory:

```bash
# Copy the example and edit with your values
cp modules/llm_services/tests/env_example.txt backend/.env
```

**Note**: If you prefer to use `python-dotenv`, you can install it (`pip install python-dotenv`) and use `load_dotenv()` in your own scripts. However, the test infrastructure includes built-in .env support, so `python-dotenv` is not required.

### Supported .env Files (in order of precedence)

1. `backend/.env.test.local` - Local test overrides (gitignored)
2. `backend/.env.test` - Test environment settings
3. `backend/.env.local` - Local overrides (gitignored)
4. `backend/.env` - Default environment settings

### Environment Variables

| Variable | Purpose | Required For | Example |
|----------|---------|--------------|---------|
| `OPENAI_API_KEY` | OpenAI API authentication | Integration tests | `sk-proj-...` |
| `ANTHROPIC_API_KEY` | Anthropic API (future) | Anthropic tests | `sk-ant-...` |
| `LLM_TEST_MODEL` | Model to use for testing | Optional | `gpt-3.5-turbo` |
| `LLM_TEST_TIMEOUT` | Request timeout in seconds | Optional | `30` |

## Test Markers

Use pytest markers to run specific test categories:

```bash
# Run only unit tests
pytest -m "unit" modules/llm_services/tests/

# Run only integration tests
pytest -m "integration" modules/llm_services/tests/

# Run tests that don't use real LLMs
pytest -m "not integration" modules/llm_services/tests/

# Run tests that may incur costs
pytest -m "llm" modules/llm_services/tests/
```

## Cost Management

### Estimated Costs (using gpt-3.5-turbo)
- Single unit test: $0 (mocked)
- Single integration test: ~$0.001-0.005
- Full integration suite: ~$0.01-0.05
- Full test suite (all types): ~$0.02-0.10

### Cost Reduction Strategies
1. **Use cheaper models**: gpt-3.5-turbo instead of gpt-4
2. **Short test inputs**: Keep prompts concise
3. **Enable caching**: Avoid duplicate API calls
4. **Selective testing**: Run integration tests only when needed
5. **Mock by default**: Use real LLMs only for critical tests

## Test Utilities

### Using the Test Script
```bash
# Check costs before running
python scripts/test_llm.py cost-check

# Run different test types
python scripts/test_llm.py unit          # Unit tests only
python scripts/test_llm.py integration  # Integration tests only
python scripts/test_llm.py hybrid       # Hybrid tests
python scripts/test_llm.py all          # All tests with confirmation
```

### Cost Monitoring
```python
# In your tests, use the cost_monitor fixture
def test_with_cost_tracking(cost_monitor, real_llm_service):
    # Make LLM calls
    result = await real_llm_service.generate_content(...)

    # Track costs
    cost_monitor.record_request(tokens_used=50, cost_estimate=0.001)

    # Get summary
    summary = cost_monitor.get_summary()
    print(f"Total cost: ${summary['total_cost']:.4f}")
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: LLM Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run unit tests
        run: pytest -m "not integration" modules/llm_services/tests/

  integration-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Run integration tests
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: pytest -m "integration" modules/llm_services/tests/
```

## Best Practices

### For Unit Tests
1. **Mock all external dependencies**
2. **Test business logic thoroughly**
3. **Use deterministic test data**
4. **Keep tests fast and reliable**
5. **Test error conditions**

### For Integration Tests
1. **Use simple, predictable inputs**
2. **Test core functionality only**
3. **Handle API rate limits gracefully**
4. **Monitor and log costs**
5. **Make assertions flexible (LLM outputs vary)**

### For Hybrid Tests
1. **Design tests that work with both real and mock**
2. **Focus on contracts and interfaces**
3. **Use configuration to switch modes**
4. **Provide clear documentation**
5. **Handle both deterministic and probabilistic outputs**

## Troubleshooting

### Common Issues

**"OPENAI_API_KEY not set"**
```bash
export OPENAI_API_KEY="sk-your-key-here"
```

**"Tests are too slow"**
- Run unit tests only: `pytest -m "not integration"`
- Use smaller test inputs
- Enable caching

**"Tests are too expensive"**
- Use gpt-3.5-turbo instead of gpt-4
- Reduce number of integration tests
- Use mocks for development

**"Flaky test results"**
- LLM outputs are probabilistic
- Make assertions more flexible
- Use temperature=0 for more deterministic results
- Test patterns rather than exact matches

### Debug Mode
```bash
# Run with verbose output
pytest -v -s modules/llm_services/tests/

# Run single test with debugging
pytest -v -s modules/llm_services/tests/test_llm_integration.py::test_real_content_generation
```

## Adding New Tests

### For New LLM Features
1. Start with unit tests (mocked)
2. Add hybrid tests for contracts
3. Add integration tests for critical paths
4. Update cost estimates
5. Document any new environment variables

### Test Template
```python
@pytest.mark.asyncio
async def test_new_feature(llm_service_hybrid):
    """Test new LLM feature with hybrid approach"""
    # Arrange
    input_data = "test input"

    # Act
    result = await llm_service_hybrid.new_feature(input_data)

    # Assert - works for both real and mock
    assert isinstance(result, str)
    assert len(result) > 0

    # Mock-specific assertions
    if hasattr(llm_service_hybrid, '_mock_client'):
        # Verify mock interactions
        pass
    else:
        # Real LLM assertions (be flexible)
        pass
```

This testing approach provides comprehensive coverage while managing costs and maintaining development velocity.
