# Learning App LLM Modules

This directory contains well-structured, documented modules for integrating Large Language Models (LLMs) into the proactive learning application. The modules are designed to be modular, testable, and easily swappable between different LLM providers.

## 📁 Project Structure

This project is organized as a multi-platform application with the following structure:

```
deeplearn/
├── backend/                 # Python backend API
│   ├── src/
│   │   ├── api/            # API endpoints and main app
│   │   ├── services/       # Business logic and services
│   │   ├── config/         # Configuration files
│   │   ├── models/         # Data models
│   │   └── utils/          # Utility functions
│   ├── tests/              # Backend tests
│   ├── logs/               # Application logs
│   └── requirements.txt    # Python dependencies
├── web/                    # NextJS web application
│   ├── src/
│   │   ├── app/           # NextJS app router pages
│   │   ├── components/    # React components
│   │   ├── lib/           # Shared utilities
│   │   └── styles/        # Styling files
│   ├── public/            # Static assets
│   └── prisma/            # Database schema
├── mobile/                 # React Native mobile app
│   ├── src/
│   │   ├── screens/       # Mobile screens
│   │   ├── components/    # Mobile components
│   │   ├── services/      # API services
│   │   ├── utils/         # Utility functions
│   │   └── assets/        # Images and assets
│   ├── android/           # Android-specific code
│   └── ios/               # iOS-specific code
├── README.md              # This file
├── QUICKSTART.md          # Quick start guide
└── learning_app_spec.md   # Application specification
```

## 📁 Module Overview

### Core Modules

1. **`llm_interface.py`** - Abstract LLM interface with OpenAI implementation
2. **`prompt_engineering.py`** - Structured prompt templates and helpers
3. **`learning_service.py`** - High-level service combining LLM and prompts
4. **`data_structures.py`** - Data models and structures
5. **`learning_app_spec.md`** - Complete application specification

## 🚀 Quick Start

### Web Application Setup

To run the NextJS frontend locally:

```bash
# Navigate to web directory
cd web

# Install dependencies
npm install

# Start development server
npm run dev
```

The application will be available at `http://localhost:3000`

### Backend API Setup

To run the Python backend:

```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export OPENAI_API_KEY="your-openai-api-key"

# Run the backend server
python src/api/main.py
```

### Development Commands

**Web Application:**
```bash
cd web
npm run dev      # Start development server
npm run build    # Build for production
npm run start    # Start production server
npm run lint     # Run linting
```

**Backend API:**
```bash
cd backend
python src/api/main.py           # Start API server
python -m pytest tests/         # Run tests
```

### Basic Usage

```python
import asyncio
from learning_service import create_learning_service

async def main():
    # Create service
    service = create_learning_service(
        api_key="your-openai-api-key",
        model="gpt-3.5-turbo"
    )
    
    # Generate syllabus
    syllabus = await service.generate_syllabus(
        topic="Python Programming",
        user_level="beginner"
    )
    
    # Generate lesson content
    lesson = await service.generate_lesson_content(
        topic_title=syllabus['topics'][0]['title'],
        topic_description=syllabus['topics'][0]['description'],
        learning_objectives=syllabus['topics'][0]['learning_objectives']
    )
    
    print(f"Generated lesson: {len(lesson)} characters")

asyncio.run(main())
```

## 📚 Module Documentation

### LLM Interface (`llm_interface.py`)

Provides a clean abstraction layer for interacting with different LLM providers.

#### Key Features:
- **Provider Abstraction**: Easy to swap between OpenAI, Anthropic, etc.
- **Error Handling**: Comprehensive error handling with custom exceptions
- **Retry Logic**: Built-in exponential backoff for rate limits
- **Token Tracking**: Automatic token counting and cost estimation
- **Structured Responses**: Support for JSON schema validation

#### Usage Example:

```python
from llm_interface import LLMConfig, LLMProvider, OpenAIProvider, LLMMessage, MessageRole

# Configure provider
config = LLMConfig(
    provider=LLMProvider.OPENAI,
    model="gpt-3.5-turbo",
    api_key="your-api-key",
    temperature=0.7,
    max_tokens=1000
)

# Create provider
provider = OpenAIProvider(config)

# Generate response
messages = [
    LLMMessage(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
    LLMMessage(role=MessageRole.USER, content="Explain machine learning")
]

response = await provider.generate_response(messages)
print(response.content)
```

#### Error Handling:

```python
from llm_interface import LLMError, LLMRateLimitError, LLMAuthenticationError

try:
    response = await provider.generate_response(messages)
except LLMRateLimitError:
    print("Rate limit exceeded, implement backoff")
except LLMAuthenticationError:
    print("Check your API key")
except LLMError as e:
    print(f"General LLM error: {e}")
```

