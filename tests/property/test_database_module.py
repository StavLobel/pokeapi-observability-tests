"""
Unit tests for the database module to verify basic functionality.
These tests can run independently to verify the module structure.
"""

import pytest
from tests.utils.database import ResponseRepository


def test_response_repository_initialization():
    """Test that ResponseRepository can be initialized with default values."""
    repo = ResponseRepository()
    
    assert repo.host is not None
    assert repo.port is not None
    assert repo.database is not None
    assert repo.user is not None
    assert repo.password is not None


def test_response_repository_custom_config():
    """Test that ResponseRepository accepts custom configuration."""
    repo = ResponseRepository(
        host='custom-host',
        port=5433,
        database='custom-db',
        user='custom-user',
        password='custom-pass'
    )
    
    assert repo.host == 'custom-host'
    assert repo.port == 5433
    assert repo.database == 'custom-db'
    assert repo.user == 'custom-user'
    assert repo.password == 'custom-pass'


@pytest.mark.skipif(
    True,  # Skip by default - requires database
    reason="Requires PostgreSQL database connection"
)
def test_database_connection(db_repository):
    """Test that database connection can be established."""
    with db_repository.get_connection() as conn:
        assert conn is not None
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
