"""
API client module for PokéAPI interactions.

Provides HTTPX-based client with resilience patterns including:
- Rate limiting
- Circuit breaker
- Retry with exponential backoff
- Metrics collection
"""

from tests.api.client import PokeAPIClient
from tests.api.endpoints import POKEMON_ENDPOINT, TYPE_ENDPOINT, ABILITY_ENDPOINT

__all__ = [
    'PokeAPIClient',
    'POKEMON_ENDPOINT',
    'TYPE_ENDPOINT',
    'ABILITY_ENDPOINT',
]