### Prompt Engineering (`prompt_engineering.py`)

Structured prompt templates for consistent, effective LLM interactions.

#### Key Features:
- **Template System**: Reusable prompt templates for different tasks
- **Context Management**: Structured context passing
- **Validation**: Response format validation
- **Extensibility**: Easy to add new prompt types

#### Available Prompt Types:
- **SYLLABUS_GENERATION**: Generate learning syllabi
- **LESSON_CONTENT**: Create lesson content
- **QUIZ_GENERATION**: Generate quiz questions
- **ASSESSMENT_GRADING**: Grade student responses
- **REVIEW_CONTENT**: Create review sessions
- **DIFFICULTY_ADJUSTMENT**: Adjust content difficulty

#### Usage Example:

```python
from prompt_engineering import PromptFactory, PromptType, create_default_context

# Create context
context = create_default_context(
    user_level="intermediate",
    time_constraint=15
)

# Generate syllabus prompt
prompt = PromptFactory.create_prompt(
    PromptType.SYLLABUS_GENERATION,
    context,
    topic="Data Science",
    user_refinements=["Focus on practical applications"]
)

# Use with LLM provider
response = await provider.generate_response(prompt)
```

### Learning Service (`learning_service.py`)

High-level service combining LLM interface with prompt engineering.

#### Key Features:
- **Complete Learning Operations**: Syllabus, lessons, quizzes, grading
- **Caching**: Optional content caching for performance
- **Progress Analysis**: Learning progress tracking and recommendations
- **Error Recovery**: Comprehensive error handling and retry logic

#### Main Methods:

```python
from learning_service import LearningService, LearningServiceConfig

service = LearningService(config)

# Generate syllabus
syllabus = await service.generate_syllabus(
    topic="Machine Learning",
    user_level="beginner"
)

# Create lesson content
lesson = await service.generate_lesson_content(
    topic_title="Linear Regression",
    topic_description="Introduction to linear regression",
    learning_objectives=["Understand linear relationships", "Apply regression analysis"]
)

# Generate quiz
quiz = await service.generate_quiz(
    topic_title="Linear Regression",
    learning_objectives=["Understand linear relationships"],
    lesson_content=lesson,
    question_count=5
)

# Grade responses
grade = await service.grade_quiz_response(
    question=quiz[0],
    student_answer="Linear regression models relationships between variables",
    user_level="beginner"
)

# Generate review content
review = await service.generate_review_content(
    topic_title="Linear Regression",
    original_content=lesson,
    time_since_study=7,  # days
    user_level="beginner"
)
```

## 🔧 Configuration

### Environment Variables

```bash
# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-3.5-turbo

# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2023-05-15
```

### Configuration Objects

```python
from llm_interface import LLMConfig, LLMProvider
from learning_service import LearningServiceConfig

# LLM Configuration
llm_config = LLMConfig(
    provider=LLMProvider.OPENAI,
    model="gpt-3.5-turbo",
    api_key="your-api-key",
    temperature=0.7,
    max_tokens=1500,
    timeout=30,
    max_retries=3
)

# Service Configuration
service_config = LearningServiceConfig(
    llm_config=llm_config,
    default_lesson_duration=15,
    max_quiz_questions=10,
    mastery_threshold=0.9,
    cache_enabled=True
)
```

## 🧪 Testing

### Unit Tests Example

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from learning_service import LearningService

@pytest.fixture
def mock_service():
    config = MagicMock()
    service = LearningService(config)
    service.llm_provider = AsyncMock()
    return service

@pytest.mark.asyncio
async def test_generate_syllabus(mock_service):
    # Mock LLM response
    mock_response = {
        "topic_name": "Test Topic",
        "description": "Test Description",
        "topics": [
            {
                "title": "Topic 1",
                "description": "Description 1",
                "learning_objectives": ["Objective 1"]
            }
        ]
    }
    
    mock_service.llm_provider.generate_structured_response.return_value = mock_response
    
    result = await mock_service.generate_syllabus("Test Topic")
    
    assert result["topic_name"] == "Test Topic"
    assert len(result["topics"]) == 1
```

### Integration Tests

```python
import asyncio
from learning_service import create_learning_service

