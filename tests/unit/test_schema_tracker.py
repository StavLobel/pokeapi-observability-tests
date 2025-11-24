"""
Unit tests for schema tracking functionality.
Tests schema extraction and comparison logic.
"""

import pytest
from tests.utils.schema_tracker import (
    SchemaTracker,
    SchemaDiff,
    SchemaChange,
    ChangeType
)


class TestSchemaExtraction:
    """Tests for extract_schema_structure method."""
    
    def test_extract_simple_types(self):
        """Test extraction of simple data types."""
        tracker = SchemaTracker()
        response = {
            "id": 1,
            "name": "bulbasaur",
            "height": 7.5,
            "is_default": True,
            "description": None
        }
        
        schema = tracker.extract_schema_structure(response)
        
        assert schema["id"] == "int"
        assert schema["name"] == "str"
        assert schema["height"] == "float"
        assert schema["is_default"] == "bool"
        assert schema["description"] == "null"
    
    def test_extract_nested_dict(self):
        """Test extraction of nested dictionary structures."""
        tracker = SchemaTracker()
        response = {
            "id": 1,
            "sprites": {
                "front_default": "url1",
                "back_default": "url2"
            }
        }
        
        schema = tracker.extract_schema_structure(response)
        
        assert schema["id"] == "int"
        assert schema["sprites"] == "dict"
        assert schema["sprites.front_default"] == "str"
        assert schema["sprites.back_default"] == "str"
    
    def test_extract_list_with_items(self):
        """Test extraction of list structures with items."""
        tracker = SchemaTracker()
        response = {
            "id": 1,
            "types": [
                {"slot": 1, "type": {"name": "grass"}},
                {"slot": 2, "type": {"name": "poison"}}
            ]
        }
        
        schema = tracker.extract_schema_structure(response)
        
        assert schema["id"] == "int"
        assert schema["types"] == "list"
        assert schema["types[].slot"] == "int"
        assert schema["types[].type"] == "dict"
        assert schema["types[].type.name"] == "str"
    
    def test_extract_empty_list(self):
        """Test extraction of empty list."""
        tracker = SchemaTracker()
        response = {
            "id": 1,
            "moves": []
        }
        
        schema = tracker.extract_schema_structure(response)
        
        assert schema["id"] == "int"
        assert schema["moves"] == "list"
        # Empty list should not have item schema
        assert "moves[]" not in schema
    
    def test_extract_deeply_nested(self):
        """Test extraction of deeply nested structures."""
        tracker = SchemaTracker()
        response = {
            "level1": {
                "level2": {
                    "level3": {
                        "value": 42
                    }
                }
            }
        }
        
        schema = tracker.extract_schema_structure(response)
        
        assert schema["level1"] == "dict"
        assert schema["level1.level2"] == "dict"
        assert schema["level1.level2.level3"] == "dict"
        assert schema["level1.level2.level3.value"] == "int"
    
    def test_extract_empty_dict(self):
        """Test extraction from empty dictionary."""
        tracker = SchemaTracker()
        response = {}
        
        schema = tracker.extract_schema_structure(response)
        
        assert schema == {}
    
    def test_extract_none_response(self):
        """Test extraction from None response."""
        tracker = SchemaTracker()
        
        schema = tracker.extract_schema_structure(None)
        
        assert schema == {}


