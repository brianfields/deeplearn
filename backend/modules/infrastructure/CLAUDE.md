# Infrastructure Module

## Purpose
This module provides core technical infrastructure services that support all other modules. It handles database management, LLM integration, configuration, and shared technical utilities without containing any business domain logic.

## Domain Responsibility
**"Providing technical infrastructure services to all modules"**

The Infrastructure module owns all technical infrastructure:
- Database connection management and schema operations
- LLM client integration and prompt management
- Application configuration and environment management
- Shared technical utilities and base classes
- Logging, monitoring, and observability
- External service integrations (non-domain specific)

## Architecture

### Module API (Public Interface)
```python
# module_api/infrastructure_service.py
class InfrastructureService:
    @staticmethod
    def get_database_session() -> DatabaseSession:
        """Get database session for data operations"""

    @staticmethod
    def get_llm_client(provider: LLMProvider = None) -> LLMClient:
        """Get configured LLM client"""

    @staticmethod
    def get_config() -> AppConfig:
        """Get application configuration"""

    @staticmethod
    def execute_prompt(prompt: Prompt, context: PromptContext) -> LLMResponse:
        """Execute LLM prompt with context"""

    @staticmethod
    def validate_environment() -> EnvironmentStatus:
        """Validate infrastructure environment"""

# module_api/types.py
@dataclass
class DatabaseSession:
    session: Session
    connection_id: str

@dataclass
class LLMClient:
    provider: LLMProvider
    model: str
    client: Any

@dataclass
class AppConfig:
    database_url: str
    llm_config: LLMConfig
    api_config: APIConfig
    feature_flags: Dict[str, bool]

@dataclass
class LLMResponse:
    content: str
    metadata: Dict[str, Any]
    usage_stats: UsageStats
```

### Domain Layer (Technical Logic)
```python
# domain/entities/database.py
class DatabaseConnection:
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.engine = None

    def connect(self) -> None:
        """Technical logic for database connection"""
        self.engine = create_engine(self.config.url)

    def validate_connection(self) -> bool:
        """Technical validation of database connectivity"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def get_session(self) -> Session:
        """Technical logic for session creation"""
        return sessionmaker(bind=self.engine)()

# domain/entities/llm.py
class LLMProvider:
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = None

    def initialize_client(self) -> None:
        """Technical logic for LLM client initialization"""
        if self.config.provider == "openai":
            self.client = OpenAI(api_key=self.config.api_key)
        elif self.config.provider == "azure":
            self.client = AzureOpenAI(
                api_key=self.config.api_key,
                endpoint=self.config.endpoint
            )

    def execute_prompt(self, prompt: str, parameters: Dict) -> LLMResponse:
        """Technical logic for prompt execution"""
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[{"role": "user", "content": prompt}],
            **parameters
        )
        return LLMResponse(
            content=response.choices[0].message.content,
            metadata={"model": self.config.model},
            usage_stats=UsageStats(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens
            )
        )

# domain/entities/configuration.py
class Configuration:
    def __init__(self):
        self.values = {}

    def load_from_environment(self) -> None:
        """Technical logic for loading environment variables"""
        self.values = {
            "database_url": os.getenv("DATABASE_URL"),
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "log_level": os.getenv("LOG_LEVEL", "INFO")
        }

    def validate_required_config(self) -> List[str]:
        """Technical validation of required configuration"""
        required = ["database_url", "openai_api_key"]
        missing = [key for key in required if not self.values.get(key)]
        return missing
```

### Infrastructure Layer (Technical Implementation)
```python
# infrastructure/database/connection_manager.py
class ConnectionManager:
    def __init__(self):
        self.connections = {}
        self.pool = None

    def create_connection_pool(self, config: DatabaseConfig) -> None:
        """Create database connection pool"""
        self.pool = create_engine(
            config.url,
            pool_size=config.pool_size,
            max_overflow=config.max_overflow
        )

    def get_connection(self) -> Connection:
        """Get connection from pool"""
        return self.pool.connect()

# infrastructure/llm_clients/openai_client.py
class OpenAIClient:
    def __init__(self, config: OpenAIConfig):
        self.config = config
        self.client = OpenAI(api_key=config.api_key)

    def generate_completion(self, prompt: str, **kwargs) -> str:
        """OpenAI-specific implementation"""
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return response.choices[0].message.content

# infrastructure/config/environment_loader.py
class EnvironmentLoader:
    @staticmethod
    def load_config() -> Dict[str, Any]:
        """Load configuration from environment"""
        load_dotenv()  # Load .env file if present

        return {
            "database": {
                "url": os.getenv("DATABASE_URL"),
                "pool_size": int(os.getenv("DB_POOL_SIZE", "5"))
            },
            "llm": {
                "provider": os.getenv("LLM_PROVIDER", "openai"),
                "api_key": os.getenv("OPENAI_API_KEY"),
                "model": os.getenv("OPENAI_MODEL", "gpt-4")
            }
        }
```

