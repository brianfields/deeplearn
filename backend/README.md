# DeepLearn Backend - AI Learning Platform API

FastAPI-based backend for the DeepLearn platform, featuring PostgreSQL database, SQLAlchemy ORM, and OpenAI integration for intelligent content generation.

## 🏗️ Architecture

The backend follows a modular architecture with clear separation of concerns:

```
backend/
├── src/
│   ├── api/                    # FastAPI REST endpoints
│   │   ├── server.py          # Main application server
│   │   ├── routes.py          # HTTP endpoints
│   │   ├── websocket.py       # WebSocket handlers
│   │   ├── models.py          # Pydantic request/response models
│   │   └── connection_manager.py # WebSocket connection management
│   ├── modules/               # Core learning modules
│   │   ├── lesson_planning/   # Lesson and content generation
│   │   └── assessment/        # Quiz and assessment generation
│   ├── config/                # Configuration management
│   │   ├── config.py         # Environment configuration
│   │   └── test_config.py    # Testing configuration
│   ├── database_service.py    # PostgreSQL data access layer
│   ├── data_structures.py     # SQLAlchemy models and Pydantic schemas
│   ├── enhanced_conversational_learning.py # AI conversation engine
│   ├── teaching_engine.py     # Adaptive teaching strategies
│   └── llm_interface.py       # OpenAI API abstraction
├── alembic/                   # Database migrations
├── tests/                     # Test suite
├── migrate_to_postgres.py     # Data migration utility
└── requirements.txt           # Python dependencies
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.9+**
- **PostgreSQL 12+**
- **OpenAI API Key**

### Installation

```bash
# Clone and navigate
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials
```

### Database Setup

```bash
# Create PostgreSQL database
createdb deeplearn
createuser deeplearn_user

# Generate initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

### Start Development Server

```bash
# Run the FastAPI server
python -m src.api.server

# Server runs on http://localhost:8000
# API docs available at http://localhost:8000/docs
```

## 🛠️ Key Components

### Database Service (`database_service.py`)

PostgreSQL-based data access layer replacing the previous file-based storage:

```python
from database_service import get_database_service

# Get service instance
db_service = get_database_service()

# Save learning path
db_service.save_learning_path(learning_path)

# Get learning path
learning_path = db_service.get_learning_path(path_id)

# Work with sessions
with db_service.get_session() as session:
    topics = session.execute(select(BiteSizedTopic)).scalars().all()
```

### Data Structures (`data_structures.py`)

SQLAlchemy models for PostgreSQL and Pydantic schemas for API:

```python
# SQLAlchemy Models (Database)
from data_structures import LearningPath, Topic, BiteSizedTopic

# Pydantic Models (API)
from data_structures import SimpleLearningPath, SimpleProgress
```

### API Server (`src/api/server.py`)

FastAPI application with automatic service initialization:

```python
# Global services available to all endpoints
database: DatabaseService      # PostgreSQL data access
learning_service: LearningService  # AI content generation
conversation_engine: EnhancedConversationalLearningEngine  # Chat system
```

### Conversation Engine (`enhanced_conversational_learning.py`)

AI-powered conversational learning with teaching strategies:

```python
# Start conversation
session = conversation_engine.start_conversation(learning_path_id, topic_id)

# Process user message
ai_response, progress = await conversation_engine.process_user_message(user_message)
```

### Bite-Sized Content System

PostgreSQL-based storage for AI-generated educational content:

```python
from modules.lesson_planning.bite_sized_topics.postgresql_storage import PostgreSQLTopicRepository

# Store topic content
repository = PostgreSQLTopicRepository()
topic_id = await repository.store_topic(topic_content)

# Retrieve content
topic_content = await repository.get_topic(topic_id)
```

## 🗄️ Database Schema

### Core Tables

- **`learning_paths`**: User learning journeys with topics
- **`topics`**: Individual learning topics with objectives
- **`bite_sized_topics`**: AI-generated educational content
- **`bite_sized_components`**: Content components (lessons, quizzes, dialogues)
- **`learning_sessions`**: User interaction tracking
- **`topic_progress`**: Progress tracking per topic

### Key Features

- **UUID primary keys** for distributed systems
- **JSON columns** for flexible content storage
- **Proper indexing** for query performance
- **Foreign key constraints** for data integrity
- **Timestamps** for audit trails

## 🔧 Configuration

### Environment Variables

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/deeplearn
# OR
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=deeplearn
DATABASE_USER=username
DATABASE_PASSWORD=password

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-3.5-turbo

# Learning Configuration
USER_LEVEL=beginner
LESSON_DURATION=15
TEMPERATURE=0.7
MAX_TOKENS=1500

