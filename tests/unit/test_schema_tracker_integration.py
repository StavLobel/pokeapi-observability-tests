"""
Integration tests demonstrating schema tracking workflow.
Shows how schema tracker integrates with database repository.
"""

import pytest
from tests.utils.schema_tracker import SchemaTracker


class TestSchemaTrackingWorkflow:
    """Integration tests for complete schema tracking workflow."""
    
    def test_complete_workflow_with_schema_change(self):
        """
        Test complete workflow: extract schema, compare, detect changes.
        Validates Requirements 4.1 and 4.2.
        """
        tracker = SchemaTracker()
        
        # Simulate first API call - establish baseline
        first_response = {
            "id": 1,
            "name": "bulbasaur",
            "height": 7,
            "types": [
                {"slot": 1, "type": {"name": "grass"}}
            ]
        }
        
        baseline_schema = tracker.extract_schema_structure(first_response)
        
        # Simulate second API call - API has evolved
        second_response = {
            "id": 1,
            "name": "bulbasaur",
            "height": 7.0,  # Changed from int to float
            "weight": 69,   # New field added
            "types": [
                {"slot": 1, "type": {"name": "grass"}}
            ]
        }
        
        current_schema = tracker.extract_schema_structure(second_response)
        
        # Compare schemas (Requirement 4.1)
        diff = tracker.compare_schemas(current_schema, baseline_schema)
        
        # Verify changes detected (Requirement 4.2)
        assert diff.has_changes
        
        # Verify specific field changes are logged
        assert len(diff.added_fields) == 1
        assert diff.added_fields[0].field_path == "weight"
        assert diff.added_fields[0].new_value == "int"
        
        assert len(diff.modified_fields) == 1
        assert diff.modified_fields[0].field_path == "height"
        assert diff.modified_fields[0].old_value == "int"
        assert diff.modified_fields[0].new_value == "float"
        
        # Verify human-readable summary
        summary = str(diff)
        assert "1 field(s) added" in summary
        assert "1 field(s) modified" in summary
    
    def test_workflow_no_changes(self):
        """Test workflow when API schema hasn't changed."""
        tracker = SchemaTracker()
        
        response1 = {"id": 1, "name": "bulbasaur"}
        response2 = {"id": 2, "name": "ivysaur"}  # Different data, same schema
        
        schema1 = tracker.extract_schema_structure(response1)
        schema2 = tracker.extract_schema_structure(response2)
        
        diff = tracker.compare_schemas(schema2, schema1)
        
        # No schema changes should be detected
        assert not diff.has_changes
        assert len(diff.added_fields) == 0
        assert len(diff.removed_fields) == 0
        assert len(diff.modified_fields) == 0
    
    def test_workflow_with_nested_changes(self):
        """Test workflow detecting changes in nested structures."""
        tracker = SchemaTracker()
        
        # Original nested structure
        original = {
            "id": 1,
            "sprites": {
                "front_default": "url1"
            }
        }
        
        # Updated with additional nested field
        updated = {
            "id": 1,
            "sprites": {
                "front_default": "url1",
                "back_default": "url2",
                "front_shiny": "url3"
            }
        }
        
        original_schema = tracker.extract_schema_structure(original)
        updated_schema = tracker.extract_schema_structure(updated)
        
        diff = tracker.compare_schemas(updated_schema, original_schema)
        
        assert diff.has_changes
        assert len(diff.added_fields) == 2
        
        # Verify nested field paths
        added_paths = {change.field_path for change in diff.added_fields}
        assert "sprites.back_default" in added_paths
        assert "sprites.front_shiny" in added_paths
    
    def test_workflow_with_list_structure_changes(self):
        """Test workflow detecting changes in list item structures."""
        tracker = SchemaTracker()
        
        # Original list structure
        original = {
            "types": [
                {"slot": 1, "type": {"name": "grass"}}
            ]
        }
        
        # Updated list structure with additional field
        updated = {
            "types": [
                {
                    "slot": 1,
                    "type": {
                        "name": "grass",
                        "url": "https://pokeapi.co/api/v2/type/12/"
                    }
                }
            ]
        }
        
        original_schema = tracker.extract_schema_structure(original)
        updated_schema = tracker.extract_schema_structure(updated)
        
        diff = tracker.compare_schemas(updated_schema, original_schema)
        
        assert diff.has_changes
        assert len(diff.added_fields) == 1
        assert diff.added_fields[0].field_path == "types[].type.url"
    
    def test_change_details_for_logging(self):
        """Test that change details are suitable for logging (Requirement 4.2)."""
        tracker = SchemaTracker()
        
        previous = {"id": "int", "name": "str"}
        current = {"id": "int", "name": "str", "height": "int"}
        
        diff = tracker.compare_schemas(current, previous)
        
        # Verify we can iterate and log all changes
        for change in diff.all_changes:
            # Each change should have a clear string representation
            change_str = str(change)
            assert len(change_str) > 0
            assert change.field_path in change_str
            
            # Verify change has all necessary information for logging
            assert change.change_type is not None
            assert change.field_path is not None