## Cross-Module Communication

### Provides to Other Modules
- **All Modules**: Database sessions, LLM clients, configuration
- **Content Creation Module**: LLM services for content generation
- **Learning Session Module**: Database persistence
- **Learning Analytics Module**: Database queries and aggregations

### Dependencies
- **External Services**: Database (PostgreSQL), LLM providers (OpenAI, Azure)
- **System Environment**: Environment variables, configuration files

### Communication Examples
```python
# All modules access infrastructure via module_api
from modules.infrastructure.module_api import InfrastructureService

# Content Creation module using LLM service
llm_client = InfrastructureService.get_llm_client()
response = InfrastructureService.execute_prompt(mcq_prompt, context)

# Learning Session module using database
db_session = InfrastructureService.get_database_session()
session_data = db_session.query(SessionModel).filter_by(id=session_id).first()
```

## Key Technical Responsibilities

1. **Database Management**: Connection pooling, session management, transaction handling
2. **LLM Integration**: Client initialization, prompt execution, response parsing
3. **Configuration Management**: Environment loading, validation, feature flags
4. **Error Handling**: Infrastructure-level error handling and recovery
5. **Monitoring**: Logging, metrics, health checks
6. **Security**: API key management, connection security

## Data Flow

1. **Database Operations**:
   ```
   Module Request → Get Session → Execute Query → Return Results → Close Session
   ```

2. **LLM Operations**:
   ```
   Prompt Request → Get Client → Execute Prompt → Parse Response → Return Content
   ```

3. **Configuration Loading**:
   ```
   App Start → Load Environment → Validate Config → Initialize Services → Ready State
   ```

## Testing Strategy

### Domain Tests (Technical Logic)
```python
def test_database_connection_validation():
    config = DatabaseConfig(url="sqlite:///:memory:")
    db = DatabaseConnection(config)
    db.connect()

    assert db.validate_connection() == True

def test_llm_provider_initialization():
    config = LLMConfig(provider="openai", api_key="test-key")
    provider = LLMProvider(config)
    provider.initialize_client()

    assert provider.client is not None
```

### Service Tests (Orchestration)
```python
@patch('infrastructure.database.ConnectionManager')
def test_get_database_session(mock_manager):
    session = InfrastructureService.get_database_session()
    mock_manager.get_connection.assert_called_once()
```

### Integration Tests (External Services)
```python
def test_database_connectivity():
    """Test actual database connection"""
    db_session = InfrastructureService.get_database_session()
    result = db_session.execute(text("SELECT 1")).scalar()
    assert result == 1

def test_llm_client_integration():
    """Test actual LLM API call"""
    llm_client = InfrastructureService.get_llm_client()
    response = llm_client.generate_completion("Hello, world!")
    assert len(response) > 0
```

## Configuration Management

### Environment Variables
```bash
# Database Configuration
DATABASE_URL=postgresql://user:pass@localhost:5432/deeplearn
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# LLM Configuration
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4
OPENAI_BASE_URL=https://api.openai.com/v1

# Application Configuration
LOG_LEVEL=INFO
DEBUG=false
FEATURE_FLAG_NEW_UI=true
```

### Configuration Validation
```python
def validate_environment() -> EnvironmentStatus:
    """Validate all required configuration is present"""
    config = InfrastructureService.get_config()

    errors = []
    if not config.database_url:
        errors.append("DATABASE_URL not configured")
    if not config.llm_config.api_key:
        errors.append("LLM API key not configured")

    return EnvironmentStatus(
        is_valid=len(errors) == 0,
        errors=errors
    )
```

## Anti-Patterns to Avoid

❌ **Business domain logic in infrastructure**
❌ **Direct database access from other modules**
❌ **LLM prompts containing business rules**
❌ **Configuration scattered across modules**
❌ **Infrastructure services with business knowledge**

## Performance Considerations

- **Connection Pooling**: Efficient database connection management
- **LLM Caching**: Cache LLM responses for repeated prompts
- **Configuration Caching**: Cache loaded configuration in memory
- **Resource Management**: Proper cleanup of connections and resources

## Security Considerations

- **API Key Management**: Secure storage and rotation of API keys
- **Database Security**: Connection encryption, credential management
- **Input Validation**: Validate all inputs to external services
- **Error Handling**: Don't expose sensitive information in errors

## Module Evolution

This module can be extended with:
- **Multiple LLM Providers**: Support for additional LLM services
- **Advanced Database Features**: Read replicas, sharding, migrations
- **Monitoring Integration**: Metrics, tracing, alerting
- **Caching Layer**: Redis integration for performance
- **Message Queues**: Async processing capabilities

The infrastructure module provides a stable foundation that allows other modules to focus on business logic while abstracting away technical complexity.
