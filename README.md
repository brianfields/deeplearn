# DeepLearn - AI-Powered Learning Platform

An intelligent learning platform that creates personalized educational experiences using AI, built with modern web technologies and PostgreSQL.

## 🌟 Features

- **AI-Generated Learning Paths**: Create comprehensive syllabi tailored to your learning goals
- **Bite-Sized Content**: Break down complex topics into digestible learning modules
- **Interactive Conversations**: Socratic dialogue system for deeper understanding
- **Real-Time Progress Tracking**: Monitor your learning journey with detailed analytics
- **Modern Architecture**: FastAPI backend, Next.js frontend, PostgreSQL database

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Next.js Web   │    │  FastAPI API    │    │   PostgreSQL    │
│    Frontend     │◄──►│     Backend     │◄──►│    Database     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                         │
                              │                ┌─────────────────┐
                              │                │      Redis      │
                              │                │  (Task Queue)   │
                              │                └─────────────────┘
                              │                         │
                              ▼                         │
                       ┌─────────────────┐              │
                       │   OpenAI API    │              │
                       │  (GPT Models)   │              │
                       └─────────────────┘              │
                                                        ▼
                                               ┌─────────────────┐
                                               │  ARQ Workers    │
                                               │ (Background     │
                                               │   Tasks)       │
                                               └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.9+ and pip
- **PostgreSQL** 12+
- **Redis** 6+ (for background task queue)
- **OpenAI API Key** (for content generation)

### 1. Database Setup

#### Install PostgreSQL

**macOS (Homebrew):**
```bash
brew install postgresql
brew services start postgresql
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**Windows:**
Download and install from [postgresql.org](https://www.postgresql.org/download/windows/)

#### Create Database

```bash
# Create database and user
createdb deeplearn
createuser --interactive deeplearn_user

# Grant permissions
psql -d deeplearn -c "GRANT ALL PRIVILEGES ON DATABASE deeplearn TO deeplearn_user;"
```

### 2. Redis Setup

#### Install Redis

**macOS (Homebrew):**
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**Windows:**
Download and install from [redis.io](https://redis.io/download) or use WSL.

#### Verify Redis Installation

```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG
```

### 3. Backend Setup

```bash
# Navigate to backend
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your PostgreSQL credentials and OpenAI API key
```

**Required Environment Variables:**
```bash
# Database (choose one method)
DATABASE_URL=postgresql://username:password@localhost:5432/deeplearn
# OR individual components:
# DATABASE_HOST=localhost
# DATABASE_PORT=5432
# DATABASE_NAME=deeplearn
# DATABASE_USER=username
# DATABASE_PASSWORD=password

# Redis (choose one method)
REDIS_URL=redis://localhost:6379/0
# OR individual components:
# REDIS_HOST=localhost
# REDIS_PORT=6379
# REDIS_PASSWORD=your_redis_password  # (optional)
# REDIS_DB=0

# OpenAI
OPENAI_API_KEY=your_openai_api_key_here
```

#### Initialize Database Schema

```bash
# Generate initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migration
alembic upgrade head
```

#### Start Backend Server

```bash
# Development mode
python -m src.api.server

# Server will run on http://localhost:8000
```

### 4. Frontend Setup

```bash
# Navigate to frontend
cd web

# Install dependencies
npm install

# Start development server
npm run dev

# Frontend will run on http://localhost:3000
```

### 5. Background Workers (Optional)

For background task processing (flow execution), start ARQ workers:

```bash
# Navigate to backend
cd backend

# Start a worker (in a separate terminal)
python scripts/start_worker.py

# With custom settings
python scripts/start_worker.py --max-jobs 5 --log-level DEBUG
```

**Note**: Background workers are required for long-running flows but not for basic API operations.

### 6. Verify Installation

Visit `http://localhost:3000` and:
1. Create a new learning path
2. Generate bite-sized content
3. Start a conversation
4. Check progress tracking

## 📖 Usage

### Creating Learning Paths

1. **Via Web Interface**: Go to `/learn` and enter your topic
2. **Via API**: POST to `/api/start-topic` with topic and user level
3. **Via CLI**: Use backend CLI tools for batch operations

### Managing Content

**Inspect Learning Content:**
```bash
cd backend

# Quick overview
python quick_inspect.py --all

# Interactive inspector
python inspect_bite_sized_content.py

# Specific topic details
python quick_inspect.py --topic "Machine Learning"
```

**Generate Bite-Sized Content:**
```bash
# Generate for all learning paths
python generate_bite_sized_content.py

# Generate for specific path
python generate_bite_sized_content.py --path-id your_path_id
```

### API Endpoints

- `GET /api/progress` - Get learning progress
- `GET /api/learning-paths` - List all learning paths
- `POST /api/start-topic` - Create new learning path
- `POST /api/chat` - Send chat message
- `WebSocket /ws/{client_id}` - Real-time conversations