# Development
DEBUG=false
LOG_LEVEL=INFO
DATABASE_ECHO=false  # Set to true to see SQL queries
```

### Service Configuration

The system automatically loads configuration and initializes services:

```python
from config.config import config_manager

# Get database configuration
db_config = config_manager.get_database_config()

# Get LLM configuration
llm_config = config_manager.get_llm_config()
```

## 📡 API Endpoints

### REST Endpoints

- `GET /api/progress` - Get learning progress
- `GET /api/learning-paths` - List all learning paths
- `POST /api/start-topic` - Create new learning path
- `POST /api/chat` - Send chat message
- `GET /api/health` - Health check

### WebSocket Endpoints

- `WS /ws/{client_id}` - Real-time conversation interface

### API Documentation

Interactive API documentation available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🧪 Testing

### Run Test Suite

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_conversational.py

# Run with coverage
python -m pytest --cov=src tests/
```

### Integration Tests

Test the complete system with real OpenAI API calls:

```bash
python tests/test_bite_sized_integration.py
```

## 🔍 Management Scripts

### Content Inspection

```bash
# Quick overview
python quick_inspect.py --all

# Interactive inspector
python inspect_bite_sized_content.py

# Specific topic details
python quick_inspect.py --topic "Machine Learning"
```

### Content Generation

```bash
# Generate content for all paths
python generate_bite_sized_content.py

# Generate for specific path
python generate_bite_sized_content.py --path-id path_12345
```

### Data Migration

```bash
# Migrate from SQLite (if needed)
python migrate_to_postgres.py --dry-run
python migrate_to_postgres.py --backup
```

## 🗄️ Database Management

### Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Add new feature"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Show migration history
alembic history
```

### Database Operations

```bash
# Connect to database
psql -d deeplearn

# Backup database
pg_dump deeplearn > backup.sql

# Restore database
psql deeplearn < backup.sql
```

## 🐛 Debugging

### Enable SQL Logging

```bash
# In .env file
DATABASE_ECHO=true
```

### Check Service Health

```bash
# Test database connection
python -c "
from src.database_service import get_database_service
db = get_database_service()
print('Database connection: OK')
"

# Test OpenAI connection
python -c "
from src.config.config import config_manager
from src.llm_interface import create_llm_provider
provider = create_llm_provider(config_manager.get_llm_config())
print('OpenAI connection: OK')
"
```

### Common Issues

**Import Errors:**
- Ensure you're in the backend directory
- Check Python path and virtual environment

**Database Connection:**
- Verify PostgreSQL is running: `pg_isready`
- Check DATABASE_URL format
- Confirm database exists and user has permissions

**OpenAI API:**
- Verify API key is valid and has credits
- Check rate limits and usage quotas

## 🚀 Performance

### Database Optimization

- **Connection pooling**: Configured with 5 base connections, 10 overflow
- **Indexes**: Optimized for common query patterns
- **Query optimization**: Use SQLAlchemy's efficient ORM patterns

### Caching Strategy

- **Session storage**: PostgreSQL-based session management
- **Content caching**: Database-level caching for generated content
- **Connection reuse**: Persistent database connections

### Monitoring

```python
# Get database service stats
with db_service.get_session() as session:
    # Monitor connection pool
    engine_stats = session.get_bind().pool.status()
    print(f"Pool status: {engine_stats}")
```

## 🔐 Security

### API Security

- **Input validation**: Pydantic models validate all inputs
- **SQL injection protection**: SQLAlchemy ORM prevents injection
- **Environment variables**: Sensitive data in environment variables
- **CORS configuration**: Properly configured for frontend domains

### Database Security

- **User permissions**: Dedicated database user with minimal privileges
- **Connection encryption**: SSL connections for production
- **Password security**: Environment-based credential management

## 📚 Development Guidelines

### Code Style

- **Type hints**: All functions have proper type annotations
- **Docstrings**: Comprehensive documentation
- **Error handling**: Proper exception handling throughout
- **Testing**: Unit tests for all major functions

### Adding New Features

1. **Database changes**: Create Alembic migration
2. **API endpoints**: Add to `routes.py` with proper models
3. **Business logic**: Implement in appropriate modules
4. **Tests**: Add unit and integration tests
5. **Documentation**: Update relevant docs

### Module Structure

```python
# Example new module structure
src/modules/new_feature/
├── __init__.py
├── service.py          # Main business logic
├── models.py           # Data models
├── storage.py          # Database operations
└── prompts/            # AI prompt templates
    ├── __init__.py
    └── feature_prompts.py
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**For more information**, see the main [README.md](../README.md) and [PostgreSQL Migration Guide](POSTGRES_MIGRATION_GUIDE.md).