"""
Pydantic models for PokéAPI /pokemon/{id} endpoint.

These models validate the structure and types of Pokemon data returned
from the PokéAPI. All models allow extra fields for forward compatibility.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class TypeReference(BaseModel):
    """Reference to a Pokemon type."""

    name: str = Field(..., description="Name of the type")
    url: str = Field(..., description="URL to the type resource")

    class Config:
        extra = "allow"


class PokemonType(BaseModel):
    """Pokemon type information with slot position."""

    slot: int = Field(..., description="Slot position of this type")
    type: TypeReference = Field(..., description="Type reference")

    class Config:
        extra = "allow"


class AbilityReference(BaseModel):
    """Reference to a Pokemon ability."""

    name: str = Field(..., description="Name of the ability")
    url: str = Field(..., description="URL to the ability resource")

    class Config:
        extra = "allow"


class PokemonAbility(BaseModel):
    """Pokemon ability information."""

    is_hidden: bool = Field(..., description="Whether this is a hidden ability")
    slot: int = Field(..., description="Slot position of this ability")
    ability: AbilityReference = Field(..., description="Ability reference")

    class Config:
        extra = "allow"


class StatReference(BaseModel):
    """Reference to a Pokemon stat."""

    name: str = Field(..., description="Name of the stat")
    url: str = Field(..., description="URL to the stat resource")

    class Config:
        extra = "allow"


class PokemonStat(BaseModel):
    """Pokemon stat information."""

    base_stat: int = Field(..., description="Base value of the stat")
    effort: int = Field(..., description="Effort points gained for this stat")
    stat: StatReference = Field(..., description="Stat reference")

    class Config:
        extra = "allow"


class PokemonSprite(BaseModel):
    """Pokemon sprite URLs."""

    front_default: Optional[str] = Field(None, description="Default front sprite URL")
    back_default: Optional[str] = Field(None, description="Default back sprite URL")
    front_shiny: Optional[str] = Field(None, description="Shiny front sprite URL")
    back_shiny: Optional[str] = Field(None, description="Shiny back sprite URL")
    front_female: Optional[str] = Field(None, description="Female front sprite URL")
    back_female: Optional[str] = Field(None, description="Female back sprite URL")
    front_shiny_female: Optional[str] = Field(
        None, description="Shiny female front sprite URL"
    )
    back_shiny_female: Optional[str] = Field(
        None, description="Shiny female back sprite URL"
    )

    class Config:
        extra = "allow"


class Pokemon(BaseModel):
    """
    Complete Pokemon data model.

    Validates responses from GET /pokemon/{id} endpoint.
    Enforces required fields: id, name, height, weight, types, abilities, stats, sprites.
    """

    id: int = Field(..., description="Pokemon ID", gt=0)
    name: str = Field(..., description="Pokemon name", min_length=1)
    base_experience: Optional[int] = Field(
        None, description="Base experience gained for defeating this Pokemon"
    )
    height: int = Field(..., description="Height in decimeters", ge=0)
    weight: int = Field(..., description="Weight in hectograms", ge=0)
    types: List[PokemonType] = Field(
        ..., description="List of types", min_length=1
    )
    abilities: List[PokemonAbility] = Field(
        ..., description="List of abilities", min_length=1
    )
    stats: List[PokemonStat] = Field(
        ..., description="List of stats", min_length=1
    )
    sprites: PokemonSprite = Field(..., description="Sprite URLs")

    class Config:
        extra = "allow"
