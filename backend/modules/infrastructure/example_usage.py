"""
Example usage of the Infrastructure module.

This example shows how to use the new simplified infrastructure module
following the backend.md pattern.
"""

from modules.infrastructure.public import InfrastructureProvider, infrastructure_provider


def example_usage():
    """Example of how to use the infrastructure module."""

    # Get the infrastructure service through the public API
    infra: InfrastructureProvider = infrastructure_provider()

    # Initialize the service
    infra.initialize()

    # Get configuration
    config = infra.get_config()
    print(f"Database URL: {config.database_url}")
    print(f"API Port: {config.api_config.port}")
    print(f"Debug Mode: {config.feature_flags['debug']}")

    # Validate environment
    status = infra.validate_environment()
    if status.is_valid:
        print("✅ Environment is valid")
    else:
        print("❌ Environment validation failed:")
        for error in status.errors:
            print(f"  - {error}")

    # Use database session
    try:
        db_session = infra.get_database_session()
        print(f"✅ Got database session: {db_session.connection_id}")

        # Use the session for database operations
        # db_session.session.execute(text("SELECT 1"))

        # Close the session
        infra.close_database_session(db_session)
        print("✅ Database session closed")

    except Exception as e:
        print(f"❌ Database session error: {e}")

    # Use session context manager (recommended)
    try:
        with infra.get_session_context() as session:
            print("✅ Using database session context manager")
            # Use session for database operations
            # result = session.execute(text("SELECT 1"))
            # Session will be automatically committed/rolled back and closed

    except Exception as e:
        print(f"❌ Database context error: {e}")

    # Cleanup
    infra.shutdown()
    print("✅ Infrastructure service shut down")


def example_dependency_injection():
    """Example of how another module would use the infrastructure service."""

    # This is how another module would import and use infrastructure
    from modules.infrastructure.public import InfrastructureProvider

    class SomeOtherService:
        def __init__(self, infra: InfrastructureProvider):
            self.infra = infra

        def do_something_with_database(self):
            """Example method that uses database through infrastructure."""
            with self.infra.get_session_context() as session:
                # Do database operations
                # result = session.execute(text("SELECT * FROM some_table"))
                return "Database operation completed"

        def get_app_config(self):
            """Example method that uses configuration."""
            config = self.infra.get_config()
            return {"api_port": config.api_config.port, "debug_mode": config.feature_flags["debug"]}

    # Usage
    infra = infrastructure_provider()
    infra.initialize()

    service = SomeOtherService(infra)

    try:
        result = service.do_something_with_database()
        print(f"✅ Service result: {result}")

        config_info = service.get_app_config()
        print(f"✅ Config info: {config_info}")

    finally:
        infra.shutdown()


if __name__ == "__main__":
    print("=== Infrastructure Module Example ===")
    example_usage()

    print("\n=== Dependency Injection Example ===")
    example_dependency_injection()