class TestSchemaComparison:
    """Tests for compare_schemas method."""
    
    def test_no_changes(self):
        """Test comparison when schemas are identical."""
        tracker = SchemaTracker()
        schema1 = {"id": "int", "name": "str"}
        schema2 = {"id": "int", "name": "str"}
        
        diff = tracker.compare_schemas(schema1, schema2)
        
        assert not diff.has_changes
        assert len(diff.added_fields) == 0
        assert len(diff.removed_fields) == 0
        assert len(diff.modified_fields) == 0
    
    def test_field_added(self):
        """Test detection of added fields."""
        tracker = SchemaTracker()
        previous = {"id": "int", "name": "str"}
        current = {"id": "int", "name": "str", "height": "int"}
        
        diff = tracker.compare_schemas(current, previous)
        
        assert diff.has_changes
        assert len(diff.added_fields) == 1
        assert diff.added_fields[0].change_type == ChangeType.FIELD_ADDED
        assert diff.added_fields[0].field_path == "height"
        assert diff.added_fields[0].new_value == "int"
        assert diff.added_fields[0].old_value is None
    
    def test_field_removed(self):
        """Test detection of removed fields."""
        tracker = SchemaTracker()
        previous = {"id": "int", "name": "str", "height": "int"}
        current = {"id": "int", "name": "str"}
        
        diff = tracker.compare_schemas(current, previous)
        
        assert diff.has_changes
        assert len(diff.removed_fields) == 1
        assert diff.removed_fields[0].change_type == ChangeType.FIELD_REMOVED
        assert diff.removed_fields[0].field_path == "height"
        assert diff.removed_fields[0].old_value == "int"
        assert diff.removed_fields[0].new_value is None
    
    def test_type_changed(self):
        """Test detection of type changes."""
        tracker = SchemaTracker()
        previous = {"id": "int", "name": "str", "height": "int"}
        current = {"id": "int", "name": "str", "height": "float"}
        
        diff = tracker.compare_schemas(current, previous)
        
        assert diff.has_changes
        assert len(diff.modified_fields) == 1
        assert diff.modified_fields[0].change_type == ChangeType.TYPE_CHANGED
        assert diff.modified_fields[0].field_path == "height"
        assert diff.modified_fields[0].old_value == "int"
        assert diff.modified_fields[0].new_value == "float"
    
    def test_multiple_changes(self):
        """Test detection of multiple simultaneous changes."""
        tracker = SchemaTracker()
        previous = {
            "id": "int",
            "name": "str",
            "height": "int",
            "old_field": "str"
        }
        current = {
            "id": "int",
            "name": "str",
            "height": "float",
            "new_field": "bool"
        }
        
        diff = tracker.compare_schemas(current, previous)
        
        assert diff.has_changes
        assert len(diff.added_fields) == 1
        assert len(diff.removed_fields) == 1
        assert len(diff.modified_fields) == 1
        
        # Check added field
        assert diff.added_fields[0].field_path == "new_field"
        
        # Check removed field
        assert diff.removed_fields[0].field_path == "old_field"
        
        # Check modified field
        assert diff.modified_fields[0].field_path == "height"
    
    def test_nested_field_changes(self):
        """Test detection of changes in nested fields."""
        tracker = SchemaTracker()
        previous = {
            "id": "int",
            "sprites": "dict",
            "sprites.front": "str"
        }
        current = {
            "id": "int",
            "sprites": "dict",
            "sprites.front": "str",
            "sprites.back": "str"
        }
        
        diff = tracker.compare_schemas(current, previous)
        
        assert diff.has_changes
        assert len(diff.added_fields) == 1
        assert diff.added_fields[0].field_path == "sprites.back"
    
    def test_all_changes_property(self):
        """Test the all_changes property returns combined list."""
        tracker = SchemaTracker()
        previous = {"id": "int", "old": "str"}
        current = {"id": "str", "new": "int"}
        
        diff = tracker.compare_schemas(current, previous)
        
        all_changes = diff.all_changes
        assert len(all_changes) == 3  # 1 added, 1 removed, 1 modified
        
        # Verify all change types are present
        change_types = {change.change_type for change in all_changes}
        assert ChangeType.FIELD_ADDED in change_types
        assert ChangeType.FIELD_REMOVED in change_types
        assert ChangeType.TYPE_CHANGED in change_types


class TestSchemaDiff:
    """Tests for SchemaDiff class."""
    
    def test_has_changes_false(self):
        """Test has_changes returns False when no changes."""
        diff = SchemaDiff()
        assert not diff.has_changes
    
    def test_has_changes_with_added(self):
        """Test has_changes returns True with added fields."""
        diff = SchemaDiff(
            added_fields=[
                SchemaChange(ChangeType.FIELD_ADDED, "field1", new_value="int")
            ]
        )
        assert diff.has_changes
    
    def test_has_changes_with_removed(self):
        """Test has_changes returns True with removed fields."""
        diff = SchemaDiff(
            removed_fields=[
                SchemaChange(ChangeType.FIELD_REMOVED, "field1", old_value="int")
            ]
        )
        assert diff.has_changes
    
    def test_has_changes_with_modified(self):
        """Test has_changes returns True with modified fields."""
        diff = SchemaDiff(
            modified_fields=[
                SchemaChange(
                    ChangeType.TYPE_CHANGED,
                    "field1",
                    old_value="int",
                    new_value="str"
                )
            ]
        )
        assert diff.has_changes
    
    def test_str_no_changes(self):
        """Test string representation with no changes."""
        diff = SchemaDiff()
        assert str(diff) == "No schema changes detected"
    
    def test_str_with_changes(self):
        """Test string representation with changes."""
        diff = SchemaDiff(
            added_fields=[SchemaChange(ChangeType.FIELD_ADDED, "f1", new_value="int")],
            removed_fields=[SchemaChange(ChangeType.FIELD_REMOVED, "f2", old_value="str")],
            modified_fields=[
                SchemaChange(ChangeType.TYPE_CHANGED, "f3", old_value="int", new_value="float")
            ]
        )
        
        result = str(diff)
        assert "1 field(s) added" in result
        assert "1 field(s) removed" in result
        assert "1 field(s) modified" in result