## 🛠️ Development

### Project Structure

```
deeplearn/
├── backend/                 # Python FastAPI backend
│   ├── src/
│   │   ├── api/            # REST API endpoints
│   │   ├── modules/        # Learning engine modules
│   │   ├── config/         # Configuration management
│   │   └── database_service.py # PostgreSQL data access
│   ├── alembic/            # Database migrations
│   ├── migrate_to_postgres.py # Data migration script
│   └── requirements.txt    # Python dependencies
├── web/                    # Next.js frontend
│   ├── src/
│   │   ├── app/           # Next.js 13+ app router
│   │   ├── components/    # React components
│   │   ├── hooks/         # Custom React hooks
│   │   └── services/      # API client services
│   └── package.json       # Node.js dependencies
└── README.md              # This file
```

### Key Technologies

**Backend:**
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: Database ORM with PostgreSQL
- **Alembic**: Database migration management
- **Pydantic**: Data validation and serialization
- **ARQ**: Async Redis Queue for background tasks
- **OpenAI API**: GPT models for content generation

**Frontend:**
- **Next.js 13+**: React framework with app router
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first CSS framework
- **Shadcn/ui**: Modern React component library

**Database & Queue:**
- **PostgreSQL**: Production-grade relational database
- **Redis**: In-memory data structure store for task queuing
- **Connection pooling**: Optimized database connections
- **Migrations**: Version-controlled schema changes

### Database Schema

Key tables:
- `learning_paths`: User learning journeys
- `topics`: Individual learning topics
- `bite_sized_topics`: AI-generated educational content
- `bite_sized_components`: Content components (lessons, quizzes, etc.)
- `learning_sessions`: User interaction tracking

### Adding New Features

1. **Backend**: Add new API endpoints in `src/api/routes.py`
2. **Frontend**: Create components in `src/components/`
3. **Database**: Create migrations with `alembic revision --autogenerate`
4. **AI Integration**: Extend modules in `src/modules/`

## 🗄️ Data Migration

If you have existing SQLite data, use the migration script:

```bash
cd backend

# See what would be migrated
python migrate_to_postgres.py --dry-run

# Migrate with backup
python migrate_to_postgres.py --backup

# Check migration success
python quick_inspect.py --all
```

## 🔧 Configuration

### Environment Variables

See `backend/.env.example` for all configuration options including:
- Database connection settings
- OpenAI API configuration
- Learning algorithm parameters
- Logging and debugging options

### Database Tuning

For production deployments:
- Adjust PostgreSQL connection pool settings
- Configure appropriate indexes for your query patterns
- Set up regular maintenance (VACUUM, ANALYZE)
- Consider read replicas for scaling

## 🐛 Troubleshooting

### Database Issues

**Connection errors:**
- Verify PostgreSQL is running: `pg_isready`
- Check DATABASE_URL format and credentials
- Ensure database exists: `psql -l | grep deeplearn`

**Migration issues:**
- Reset migrations: `alembic downgrade base && alembic upgrade head`
- Check Alembic configuration in `alembic.ini`

### Redis Issues

**Connection errors:**
- Verify Redis is running: `redis-cli ping`
- Check REDIS_URL format and credentials
- Ensure Redis is accessible on the configured port

**Background task issues:**
- Check if workers are running: `ps aux | grep start_worker`
- Monitor worker logs for errors
- Verify queue status: `redis-cli LLEN arq:queue:default`

### API Issues

**Import errors:**
- Ensure you're in the backend directory
- Verify virtual environment is activated
- Check all dependencies are installed: `pip install -r requirements.txt`

**OpenAI API errors:**
- Verify API key is valid and has credits
- Check rate limits and quota usage
- Ensure proper model access permissions

### Frontend Issues

**Build errors:**
- Clear Next.js cache: `rm -rf .next`
- Reinstall dependencies: `rm -rf node_modules && npm install`
- Check Node.js version compatibility

## 📚 Documentation

- [Backend Architecture](backend/ARCHITECTURE.md)
- [PostgreSQL Migration Guide](backend/POSTGRES_MIGRATION_GUIDE.md)
- [API Documentation](backend/CLI_COMPREHENSIVE_GUIDE.md)
- [Frontend Components](web/ARCHITECTURE.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Commit your changes: `git commit -m 'Add amazing feature'`
5. Push to the branch: `git push origin feature/amazing-feature`
6. Open a Pull Request

### Development Workflow

1. **Database changes**: Create migrations with Alembic
2. **API changes**: Update both backend and frontend
3. **Testing**: Run backend tests and frontend type checking
4. **Documentation**: Update relevant docs for changes

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for providing the GPT models
- FastAPI and Next.js communities
- PostgreSQL development team
- All contributors and users of this platform

---

**Need help?** Check our troubleshooting guide above or open an issue on GitHub.