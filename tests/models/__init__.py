"""
Pydantic models for PokéAPI response validation.

This module provides data validation models for the following endpoints:
- /pokemon/{id}
- /type/{id}
- /ability/{id}

All models are configured with extra="allow" for forward compatibility
with API changes.
"""

from tests.models.pokemon import (
    Pokemon,
    PokemonType,
    PokemonAbility,
    PokemonStat,
    PokemonSprite,
)
from tests.models.type import Type, TypePokemon
from tests.models.ability import Ability, EffectEntry

__all__ = [
    "Pokemon",
    "PokemonType",
    "PokemonAbility",
    "PokemonStat",
    "PokemonSprite",
    "Type",
    "TypePokemon",
    "Ability",
    "EffectEntry",
]