async def test_full_workflow():
    """Test complete learning workflow"""
    service = create_learning_service(
        api_key="test-key",
        model="gpt-3.5-turbo"
    )
    
    # Test syllabus generation
    syllabus = await service.generate_syllabus(
        topic="Test Topic",
        user_level="beginner"
    )
    
    assert "topics" in syllabus
    assert len(syllabus["topics"]) > 0
    
    # Test lesson generation
    first_topic = syllabus["topics"][0]
    lesson = await service.generate_lesson_content(
        topic_title=first_topic["title"],
        topic_description=first_topic["description"],
        learning_objectives=first_topic["learning_objectives"]
    )
    
    assert isinstance(lesson, str)
    assert len(lesson) > 100  # Reasonable content length
```

## 📈 Performance Considerations

### Caching Strategy

```python
# Enable caching for better performance
service_config = LearningServiceConfig(
    llm_config=llm_config,
    cache_enabled=True  # Cache lesson content
)

# Cache is automatically used for:
# - Lesson content (based on topic + user level)
# - Reduces API calls for repeated requests
```

### Token Management

```python
# Monitor token usage
response = await provider.generate_response(messages)
print(f"Tokens used: {response.tokens_used}")
print(f"Estimated cost: ${response.cost_estimate}")

# Optimize token usage
config = LLMConfig(
    model="gpt-3.5-turbo",  # More cost-effective than GPT-4
    max_tokens=1000,        # Limit response length
    temperature=0.7         # Balance creativity vs consistency
)
```

## 🔄 Extending the System

### Adding New LLM Providers

```python
from llm_interface import LLMProvider

class AnthropicProvider(LLMProvider):
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        # Setup Anthropic client
    
    async def generate_response(self, messages, **kwargs):
        # Implement Anthropic-specific logic
        pass
    
    async def generate_structured_response(self, messages, schema, **kwargs):
        # Implement structured response
        pass
```

### Adding New Prompt Types

```python
from prompt_engineering import PromptTemplate, PromptType

class CustomPromptTemplate(PromptTemplate):
    def __init__(self):
        super().__init__(PromptType.CUSTOM_TYPE)
    
    def _get_base_instructions(self):
        return "Your custom instructions here"
    
    def generate_prompt(self, context, **kwargs):
        # Generate custom prompt
        pass

# Register in PromptFactory
PromptFactory._templates[PromptType.CUSTOM_TYPE] = CustomPromptTemplate
```

## 🐛 Error Handling

### Common Error Patterns

```python
from llm_interface import LLMError, LLMRateLimitError
from learning_service import ContentGenerationError

try:
    result = await service.generate_syllabus(topic)
except LLMRateLimitError:
    # Implement exponential backoff
    await asyncio.sleep(2 ** retry_count)
    retry_count += 1
except ContentGenerationError as e:
    # Log error and provide fallback
    logger.error(f"Content generation failed: {e}")
    result = get_fallback_content()
except Exception as e:
    # Unexpected error
    logger.error(f"Unexpected error: {e}")
    raise
```

## 📊 Monitoring and Logging

### Structured Logging

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Service logs automatically include:
# - API call metrics
# - Error details
# - Performance statistics
```

### Usage Metrics

```python
# Get service statistics
stats = service.get_service_stats()
print(f"Cache hit rate: {stats['cache_size']}")
print(f"Provider: {stats['provider']}")
print(f"Model: {stats['model']}")
```

## 🔐 Security Considerations

### API Key Management

```python
import os
from pathlib import Path

# Use environment variables
api_key = os.getenv("OPENAI_API_KEY")

# Or secure key management
def load_api_key():
    key_file = Path.home() / ".config" / "learning_app" / "api_key"
    if key_file.exists():
        return key_file.read_text().strip()
    raise ValueError("API key not found")
```

### Input Validation

```python
# All inputs are validated
from learning_service import LearningServiceError

try:
    # Invalid topic length
    await service.generate_syllabus("x" * 1000)
except LearningServiceError as e:
    print(f"Validation error: {e}")
```

## 🚀 Production Deployment

### Docker Configuration

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Health Checks

```python
async def health_check():
    """Health check endpoint"""
    try:
        service = create_learning_service(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-3.5-turbo"
        )
        
        # Simple test
        stats = service.get_service_stats()
        return {"status": "healthy", "stats": stats}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

## 📝 Contributing

### Code Style

- Follow PEP 8
- Use type hints
- Add docstrings to all functions
- Include comprehensive error handling
- Write tests for new features

### Testing Requirements

```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=. tests/

# Run specific test file
pytest tests/test_learning_service.py
```

## 📄 Copyright

Copyright 2025 by Brian Fields. All rights reserved.

## 🤝 Support

For questions or issues:
1. Check the documentation above
2. Review the code comments
3. Create an issue with detailed description
4. Include error messages and stack traces

---

*This module system provides a solid foundation for building AI-powered learning applications with proper separation of concerns, comprehensive error handling, and easy extensibility.*