class TestSchemaChange:
    """Tests for SchemaChange class."""
    
    def test_str_field_added(self):
        """Test string representation of added field."""
        change = SchemaChange(
            ChangeType.FIELD_ADDED,
            "new_field",
            new_value="int"
        )
        
        result = str(change)
        assert "Added field 'new_field'" in result
        assert "type int" in result
    
    def test_str_field_removed(self):
        """Test string representation of removed field."""
        change = SchemaChange(
            ChangeType.FIELD_REMOVED,
            "old_field",
            old_value="str"
        )
        
        result = str(change)
        assert "Removed field 'old_field'" in result
        assert "was type str" in result
    
    def test_str_type_changed(self):
        """Test string representation of type change."""
        change = SchemaChange(
            ChangeType.TYPE_CHANGED,
            "changed_field",
            old_value="int",
            new_value="float"
        )
        
        result = str(change)
        assert "Changed field 'changed_field'" in result
        assert "from int to float" in result


class TestSchemaTrackerHelperMethods:
    """Tests for helper methods in SchemaTracker."""
    
    def test_get_field_paths(self):
        """Test getting all field paths from schema."""
        tracker = SchemaTracker()
        schema = {
            "id": "int",
            "name": "str",
            "nested.field": "bool"
        }
        
        paths = tracker.get_field_paths(schema)
        
        assert paths == {"id", "name", "nested.field"}
    
    def test_get_field_type_exists(self):
        """Test getting type of existing field."""
        tracker = SchemaTracker()
        schema = {"id": "int", "name": "str"}
        
        field_type = tracker.get_field_type(schema, "id")
        
        assert field_type == "int"
    
    def test_get_field_type_not_exists(self):
        """Test getting type of non-existent field."""
        tracker = SchemaTracker()
        schema = {"id": "int"}
        
        field_type = tracker.get_field_type(schema, "nonexistent")
        
        assert field_type is None


class TestEndToEndScenarios:
    """End-to-end tests with realistic API response scenarios."""
    
    def test_pokemon_response_extraction(self):
        """Test extraction from realistic Pokemon API response."""
        tracker = SchemaTracker()
        response = {
            "id": 1,
            "name": "bulbasaur",
            "base_experience": 64,
            "height": 7,
            "weight": 69,
            "types": [
                {
                    "slot": 1,
                    "type": {
                        "name": "grass",
                        "url": "https://pokeapi.co/api/v2/type/12/"
                    }
                }
            ],
            "abilities": [
                {
                    "is_hidden": False,
                    "slot": 1,
                    "ability": {
                        "name": "overgrow",
                        "url": "https://pokeapi.co/api/v2/ability/65/"
                    }
                }
            ]
        }
        
        schema = tracker.extract_schema_structure(response)
        
        # Verify top-level fields
        assert schema["id"] == "int"
        assert schema["name"] == "str"
        assert schema["types"] == "list"
        assert schema["abilities"] == "list"
        
        # Verify nested structures
        assert schema["types[].slot"] == "int"
        assert schema["types[].type"] == "dict"
        assert schema["types[].type.name"] == "str"
        assert schema["abilities[].is_hidden"] == "bool"
        assert schema["abilities[].ability.name"] == "str"
    
    def test_schema_evolution_scenario(self):
        """Test detecting schema evolution over time."""
        tracker = SchemaTracker()
        
        # Version 1 of API
        v1_response = {
            "id": 1,
            "name": "bulbasaur",
            "height": 7
        }
        
        # Version 2 adds weight field
        v2_response = {
            "id": 1,
            "name": "bulbasaur",
            "height": 7,
            "weight": 69
        }
        
        # Version 3 changes height to float and adds is_default
        v3_response = {
            "id": 1,
            "name": "bulbasaur",
            "height": 7.0,
            "weight": 69,
            "is_default": True
        }
        
        v1_schema = tracker.extract_schema_structure(v1_response)
        v2_schema = tracker.extract_schema_structure(v2_response)
        v3_schema = tracker.extract_schema_structure(v3_response)
        
        # Compare v1 to v2
        diff_v1_v2 = tracker.compare_schemas(v2_schema, v1_schema)
        assert diff_v1_v2.has_changes
        assert len(diff_v1_v2.added_fields) == 1
        assert diff_v1_v2.added_fields[0].field_path == "weight"
        
        # Compare v2 to v3
        diff_v2_v3 = tracker.compare_schemas(v3_schema, v2_schema)
        assert diff_v2_v3.has_changes
        assert len(diff_v2_v3.added_fields) == 1
        assert len(diff_v2_v3.modified_fields) == 1
        assert diff_v2_v3.added_fields[0].field_path == "is_default"
        assert diff_v2_v3.modified_fields[0].field_path == "height"
        assert diff_v2_v3.modified_fields[0].old_value == "int"
        assert diff_v2_v3.modified_fields[0].new_value == "float"
