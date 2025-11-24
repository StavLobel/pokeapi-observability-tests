"""
Pydantic models for PokéAPI /type/{id} endpoint.

These models validate the structure and types of Type data returned
from the PokéAPI. All models allow extra fields for forward compatibility.
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field


class PokemonReference(BaseModel):
    """Reference to a Pokemon."""

    name: str = Field(..., description="Name of the Pokemon")
    url: str = Field(..., description="URL to the Pokemon resource")

    class Config:
        extra = "allow"


class TypePokemon(BaseModel):
    """Pokemon that has this type."""

    slot: int = Field(..., description="Slot position of this type for the Pokemon")
    pokemon: PokemonReference = Field(..., description="Pokemon reference")

    class Config:
        extra = "allow"


class Type(BaseModel):
    """
    Complete Type data model.

    Validates responses from GET /type/{id} endpoint.
    Enforces required fields: id, name, damage_relations, pokemon, moves.
    """

    id: int = Field(..., description="Type ID", gt=0)
    name: str = Field(..., description="Type name", min_length=1)
    damage_relations: Dict[str, Any] = Field(
        ..., description="Damage relations for this type"
    )
    pokemon: List[TypePokemon] = Field(
        ..., description="List of Pokemon with this type"
    )
    moves: List[Dict[str, Any]] = Field(
        ..., description="List of moves of this type"
    )

    class Config:
        extra = "allow"
