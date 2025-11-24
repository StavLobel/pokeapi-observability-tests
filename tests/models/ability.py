"""
Pydantic models for PokéAPI /ability/{id} endpoint.

These models validate the structure and types of Ability data returned
from the PokéAPI. All models allow extra fields for forward compatibility.
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field


class LanguageReference(BaseModel):
    """Reference to a language."""

    name: str = Field(..., description="Name of the language")
    url: str = Field(..., description="URL to the language resource")

    class Config:
        extra = "allow"


class EffectEntry(BaseModel):
    """Effect description in a specific language."""

    effect: str = Field(..., description="Full effect description")
    language: LanguageReference = Field(..., description="Language reference")
    short_effect: str = Field(..., description="Short effect description")

    class Config:
        extra = "allow"


class Ability(BaseModel):
    """
    Complete Ability data model.

    Validates responses from GET /ability/{id} endpoint.
    Enforces required fields: id, name, is_main_series, effect_entries, pokemon.
    """

    id: int = Field(..., description="Ability ID", gt=0)
    name: str = Field(..., description="Ability name", min_length=1)
    is_main_series: bool = Field(
        ..., description="Whether this ability is from the main series"
    )
    effect_entries: List[EffectEntry] = Field(
        ..., description="List of effect descriptions in different languages"
    )
    pokemon: List[Dict[str, Any]] = Field(
        ..., description="List of Pokemon with this ability"
    )

    class Config:
        extra = "allow"
