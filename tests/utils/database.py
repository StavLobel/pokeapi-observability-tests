"""
Database repository layer for storing and retrieving API responses.
Provides connection management and CRUD operations for test data.
"""

import os
import json
from typing import Optional, Dict, Any
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from contextlib import contextmanager


class ResponseRepository:
    """Repository for storing and retrieving API responses from PostgreSQL."""
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None
    ):
        """
        Initialize database connection parameters.
        
        Args:
            host: PostgreSQL host (defaults to env var POSTGRES_HOST)
            port: PostgreSQL port (defaults to env var POSTGRES_PORT)
            database: Database name (defaults to env var POSTGRES_DB)
            user: Database user (defaults to env var POSTGRES_USER)
            password: Database password (defaults to env var POSTGRES_PASSWORD)
        """
        self.host = host or os.getenv('POSTGRES_HOST', 'localhost')
        self.port = port or int(os.getenv('POSTGRES_PORT', '5432'))
        self.database = database or os.getenv('POSTGRES_DB', 'pokeapi_cache')
        self.user = user or os.getenv('POSTGRES_USER', 'postgres')
        self.password = password or os.getenv('POSTGRES_PASSWORD', 'postgres')
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        Automatically handles connection cleanup.
        """
        conn = None
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def store_response(
        self,
        endpoint: str,
        resource_id: int,
        response_data: Dict[Any, Any]
    ) -> int:
        """
        Store an API response in the database.
        Uses UPSERT logic to handle duplicate entries.
        
        Args:
            endpoint: API endpoint name (e.g., 'pokemon', 'type', 'ability')
            resource_id: Resource identifier (e.g., pokemon ID)
            response_data: Complete JSON response from API
            
        Returns:
            ID of the inserted/updated record
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO api_responses (endpoint, resource_id, response_data, created_at)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (endpoint, resource_id, Json(response_data), datetime.utcnow())
                )
                result = cursor.fetchone()
                return result[0]
    
    def get_latest_response(
        self,
        endpoint: str,
        resource_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve the most recent API response for a given endpoint and resource.
        
        Args:
            endpoint: API endpoint name
            resource_id: Resource identifier
            
        Returns:
            Dictionary containing the response data and metadata, or None if not found
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT id, endpoint, resource_id, response_data, created_at
                    FROM api_responses
                    WHERE endpoint = %s AND resource_id = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (endpoint, resource_id)
                )
                result = cursor.fetchone()
                if result:
                    return dict(result)
                return None
    
    def store_schema_version(
        self,
        endpoint: str,
        schema_structure: Dict[Any, Any]
    ) -> int:
        """
        Store a schema version for an endpoint.
        
        Args:
            endpoint: API endpoint name
            schema_structure: JSON representation of the schema structure
            
        Returns:
            ID of the inserted record
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO schema_versions (endpoint, schema_structure, created_at)
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (endpoint, Json(schema_structure), datetime.utcnow())
                )
                result = cursor.fetchone()
                return result[0]
    
    def get_latest_schema(
        self,
        endpoint: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve the most recent schema version for an endpoint.
        
        Args:
            endpoint: API endpoint name
            
        Returns:
            Dictionary containing the schema structure and metadata, or None if not found
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT id, endpoint, schema_structure, created_at
                    FROM schema_versions
                    WHERE endpoint = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (endpoint,)
                )
                result = cursor.fetchone()
                if result:
                    return dict(result)
                return None
    
    def get_all_responses(
        self,
        endpoint: str,
        resource_id: int
    ) -> list[Dict[str, Any]]:
        """
        Retrieve all stored responses for a given endpoint and resource.
        Useful for historical comparison.
        
        Args:
            endpoint: API endpoint name
            resource_id: Resource identifier
            
        Returns:
            List of dictionaries containing response data and metadata
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT id, endpoint, resource_id, response_data, created_at
                    FROM api_responses
                    WHERE endpoint = %s AND resource_id = %s
                    ORDER BY created_at DESC
                    """,
                    (endpoint, resource_id)
                )
                results = cursor.fetchall()
                return [dict(row) for row in results]
    
    def clear_responses(self, endpoint: Optional[str] = None) -> int:
        """
        Clear stored responses. Used for testing cleanup.
        
        Args:
            endpoint: If provided, only clear responses for this endpoint.
                     If None, clear all responses.
            
        Returns:
            Number of rows deleted
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                if endpoint:
                    cursor.execute(
                        "DELETE FROM api_responses WHERE endpoint = %s",
                        (endpoint,)
                    )
                else:
                    cursor.execute("DELETE FROM api_responses")
                return cursor.rowcount
