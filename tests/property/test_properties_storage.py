"""
Property-based tests for API response storage (Properties 3-10).

These tests verify that API responses are correctly stored in the database
and that historical comparison functionality works as expected.
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from tests.utils.database import ResponseRepository


# Custom strategies for generating test data
@st.composite
def pokemon_response(draw):
    """Generate a valid pokemon-like response structure."""
    # Use printable characters excluding null bytes for JSON compatibility
    safe_text = st.text(
        alphabet=st.characters(min_codepoint=32, max_codepoint=126),
        min_size=1
    )
    
    return {
        'id': draw(st.integers(min_value=1, max_value=1000)),
        'name': draw(safe_text.filter(lambda x: len(x) <= 20)),
        'base_experience': draw(st.integers(min_value=0, max_value=500)),
        'height': draw(st.integers(min_value=1, max_value=200)),
        'weight': draw(st.integers(min_value=1, max_value=1000)),
        'types': draw(st.lists(
            st.fixed_dictionaries({
                'slot': st.integers(min_value=1, max_value=2),
                'type': st.fixed_dictionaries({
                    'name': safe_text.filter(lambda x: len(x) <= 15),
                    'url': safe_text.filter(lambda x: len(x) <= 50)
                })
            }),
            min_size=1,
            max_size=2
        )),
        'abilities': draw(st.lists(
            st.fixed_dictionaries({
                'is_hidden': st.booleans(),
                'slot': st.integers(min_value=1, max_value=3),
                'ability': st.fixed_dictionaries({
                    'name': safe_text.filter(lambda x: len(x) <= 20),
                    'url': safe_text.filter(lambda x: len(x) <= 50)
                })
            }),
            min_size=1,
            max_size=3
        ))
    }


@st.composite
def type_response(draw):
    """Generate a valid type-like response structure."""
    # Use printable characters excluding null bytes for JSON compatibility
    safe_text = st.text(
        alphabet=st.characters(min_codepoint=32, max_codepoint=126),
        min_size=1
    )
    
    return {
        'id': draw(st.integers(min_value=1, max_value=20)),
        'name': draw(safe_text.filter(lambda x: len(x) <= 15)),
        'damage_relations': draw(st.fixed_dictionaries({
            'double_damage_from': st.lists(st.dictionaries(safe_text, safe_text, max_size=2), max_size=2),
            'double_damage_to': st.lists(st.dictionaries(safe_text, safe_text, max_size=2), max_size=2),
            'half_damage_from': st.lists(st.dictionaries(safe_text, safe_text, max_size=2), max_size=2),
            'half_damage_to': st.lists(st.dictionaries(safe_text, safe_text, max_size=2), max_size=2),
            'no_damage_from': st.lists(st.dictionaries(safe_text, safe_text, max_size=2), max_size=2),
            'no_damage_to': st.lists(st.dictionaries(safe_text, safe_text, max_size=2), max_size=2)
        })),
        'pokemon': draw(st.lists(
            st.fixed_dictionaries({
                'slot': st.integers(min_value=1, max_value=2),
                'pokemon': st.fixed_dictionaries({
                    'name': safe_text.filter(lambda x: len(x) <= 20),
                    'url': safe_text.filter(lambda x: len(x) <= 50)
                })
            }),
            max_size=5
        ))
    }


@st.composite
def ability_response(draw):
    """Generate a valid ability-like response structure."""
    # Use printable characters excluding null bytes for JSON compatibility
    safe_text = st.text(
        alphabet=st.characters(min_codepoint=32, max_codepoint=126),
        min_size=1
    )
    
    return {
        'id': draw(st.integers(min_value=1, max_value=300)),
        'name': draw(safe_text.filter(lambda x: len(x) <= 20)),
        'is_main_series': draw(st.booleans()),
        'effect_entries': draw(st.lists(
            st.fixed_dictionaries({
                'effect': safe_text.filter(lambda x: len(x) <= 100),
                'short_effect': safe_text.filter(lambda x: len(x) <= 50),
                'language': st.fixed_dictionaries({
                    'name': safe_text.filter(lambda x: len(x) <= 10),
                    'url': safe_text.filter(lambda x: len(x) <= 50)
                })
            }),
            min_size=1,
            max_size=3
        ))
    }


# Property 3: API responses are stored in database
@given(
    endpoint=st.sampled_from(['pokemon', 'type', 'ability']),
    resource_id=st.integers(min_value=1, max_value=1000),
    response_data=st.one_of(pokemon_response(), type_response(), ability_response())
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.property
def test_property_3_responses_stored_in_database(clean_db, endpoint, resource_id, response_data):
    """
    Feature: pokeapi-observability-tests, Property 3: API responses are stored in database
    
    For any successful API response from pokemon, type, or ability endpoints,
    the complete JSON response shall be stored in PostgreSQL with endpoint name,
    resource ID, and timestamp.
    
    Validates: Requirements 5.1, 5.2, 5.3
    """
    # Store the response
    record_id = clean_db.store_response(endpoint, resource_id, response_data)
    
    # Verify the record was created
    assert record_id is not None
    assert isinstance(record_id, int)
    assert record_id > 0
    
    # Retrieve the stored response
    stored = clean_db.get_latest_response(endpoint, resource_id)
    
    # Verify the response was stored correctly
    assert stored is not None, f"No response found for endpoint={endpoint}, resource_id={resource_id}"
    assert stored['endpoint'] == endpoint, f"Expected endpoint '{endpoint}', got '{stored['endpoint']}'"
    assert stored['resource_id'] == resource_id, f"Expected resource_id {resource_id}, got {stored['resource_id']}"
    assert stored['response_data'] == response_data, "Stored response data does not match original"
    assert 'created_at' in stored, "Timestamp not stored with response"
    assert stored['created_at'] is not None, "Timestamp is None"
