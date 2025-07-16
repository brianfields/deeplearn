"""
Configuration Module for Proactive Learning App

This module handles environment variable loading and configuration management.
Supports both .env files and environment variables.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

# Try to import python-dotenv for .env file support
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

from llm_interface import LLMConfig, LLMProviderType

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class AppConfig:
    """Main application configuration"""
    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-3.5-turbo"
    openai_base_url: str = "https://api.openai.com/v1"

    # Azure OpenAI Configuration
    azure_openai_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_version: str = "2023-05-15"

    # Database Configuration
    database_url: Optional[str] = None
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "deeplearn"
    database_user: str = "postgres"
    database_password: Optional[str] = None
    database_echo: bool = False  # SQLAlchemy echo for debugging

    # Learning Configuration
    user_level: str = "beginner"
    lesson_duration: int = 15
    mastery_threshold: float = 0.9
    passing_threshold: float = 0.7

    # Data Storage
    data_directory: str = ".learning_data"
    cache_enabled: bool = True

    # API Configuration
    max_retries: int = 3
    request_timeout: int = 30
    temperature: float = 0.7
    max_tokens: int = 1500

    # Quiz Configuration
    max_quiz_questions: int = 10
    min_quiz_questions: int = 3
    default_question_count: int = 5

    # Logging Configuration
    log_level: str = "INFO"
    log_file: Optional[str] = None

    # Development Configuration
    debug: bool = False
    rich_console: bool = True

class ConfigManager:
    """Configuration manager for the learning app"""

    def __init__(self, env_file: Optional[str] = None):
        self.env_file = env_file or ".env"
        self.config = AppConfig()
        self._load_configuration()

    def _load_configuration(self) -> None:
        """Load configuration from environment variables and .env file"""

        # Load .env file if available
        if DOTENV_AVAILABLE:
            env_path = Path(self.env_file)
            if env_path.exists():
                load_dotenv(env_path)
                logger.info(f"Loaded environment variables from {env_path}")
            else:
                # Try backend directory as fallback
                backend_env = Path(__file__).parent.parent.parent / ".env"
                if backend_env.exists():
                    load_dotenv(backend_env)
                    logger.info(f"Loaded environment variables from {backend_env}")
                else:
                    # Try root directory as final fallback
                    root_env = Path(__file__).parent.parent.parent.parent / ".env"
                    if root_env.exists():
                        load_dotenv(root_env)
                        logger.info(f"Loaded environment variables from {root_env}")
                    else:
                        logger.info(f"No .env file found in current directory, backend directory, or root directory")
        else:
            logger.warning("python-dotenv not installed. Install with: pip install python-dotenv")

        # Load configuration from environment variables
        self.config.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.config.openai_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.config.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

        # Azure OpenAI
        self.config.azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.config.azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.config.azure_openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")

        # Database Configuration
        self.config.database_url = os.getenv("DATABASE_URL")
        self.config.database_host = os.getenv("DATABASE_HOST", "localhost")
        self.config.database_port = int(os.getenv("DATABASE_PORT", "5432"))
        self.config.database_name = os.getenv("DATABASE_NAME", "deeplearn")
        self.config.database_user = os.getenv("DATABASE_USER", "postgres")
        self.config.database_password = os.getenv("DATABASE_PASSWORD")
        self.config.database_echo = os.getenv("DATABASE_ECHO", "false").lower() == "true"

        # Learning Configuration
        self.config.user_level = os.getenv("USER_LEVEL", "beginner")
        self.config.lesson_duration = int(os.getenv("LESSON_DURATION", "15"))
        self.config.mastery_threshold = float(os.getenv("MASTERY_THRESHOLD", "0.9"))
        self.config.passing_threshold = float(os.getenv("PASSING_THRESHOLD", "0.7"))

        # Data Storage
        self.config.data_directory = os.getenv("DATA_DIRECTORY", ".learning_data")
        self.config.cache_enabled = os.getenv("CACHE_ENABLED", "true").lower() == "true"

        # API Configuration
        self.config.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        self.config.request_timeout = int(os.getenv("REQUEST_TIMEOUT", "30"))
        self.config.temperature = float(os.getenv("TEMPERATURE", "0.7"))
        self.config.max_tokens = int(os.getenv("MAX_TOKENS", "1500"))

        # Quiz Configuration
        self.config.max_quiz_questions = int(os.getenv("MAX_QUIZ_QUESTIONS", "10"))
        self.config.min_quiz_questions = int(os.getenv("MIN_QUIZ_QUESTIONS", "3"))
        self.config.default_question_count = int(os.getenv("DEFAULT_QUESTION_COUNT", "5"))

        # Logging Configuration
        self.config.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.config.log_file = os.getenv("LOG_FILE")

        # Development Configuration
        self.config.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.config.rich_console = os.getenv("RICH_CONSOLE", "true").lower() == "true"

    def get_llm_config(self) -> LLMConfig:
        """Get LLM configuration"""

        # Determine provider based on available keys
        if self.config.azure_openai_api_key and self.config.azure_openai_endpoint:
            provider = LLMProviderType.AZURE_OPENAI
            api_key = self.config.azure_openai_api_key
            base_url = self.config.azure_openai_endpoint
        elif self.config.openai_api_key:
            provider = LLMProviderType.OPENAI
            api_key = self.config.openai_api_key
            base_url = self.config.openai_base_url
        else:
            raise ValueError("No API key found. Please set OPENAI_API_KEY or AZURE_OPENAI_API_KEY")

        return LLMConfig(
            provider=provider,
            model=self.config.openai_model,
            api_key=api_key,
            base_url=base_url,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            timeout=self.config.request_timeout,
            max_retries=self.config.max_retries
        )

    def get_database_url(self) -> str:
        """Get database URL for SQLAlchemy connection"""
        if self.config.database_url:
            return self.config.database_url

        if not self.config.database_password:
            raise ValueError("Database password is required. Set DATABASE_PASSWORD or DATABASE_URL")

        return (f"postgresql://{self.config.database_user}:{self.config.database_password}"
                f"@{self.config.database_host}:{self.config.database_port}"
                f"/{self.config.database_name}")

    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration for SQLAlchemy engine"""
        return {
            "url": self.get_database_url(),
            "echo": self.config.database_echo,
            "pool_size": 5,
            "max_overflow": 10,
            "pool_recycle": 3600
        }



    def get_settings_dict(self) -> Dict[str, Any]:
        """Get settings dictionary for backward compatibility"""

        return {
            'user_level': self.config.user_level,
            'lesson_duration': self.config.lesson_duration,
            'openai_api_key': self.config.openai_api_key or '',
            'openai_model': self.config.openai_model,
            'mastery_threshold': self.config.mastery_threshold,
            'passing_threshold': self.config.passing_threshold,
            'cache_enabled': self.config.cache_enabled,
            'debug': self.config.debug
        }

    def setup_logging(self) -> None:
        """Setup logging configuration"""

        # Configure logging level
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)

        # Setup logging configuration
        logging_config = {
            'level': log_level,
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }

        # Add file handler if log file is specified
        if self.config.log_file:
            logging_config['filename'] = self.config.log_file
            logging_config['filemode'] = 'a'

        logging.basicConfig(**logging_config)

        # Set specific logger levels
        if self.config.debug:
            logging.getLogger('learning_app').setLevel(logging.DEBUG)
        else:
            logging.getLogger('learning_app').setLevel(log_level)

    def validate_config(self) -> bool:
        """Validate configuration"""

        errors = []

        # Check API key
        if not self.config.openai_api_key and not self.config.azure_openai_api_key:
            errors.append("No API key configured. Set OPENAI_API_KEY or AZURE_OPENAI_API_KEY")

        # Check thresholds
        if not 0 <= self.config.mastery_threshold <= 1:
            errors.append("MASTERY_THRESHOLD must be between 0 and 1")

        if not 0 <= self.config.passing_threshold <= 1:
            errors.append("PASSING_THRESHOLD must be between 0 and 1")

        if self.config.passing_threshold >= self.config.mastery_threshold:
            errors.append("PASSING_THRESHOLD must be less than MASTERY_THRESHOLD")

        # Check quiz configuration
        if self.config.min_quiz_questions >= self.config.max_quiz_questions:
            errors.append("MIN_QUIZ_QUESTIONS must be less than MAX_QUIZ_QUESTIONS")

        # Check lesson duration
        if self.config.lesson_duration <= 0:
            errors.append("LESSON_DURATION must be positive")

        # Check temperature
        if not 0 <= self.config.temperature <= 2:
            errors.append("TEMPERATURE must be between 0 and 2")

        if errors:
            for error in errors:
                logger.error(f"Configuration error: {error}")
            return False

        return True

    def print_config_summary(self) -> None:
        """Print configuration summary"""

        print("🔧 Configuration Summary")
        print("=" * 40)

        # API Configuration
        if self.config.openai_api_key:
            api_key_display = f"{self.config.openai_api_key[:8]}...{self.config.openai_api_key[-4:]}"
        elif self.config.azure_openai_api_key:
            api_key_display = f"Azure: {self.config.azure_openai_api_key[:8]}...{self.config.azure_openai_api_key[-4:]}"
        else:
            api_key_display = "Not configured"

        print(f"API Key: {api_key_display}")
        print(f"Model: {self.config.openai_model}")
        print(f"User Level: {self.config.user_level}")
        print(f"Lesson Duration: {self.config.lesson_duration} minutes")
        print(f"Mastery Threshold: {self.config.mastery_threshold:.0%}")
        print(f"Cache Enabled: {self.config.cache_enabled}")
        print(f"Debug Mode: {self.config.debug}")
        print(f"Data Directory: {self.config.data_directory}")
        print("=" * 40)

# Global configuration manager instance
config_manager = ConfigManager()

# Convenience functions
def get_config() -> AppConfig:
    """Get application configuration"""
    return config_manager.config

def get_llm_config() -> LLMConfig:
    """Get LLM configuration"""
    return config_manager.get_llm_config()



def setup_logging() -> None:
    """Setup logging"""
    config_manager.setup_logging()

def validate_config() -> bool:
    """Validate configuration"""
    return config_manager.validate_config()

def print_config_summary() -> None:
    """Print configuration summary"""
    config_manager.print_config_summary()

# Example usage and testing
if __name__ == "__main__":
    print("🧪 Testing Configuration Module")
    print("=" * 40)

    # Test configuration loading
    try:
        config = get_config()
        print("✅ Configuration loaded successfully")

        # Print summary
        print_config_summary()

        # Test validation
        if validate_config():
            print("✅ Configuration validation passed")
        else:
            print("❌ Configuration validation failed")

        # Test LLM config creation
        try:
            llm_config = get_llm_config()
            print("✅ LLM configuration created successfully")
        except Exception as e:
            print(f"⚠️  LLM configuration creation failed: {e}")



    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        import traceback
        traceback.print_exc()