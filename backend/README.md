# Learning System Backend

A modular, extensible backend system for AI-powered learning applications.

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Basic usage**:
   ```python
   from services.learning_service import create_learning_service

   # Create service with your API key
   service = create_learning_service(
       api_key="your-openai-api-key",
       model="gpt-4"
   )

   # Generate a syllabus
   syllabus = await service.generate_syllabus(
       topic="Python Programming",
       user_level="beginner"
   )
   ```

## Architecture Overview

This system follows a **modular, domain-driven architecture**:

- **📁 `core/`** - Shared infrastructure (LLM client, base classes)
- **📁 `modules/`** - Domain-specific capabilities (lesson planning, assessment)
- **📁 `services/`** - Public APIs and orchestration

```
backend/src/
├── core/                    # Shared infrastructure
├── modules/                 # Business domains
│   ├── lesson_planning/     # Syllabus & content generation
│   └── assessment/          # Quiz generation & grading
└── services/                # Public APIs
    └── learning_service.py  # Main API
```

## Key Features

### ✅ Current Capabilities
- **Syllabus Generation**: Create structured learning paths
- **Lesson Content**: Generate engaging educational content
- **Quiz Creation**: Generate various question types
- **Assessment Grading**: AI-powered response evaluation
- **Complete Lesson Plans**: End-to-end course creation

### 🚀 Ready for Extension
- **Didactic Snippets**: Concise concept explanations
- **Glossaries**: Term definitions and vocabularies
- **Socratic Dialogues**: Interactive questioning sequences
- **Multiple Question Types**: Short answer, multiple choice, etc.
- **Post-topic Quizzes**: Comprehensive assessments

## Adding New Functionality

### New Prompt Type
1. Create prompt file in appropriate module
2. Add to service's prompt registry
3. Implement service method
4. Export from module

### New Module
1. Create module structure (`__init__.py`, `service.py`, `prompts.py`)
2. Implement module service inheriting from `ModuleService`
3. Add to main `LearningService`
4. Update exports

## Documentation

- **📖 [Architecture Guide](./ARCHITECTURE.md)** - Comprehensive system design
- **🔧 [API Reference](./docs/api.md)** - Method documentation (coming soon)
- **🧪 [Testing Guide](./docs/testing.md)** - Testing patterns (coming soon)

## Project Structure

```
backend/
├── src/                     # Source code
│   ├── core/               # Shared infrastructure
│   ├── modules/            # Business domains
│   ├── services/           # Public APIs
│   ├── data_structures.py  # Shared data models
│   └── llm_interface.py    # LLM provider abstractions
├── tests/                  # Test suite
├── requirements.txt        # Dependencies
└── start_server.py        # Development server
```

## Development Workflow

1. **Design**: Plan module boundaries and responsibilities
2. **Prompts**: Create and test prompt templates
3. **Services**: Implement business logic and validation
4. **Integration**: Wire into main service API
5. **Testing**: Add unit and integration tests
6. **Documentation**: Update architecture docs

## Configuration

The system uses configuration classes for type safety:

```python
@dataclass
class LearningServiceConfig:
    llm_config: LLMConfig
    default_lesson_duration: int = 15
    max_quiz_questions: int = 10
    mastery_threshold: float = 0.9
    cache_enabled: bool = True
```

## Error Handling

Each module defines specific exceptions:

```python
class LessonPlanningError(Exception):
    """Lesson planning specific errors"""
    pass

class AssessmentError(Exception):
    """Assessment specific errors"""
    pass
```

## Performance Features

- **🚀 Response Caching**: Automatic LLM response caching
- **🔄 Retry Logic**: Exponential backoff for failed requests
- **📊 Health Monitoring**: Service health checks and metrics
- **⚡ Async Support**: Full async/await support for scalability

## Extension Points

The architecture is designed for easy extension:

- **New Learning Modalities**: Adaptive, collaborative, gamified learning
- **New Assessment Types**: Peer review, portfolio, continuous assessment
- **New Content Types**: Interactive simulations, case studies, microlearning
- **New AI Providers**: Easy to add new LLM providers

## Getting Started with Development

1. **Read the [Architecture Guide](./ARCHITECTURE.md)** to understand the system design
2. **Look at existing modules** in `modules/` for patterns
3. **Start with prompts** - create new prompt templates first
4. **Build incrementally** - add one capability at a time
5. **Test thoroughly** - maintain high code quality

## Support

For questions about the architecture or extending the system, refer to:
- Architecture documentation for design patterns
- Existing module implementations for examples
- Test files for usage patterns

Happy coding! 🎓