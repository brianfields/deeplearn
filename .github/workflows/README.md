# GitHub Actions Workflows

This directory contains GitHub Actions workflows for automated testing and CI/CD.

## Workflows

### 1. `tests.yml` - Comprehensive Backend Testing

**Purpose**: Run all backend tests including database migrations and comprehensive test coverage.

**Triggers**:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches
- Changes to `backend/**` files

**Features**:
- Python 3.11 support
- PostgreSQL 15 database service
- Pip dependency caching
- Database migrations with Alembic
- Optional linting with flake8
- JUnit XML test results
- Test result artifacts

**Test Coverage**:
- MCQ functionality tests (new)
- All existing backend tests
- Database integration tests

## Environment Variables

The workflows use these environment variables:

- `DATABASE_URL`: PostgreSQL connection string (backend-tests.yml only)
- `OPENAI_API_KEY`: OpenAI API key (set to test_key for testing)
- `PYTHONPATH`: Python path for imports
- `ENVIRONMENT`: Set to 'test' for test environment

## Test Results

- Test results are uploaded as artifacts with 30-day retention
- JUnit XML format for integration with GitHub's test reporting
- Detailed summaries in the GitHub Actions summary

## Usage

These workflows will automatically run on:
1. Push to main/develop branches
2. Pull requests to main/develop branches
3. Manual triggering (workflow_dispatch)

## Troubleshooting

### Common Issues:

1. **Database Connection Issues**: The PostgreSQL service has health checks and the workflow waits for it to be ready
2. **Import Errors**: PYTHONPATH is set to include the backend/src directory
3. **Test Failures**: Check the detailed test output in the workflow logs and downloaded artifacts
4. **Timeout Issues**: Workflows have reasonable timeouts (15-30 minutes)

### Debugging:

1. Check the workflow logs for detailed error messages
2. Download test result artifacts for offline analysis
3. Run tests locally with the same environment variables
4. Use the test-workflow.yml for basic validation

## Dependencies

The workflows require these files to be present:
- `backend/requirements.txt` - Python dependencies
- `backend/pytest.ini` - Pytest configuration
- `backend/tests/test_mcq_*.py` - MCQ test files
- `backend/alembic.ini` - Database migration configuration (optional)

## Future Enhancements

Potential improvements for these workflows:
- Add code coverage reporting
- Implement parallel test execution
- Add security scanning
- Include performance benchmarks
- Add deployment workflows
- Matrix testing across multiple Python versions