"""
Unit tests for the PokéAPI client.

Tests the HTTPX-based API client with resilience patterns.
"""

import pytest
import httpx
from unittest.mock import Mock, AsyncMock, patch
from tests.api.client import PokeAPIClient
from tests.utils.rate_limiter import RateLimiter
from tests.utils.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError


@pytest.mark.asyncio
async def test_client_initialization():
    """Test that client initializes with correct defaults."""
    client = PokeAPIClient()
    
    assert client.base_url == "https://pokeapi.co/api/v2"
    assert client.timeout == 10.0
    assert client.max_retries == 3
    assert 'pokemon' in client.circuit_breakers
    assert 'type' in client.circuit_breakers
    assert 'ability' in client.circuit_breakers
    
    await client.close()


@pytest.mark.asyncio
async def test_client_context_manager():
    """Test that client works as async context manager."""
    async with PokeAPIClient() as client:
        assert client.client is not None
    
    # Client should be closed after context exit
    assert client.client.is_closed


@pytest.mark.asyncio
async def test_get_pokemon_success():
    """Test successful pokemon request."""
    mock_response = {
        'id': 1,
        'name': 'bulbasaur',
        'types': [],
        'abilities': [],
        'stats': [],
        'sprites': {},
        'height': 7,
        'weight': 69
    }
    
    client = PokeAPIClient()
    
    with patch.object(client.client, 'get', new_callable=AsyncMock) as mock_get:
        mock_http_response = Mock()
        mock_http_response.status_code = 200
        mock_http_response.json.return_value = mock_response
        mock_http_response.raise_for_status = Mock()
        mock_get.return_value = mock_http_response
        
        result = await client.get_pokemon(1)
        
        assert result == mock_response
        assert mock_get.called
    
    await client.close()


@pytest.mark.asyncio
async def test_get_type_success():
    """Test successful type request."""
    mock_response = {
        'id': 1,
        'name': 'normal',
        'damage_relations': {},
        'pokemon': [],
        'moves': []
    }
    
    client = PokeAPIClient()
    
    with patch.object(client.client, 'get', new_callable=AsyncMock) as mock_get:
        mock_http_response = Mock()
        mock_http_response.status_code = 200
        mock_http_response.json.return_value = mock_response
        mock_http_response.raise_for_status = Mock()
        mock_get.return_value = mock_http_response
        
        result = await client.get_type(1)
        
        assert result == mock_response
        assert mock_get.called
    
    await client.close()


@pytest.mark.asyncio
async def test_get_ability_success():
    """Test successful ability request."""
    mock_response = {
        'id': 1,
        'name': 'stench',
        'is_main_series': True,
        'effect_entries': [],
        'pokemon': []
    }
    
    client = PokeAPIClient()
    
    with patch.object(client.client, 'get', new_callable=AsyncMock) as mock_get:
        mock_http_response = Mock()
        mock_http_response.status_code = 200
        mock_http_response.json.return_value = mock_response
        mock_http_response.raise_for_status = Mock()
        mock_get.return_value = mock_http_response
        
        result = await client.get_ability(1)
        
        assert result == mock_response
        assert mock_get.called
    
    await client.close()


@pytest.mark.asyncio
async def test_rate_limiter_integration():
    """Test that rate limiter is called when configured."""
    rate_limiter = RateLimiter(max_requests=10, time_window=60)
    client = PokeAPIClient(rate_limiter=rate_limiter)
    
    mock_response = {'id': 1, 'name': 'bulbasaur'}
    
    with patch.object(client.client, 'get', new_callable=AsyncMock) as mock_get:
        mock_http_response = Mock()
        mock_http_response.status_code = 200
        mock_http_response.json.return_value = mock_response
        mock_http_response.raise_for_status = Mock()
        mock_get.return_value = mock_http_response
        
        with patch.object(rate_limiter, 'acquire', new_callable=AsyncMock) as mock_acquire:
            await client.get_pokemon(1)
            assert mock_acquire.called
    
    await client.close()


@pytest.mark.asyncio
async def test_http_error_handling():
    """Test that HTTP errors are properly handled."""
    client = PokeAPIClient()
    
    with patch.object(client.client, 'get', new_callable=AsyncMock) as mock_get:
        mock_http_response = Mock()
        mock_http_response.status_code = 404
        mock_http_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not found",
            request=Mock(),
            response=mock_http_response
        )
        mock_get.return_value = mock_http_response
        
        with pytest.raises(httpx.HTTPStatusError):
            await client.get_pokemon(99999)
    
    await client.close()


@pytest.mark.asyncio
async def test_circuit_breaker_state():
    """Test circuit breaker state retrieval."""
    client = PokeAPIClient()
    
    # Initially closed
    assert client.get_circuit_breaker_state('pokemon') == 0
    
    await client.close()


@pytest.mark.asyncio
async def test_jitter_adds_randomness():
    """Test that jitter adds random delay."""
    client = PokeAPIClient()
    
    delays = [client._add_jitter(1.0) for _ in range(10)]
    
    # All delays should be between 1.0 and 2.0
    assert all(1.0 <= d <= 2.0 for d in delays)
    
    # Delays should not all be the same (randomness)
    assert len(set(delays)) > 1
    
    await client.close()
