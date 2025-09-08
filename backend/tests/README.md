# Integration Tests

This directory contains integration tests that use real external services (database, LLM APIs) to test the complete application workflow.

## Topic Creation Integration Test

The `test_topic_creation_integration.py` file contains a comprehensive integration test for the complete topic creation workflow, similar to what the `create_topic.py` script does but with automated validation.

### What it tests:

1. **Complete Topic Creation Flow**: Creates a topic from source material using real LLM calls
2. **Database Integration**: Verifies topics and components are properly saved to PostgreSQL
3. **Component Generation**: Tests creation of didactic snippets, glossaries, and MCQs
4. **Data Structure Validation**: Ensures all created content has the expected structure
5. **Error Handling**: Tests robustness with minimal content and error conditions

### Setup Requirements

Before running integration tests, you need:

1. **Environment Variables**:
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   export DATABASE_URL="postgresql://user:password@localhost:5432/your_db"
   ```

2. **Database**: A running PostgreSQL instance with the application schema (tables should already exist from migrations)

3. **Cost Optimization**: The test automatically uses `gpt-3.5-turbo` model to keep costs low and execution fast

**Note**: The integration test uses your existing database directly (not a separate test database). This is appropriate for integration testing since we're validating the real workflow. Each test run uses unique UUIDs to avoid data conflicts.

### Running the Tests

#### Run all integration tests:
```bash
# Using the integration test runner
python scripts/run_integration.py

# Or directly with pytest
source venv/bin/activate
python -m pytest tests/ -m integration -v
```

#### Run just the topic creation test:
```bash
source venv/bin/activate
python -m pytest tests/test_topic_creation_integration.py -v
```

#### Run a specific test method:
```bash
source venv/bin/activate
python -m pytest tests/test_topic_creation_integration.py::TestTopicCreationIntegration::test_complete_topic_creation_workflow -v
```

#### Check environment without running tests:
```bash
python scripts/run_integration.py --cost-check
```

### Test Structure

The integration test includes:

- **Environment Setup**: Configures gpt-5-nano model and validates required environment variables
- **Database Fixtures**: Sets up test database with proper schema
- **Sample Data**: Provides realistic source material about Cross-Entropy Loss
- **Comprehensive Validation**: Checks topic structure, component types, and content format
- **Error Scenarios**: Tests handling of minimal content and error conditions

### Expected Behavior

When run successfully, the test will:

1. Create a topic titled "Cross-Entropy Loss in Deep Learning"
2. Generate 2-4 components (didactic snippet, glossary, potentially MCQs)
3. Validate all content has proper JSON structure
4. Verify database persistence
5. Clean up test data

### Cost Considerations

- Uses `gpt-3.5-turbo` model for cost efficiency
- Typical test run costs < $0.01
- Includes cost estimation in the integration runner
- Can be run with `--cost-check` flag to estimate without executing

### Troubleshooting

**Test Skipped**: If you see "SKIPPED" status, check that `OPENAI_API_KEY` and `DATABASE_URL` are set.

**Database Errors**: Ensure PostgreSQL is running, the database exists, and migrations have been run (`alembic upgrade head`).

**LLM Errors**: Verify your OpenAI API key is valid and has sufficient credits.

**Import Errors**: Make sure you're running from the backend directory with the virtual environment activated.

**Pytest Warnings**: The warnings about unknown marks (`integration`, `llm`) are expected and can be ignored. These marks are defined in `pytest.ini`.
