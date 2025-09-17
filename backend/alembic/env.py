from logging.config import fileConfig
import os
from pathlib import Path
import sys

from sqlalchemy import engine_from_config, pool

from alembic import context

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    # Look for .env file in the backend directory (parent of alembic directory)
    backend_dir = Path(__file__).parent.parent
    env_file = backend_dir / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    else:
        # Also try the root directory
        root_env = backend_dir.parent / ".env"
        if root_env.exists():
            load_dotenv(root_env)
except ImportError:
    # python-dotenv not available, continue without it
    pass

# Add backend directory to Python path to import our modules
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

# Import our models - handle import errors gracefully
try:
    # Import the main Base class
    # Import all model modules to register them with the Base metadata
    # This ensures all tables are included in migrations
    from modules.content.models import LessonModel  # noqa: F401
    from modules.flow_engine.models import FlowRunModel, FlowStepRunModel  # noqa: F401
    from modules.learning_session.models import LearningSessionModel  # noqa: F401
    from modules.llm_services.models import LLMRequestModel  # noqa: F401
    from modules.shared_models import Base

    target_metadata = Base.metadata
    print(f"✅ Successfully imported models. Found {len(Base.metadata.tables)} tables.")
except ImportError as e:
    print(f"Warning: Could not import models: {e}")
    target_metadata = None

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def get_database_url() -> str:
    """Get database URL from environment or config"""
    # First try environment variable
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    # Config system not available - provide helpful error message
    print("Database configuration error:")
    print("Please set DATABASE_URL environment variable")
    print("Example: DATABASE_URL=postgresql://user:password@localhost:5432/deeplearn")
    sys.exit(1)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Get database URL
    database_url = get_database_url()

    # Update the alembic configuration with our database URL
    configuration = config.get_section(config.config_ini_section)
    if configuration is None:
        configuration = {}
    configuration["sqlalchemy.url"] = database_url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
