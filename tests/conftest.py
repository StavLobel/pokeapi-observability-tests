"""
Pytest configuration and fixtures for the test suite.
Provides shared fixtures for database connections, API clients, and test utilities.
"""

import pytest
import os
from tests.utils.database import ResponseRepository


@pytest.fixture(scope="session")
def db_config():
    """
    Provide database configuration from environment variables.
    Session-scoped to avoid repeated lookups.
    """
    return {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', '5432')),
        'database': os.getenv('POSTGRES_DB', 'pokeapi_cache'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', 'postgres')
    }


@pytest.fixture(scope="function")
def db_repository(db_config):
    """
    Provide a ResponseRepository instance for database operations.
    Function-scoped to ensure clean state for each test.
    """
    repo = ResponseRepository(**db_config)
    yield repo
    # Cleanup: Clear test data after each test
    # Note: In production, you might want more selective cleanup


@pytest.fixture(scope="function")
def clean_db(db_repository):
    """
    Provide a clean database state for tests.
    Clears all responses before and after the test.
    """
    # Clear before test
    db_repository.clear_responses()
    yield db_repository
    # Clear after test
    db_repository.clear_responses()
