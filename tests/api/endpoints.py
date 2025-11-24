"""
PokéAPI endpoint URL constants.

Defines base URL and endpoint paths for the PokéAPI service.
"""

import os

# Base URL for PokéAPI (can be overridden via environment variable)
BASE_URL = os.getenv('POKEAPI_BASE_URL', 'https://pokeapi.co/api/v2')

# Endpoint paths
POKEMON_ENDPOINT = 'pokemon'
TYPE_ENDPOINT = 'type'
ABILITY_ENDPOINT = 'ability'

# Full endpoint URLs
def get_pokemon_url(pokemon_id: int) -> str:
    """Get full URL for pokemon endpoint."""
    return f"{BASE_URL}/{POKEMON_ENDPOINT}/{pokemon_id}"

def get_type_url(type_id: int) -> str:
    """Get full URL for type endpoint."""
    return f"{BASE_URL}/{TYPE_ENDPOINT}/{type_id}"

def get_ability_url(ability_id: int) -> str:
    """Get full URL for ability endpoint."""
    return f"{BASE_URL}/{ABILITY_ENDPOINT}/{ability_id}"
