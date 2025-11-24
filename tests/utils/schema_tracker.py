"""
Schema tracking functionality for detecting API schema changes.
Extracts schema structure from JSON responses and compares versions.
"""

from typing import Dict, Any, List, Set, Optional
from dataclasses import dataclass, field
from enum import Enum


class ChangeType(Enum):
    """Types of schema changes that can be detected."""
    FIELD_ADDED = "field_added"
    FIELD_REMOVED = "field_removed"
    TYPE_CHANGED = "type_changed"


@dataclass
class SchemaChange:
    """Represents a single schema change."""
    change_type: ChangeType
    field_path: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    
    def __str__(self) -> str:
        """Human-readable representation of the change."""
        if self.change_type == ChangeType.FIELD_ADDED:
            return f"Added field '{self.field_path}' with type {self.new_value}"
        elif self.change_type == ChangeType.FIELD_REMOVED:
            return f"Removed field '{self.field_path}' (was type {self.old_value})"
        elif self.change_type == ChangeType.TYPE_CHANGED:
            return f"Changed field '{self.field_path}' type from {self.old_value} to {self.new_value}"
        return f"{self.change_type.value}: {self.field_path}"


@dataclass
class SchemaDiff:
    """
    Represents the differences between two schemas.
    Contains lists of added, removed, and modified fields.
    """
    added_fields: List[SchemaChange] = field(default_factory=list)
    removed_fields: List[SchemaChange] = field(default_factory=list)
    modified_fields: List[SchemaChange] = field(default_factory=list)
    
    @property
    def has_changes(self) -> bool:
        """Check if there are any schema changes."""
        return bool(self.added_fields or self.removed_fields or self.modified_fields)
    
    @property
    def all_changes(self) -> List[SchemaChange]:
        """Get all changes as a single list."""
        return self.added_fields + self.removed_fields + self.modified_fields
    
    def __str__(self) -> str:
        """Human-readable summary of schema differences."""
        if not self.has_changes:
            return "No schema changes detected"
        
        parts = []
        if self.added_fields:
            parts.append(f"{len(self.added_fields)} field(s) added")
        if self.removed_fields:
            parts.append(f"{len(self.removed_fields)} field(s) removed")
        if self.modified_fields:
            parts.append(f"{len(self.modified_fields)} field(s) modified")
        
        return ", ".join(parts)


class SchemaTracker:
    """
    Tracks and compares API schema structures.
    Extracts schema from JSON responses and detects changes over time.
    """
    
    def extract_schema_structure(self, response: Dict[Any, Any], path: str = "") -> Dict[str, str]:
        """
        Extract schema structure from a JSON response.
        Returns a flat dictionary mapping field paths to their types.
        
        Args:
            response: JSON response dictionary
            path: Current path in the nested structure (used for recursion)
            
        Returns:
            Dictionary mapping field paths to type names
            
        Example:
            Input: {"id": 1, "name": "bulbasaur", "types": [{"slot": 1}]}
            Output: {
                "id": "int",
                "name": "str",
                "types": "list",
                "types[].slot": "int"
            }
        """
        schema = {}
        
        if response is None:
            return schema
        
        if isinstance(response, dict):
            for key, value in response.items():
                field_path = f"{path}.{key}" if path else key
                
                if value is None:
                    schema[field_path] = "null"
                elif isinstance(value, bool):
                    # Check bool before int since bool is subclass of int
                    schema[field_path] = "bool"
                elif isinstance(value, int):
                    schema[field_path] = "int"
                elif isinstance(value, float):
                    schema[field_path] = "float"
                elif isinstance(value, str):
                    schema[field_path] = "str"
                elif isinstance(value, list):
                    schema[field_path] = "list"
                    # Extract schema from first list item if available
                    if value and len(value) > 0:
                        list_item_schema = self.extract_schema_structure(
                            value[0],
                            f"{field_path}[]"
                        )
                        schema.update(list_item_schema)
                elif isinstance(value, dict):
                    schema[field_path] = "dict"
                    # Recursively extract nested structure
                    nested_schema = self.extract_schema_structure(value, field_path)
                    schema.update(nested_schema)
                else:
                    schema[field_path] = type(value).__name__
        
        return schema
    
    def compare_schemas(
        self,
        current: Dict[str, str],
        previous: Dict[str, str]
    ) -> SchemaDiff:
        """
        Compare two schema structures and detect changes.
        
        Args:
            current: Current schema structure (from extract_schema_structure)
            previous: Previous schema structure (from extract_schema_structure)
            
        Returns:
            SchemaDiff object containing all detected changes
        """
        diff = SchemaDiff()
        
        current_fields = set(current.keys())
        previous_fields = set(previous.keys())
        
        # Detect added fields
        added = current_fields - previous_fields
        for field_path in sorted(added):
            change = SchemaChange(
                change_type=ChangeType.FIELD_ADDED,
                field_path=field_path,
                new_value=current[field_path]
            )
            diff.added_fields.append(change)
        
        # Detect removed fields
        removed = previous_fields - current_fields
        for field_path in sorted(removed):
            change = SchemaChange(
                change_type=ChangeType.FIELD_REMOVED,
                field_path=field_path,
                old_value=previous[field_path]
            )
            diff.removed_fields.append(change)
        
        # Detect modified fields (type changes)
        common_fields = current_fields & previous_fields
        for field_path in sorted(common_fields):
            if current[field_path] != previous[field_path]:
                change = SchemaChange(
                    change_type=ChangeType.TYPE_CHANGED,
                    field_path=field_path,
                    old_value=previous[field_path],
                    new_value=current[field_path]
                )
                diff.modified_fields.append(change)
        
        return diff
    
    def get_field_paths(self, schema: Dict[str, str]) -> Set[str]:
        """
        Get all field paths from a schema structure.
        
        Args:
            schema: Schema structure dictionary
            
        Returns:
            Set of field paths
        """
        return set(schema.keys())
    
    def get_field_type(self, schema: Dict[str, str], field_path: str) -> Optional[str]:
        """
        Get the type of a specific field from a schema.
        
        Args:
            schema: Schema structure dictionary
            field_path: Path to the field
            
        Returns:
            Type name as string, or None if field not found
        """
        return schema.get(field_path)
